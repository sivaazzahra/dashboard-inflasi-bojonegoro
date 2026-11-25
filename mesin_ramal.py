"""
MESIN PERAMALAN
===============

Semua perhitungan peramalan ada di berkas ini, terpisah dari tampilan
Streamlit. Dipisah supaya:
  1. halaman Peramalan tinggal memanggil, tidak mengurus hitungan;
  2. bagian yang tidak memerlukan Streamlit bisa diuji sendiri.

Alur satu komoditas:
  1. Harga dijadikan deret bulanan yang rapat (harian dirata-ratakan per bulan).
  2. Dibelah dua: bulan-bulan terakhir disembunyikan sebagai kunci jawaban.
  3. Tiga cara menebak dijalankan pada bagian latih, lalu diukur ketepatannya
     pada bagian yang disembunyikan: SARIMA, Holt-Winters, dan pembanding
     sederhana "salin harga tahun lalu".
  4. Cara yang dipakai dipasang ulang pada seluruh data, lalu meramal ke depan.

Satu pengaman penting: bila harga tidak berubah sama sekali selama beberapa
bulan terakhir (biasanya karena datanya memang tidak diperbarui di sumber),
tidak ada pola yang bisa dipelajari. Mesin tidak berpura-pura meramal, dan
menandainya dengan jelas.
"""

import io
import re
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

MUSIM = 12                # satu siklus musiman = 12 bulan
SELANG = 0.20             # 1 - 0,20 = rentang kemungkinan 80%
MIN_BULAN = 24            # data lebih pendek dari ini tidak diramal
BULAN_MANDEK = 6          # harga sama selama sebanyak ini dianggap mandek

# Calon pengaturan SARIMA. Daftar pendek dan tetap, bukan pencarian menyeluruh,
# supaya cepat dan hasilnya bisa diulang orang lain.
CALON_MUSIMAN = [((1, 1, 1), (1, 1, 1, MUSIM)),
                 ((0, 1, 1), (0, 1, 1, MUSIM)),
                 ((1, 1, 0), (1, 1, 0, MUSIM)),
                 ((2, 1, 1), (1, 1, 1, MUSIM)),
                 ((1, 1, 1), (0, 1, 1, MUSIM)),
                 ((0, 1, 1), (1, 1, 1, MUSIM))]
CALON_BIASA = [((1, 1, 1), (0, 0, 0, 0)),
               ((0, 1, 1), (0, 0, 0, 0)),
               ((1, 1, 0), (0, 0, 0, 0)),
               ((2, 1, 1), (0, 0, 0, 0))]

NAMA_PEMBANDING = "Salin harga tahun lalu"


# --------------------------------------------------------------------------
# Ukuran ketepatan
# --------------------------------------------------------------------------
def ukur(aktual, ramalan) -> dict:
    """RMSE dan MAE (rupiah) serta MAPE (persen)."""
    a, r = np.asarray(aktual, float), np.asarray(ramalan, float)
    bukan_nol = a != 0
    return {
        "RMSE": float(np.sqrt(np.mean((a - r) ** 2))),
        "MAE": float(np.mean(np.abs(a - r))),
        "MAPE": (float(np.mean(np.abs((a[bukan_nol] - r[bukan_nol])
                                      / a[bukan_nol])) * 100)
                 if bukan_nol.any() else np.nan),
    }


# --------------------------------------------------------------------------
# Menyiapkan deret waktu
# --------------------------------------------------------------------------
def deret_bulanan(tanggal, harga) -> pd.Series:
    """Menjadikan pasangan (tanggal, harga) deret bulanan yang rapat.

    Data harian atau mingguan dirata-ratakan per bulan. Bulan yang bolong
    di tengah ditambal dengan interpolasi linear.
    """
    s = pd.Series(np.asarray(harga, float), index=pd.DatetimeIndex(tanggal))
    s = s[~s.index.isna()].dropna().sort_index()
    s.index = s.index.to_period("M").to_timestamp()
    s = s.groupby(level=0).mean().asfreq("MS").interpolate()
    s.index.name = "periode"
    s.name = "harga"
    return s


def deret_dari_tabel(df: pd.DataFrame, komoditas: str) -> pd.Series:
    """Deret bulanan satu komoditas dari tabel harga bawaan dashboard."""
    satu = df[df["komoditas"] == komoditas]
    return deret_bulanan(satu["periode"], satu["harga"])


def bulan_sama_di_ujung(deret: pd.Series) -> int:
    """Berapa bulan terakhir yang harganya persis sama."""
    nilai = deret.values
    n = 0
    for v in nilai[::-1]:
        if np.isclose(v, nilai[-1]):
            n += 1
        else:
            break
    return n


def panjang_uji_untuk(n_bulan: int):
    """Jumlah bulan yang disembunyikan sebagai kunci jawaban.

    12 bulan bila datanya cukup panjang (minimal 36 bulan), 6 bulan bila
    hanya 24-35 bulan, dan tidak bisa diuji bila kurang dari 24 bulan.
    """
    if n_bulan >= 3 * MUSIM:
        return MUSIM
    if n_bulan >= MIN_BULAN:
        return 6
    return None


# --------------------------------------------------------------------------
# Membaca berkas unggahan
# --------------------------------------------------------------------------
def baca_berkas(nama: str, isi: bytes) -> pd.DataFrame:
    """Membaca CSV atau Excel hasil unggahan."""
    nama = nama.lower()
    if nama.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(isi))
    # sep=None membuat pandas menebak pemisah: koma, titik koma, atau tab
    # Semua kolom dibaca sebagai teks dulu. Kalau dibiarkan pandas menebak,
    # harga bergaya Indonesia seperti "14.000" terbaca sebagai 14,0.
    return pd.read_csv(io.BytesIO(isi), sep=None, engine="python",
                       encoding_errors="replace", dtype=str)


def tebak_kolom(df: pd.DataFrame) -> dict:
    """Menebak kolom tanggal, harga, dan (bila ada) komoditas dari namanya."""
    def cari(pola):
        for k in df.columns:
            if re.search(pola, str(k), re.I):
                return k
        return None
    return {"tanggal": cari(r"tanggal|tgl|date|periode|bulan|waktu"),
            "harga": cari(r"harga|price|nilai|rp"),
            "komoditas": cari(r"komoditas|barang|produk|item|nama")}


def bersihkan_angka(kolom: pd.Series) -> pd.Series:
    """Mengubah 'Rp 14.000' atau '14.000,50' menjadi angka."""
    if pd.api.types.is_numeric_dtype(kolom):
        return kolom.astype(float)

    def satu(x):
        t = re.sub(r"[^0-9,.\-]", "", str(x))
        if not t:
            return np.nan
        if "," in t:                       # gaya Indonesia: 14.000,50
            t = t.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):
            t = t.replace(".", "")         # 14.000 -> ribuan, bukan desimal
        try:
            return float(t)
        except ValueError:
            return np.nan

    return kolom.map(satu).astype(float)


def siapkan_unggahan(df: pd.DataFrame, kol_tanggal, kol_harga,
                     kol_komoditas=None, komoditas=None):
    """Mengubah tabel unggahan menjadi deret bulanan.

    Mengembalikan (deret, catatan). Catatan berisi hal yang diubah diam-diam
    dan layak diberitahukan kepada pengguna.
    """
    catatan = []
    d = df.copy()
    if kol_komoditas and komoditas is not None:
        d = d[d[kol_komoditas].astype(str) == str(komoditas)]
    tanggal = pd.to_datetime(d[kol_tanggal], errors="coerce", dayfirst=True)
    harga = bersihkan_angka(d[kol_harga])
    sah = tanggal.notna() & harga.notna() & (harga > 0)
    if (~sah).sum():
        catatan.append(f"{int((~sah).sum())} baris dilewati karena tanggal "
                       "atau harganya tidak terbaca.")
    if sah.sum() == 0:
        raise ValueError("Tidak ada baris yang bisa dibaca. Periksa nama "
                         "kolom tanggal dan harga.")
    deret = deret_bulanan(tanggal[sah], harga[sah])
    mentah = int(sah.sum())
    if mentah > len(deret):
        catatan.append(f"{mentah} catatan dirata-ratakan menjadi "
                       f"{len(deret)} bulan.")
    return deret, catatan


def contoh_berkas(df_harga: pd.DataFrame) -> bytes:
    """Contoh format unggahan, diambil dari data bawaan (Beras Medium)."""
    satu = df_harga[df_harga["komoditas"] == "Beras Medium"].sort_values("periode")
    contoh = pd.DataFrame({"tanggal": satu["periode"].dt.strftime("%Y-%m-%d"),
                           "komoditas": "Beras Medium",
                           "harga": satu["harga"].round(0).astype(int)})
    return contoh.to_csv(index=False).encode("utf-8")


# --------------------------------------------------------------------------
# Memasang model
# --------------------------------------------------------------------------
def pasang_sarima(latih: pd.Series, musiman: bool):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    terbaik = None
    for ordo, ordo_musiman in (CALON_MUSIMAN if musiman else CALON_BIASA):
        try:
            model = SARIMAX(latih, order=ordo, seasonal_order=ordo_musiman,
                            enforce_stationarity=False,
                            enforce_invertibility=False).fit(disp=False)
            if terbaik is None or model.aic < terbaik[0]:
                terbaik = (model.aic, ordo, ordo_musiman, model)
        except Exception:
            continue
    return terbaik


def pasang_hw(latih: pd.Series, musiman: bool):
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    if musiman:
        return ETSModel(latih, error="add", trend="add", seasonal="add",
                        seasonal_periods=MUSIM,
                        initialization_method="estimated").fit(disp=False)
    # Tanpa musiman: tren diredam supaya ramalan jauh tidak melaju lurus
    return ETSModel(latih, error="add", trend="add", damped_trend=True,
                    seasonal=None,
                    initialization_method="estimated").fit(disp=False)


# --------------------------------------------------------------------------
# Perhitungan utama
# --------------------------------------------------------------------------
def hitung(deret: pd.Series, langkah: int) -> dict:
    """Seluruh perhitungan satu deret. Hasilnya hanya tabel dan angka."""
    n = len(deret)
    uji_n = panjang_uji_untuk(n)
    if uji_n is None:
        raise ValueError(f"Data hanya {n} bulan. Dibutuhkan minimal "
                         f"{MIN_BULAN} bulan agar bisa diuji dan diramal.")

    tabel_deret = pd.DataFrame({"periode": deret.index, "harga": deret.values})
    bulan_depan = pd.date_range(deret.index[-1] + pd.offsets.MonthBegin(),
                                periods=langkah, freq="MS")
    mandek = bulan_sama_di_ujung(deret)

    # Pengaman: harga yang tidak bergerak tidak punya pola untuk dipelajari
    if mandek >= BULAN_MANDEK:
        v = float(deret.iloc[-1])
        return {"mandek": mandek, "deret": tabel_deret, "panjang_uji": uji_n,
                "musiman": None, "akhir_latih": None, "uji": None,
                "ukuran": None, "ordo": "—", "pemenang": None,
                "metode_ramalan": "Harga tetap",
                "ramalan": pd.DataFrame({"periode": bulan_depan, "ramalan": v,
                                         "bawah": v, "atas": v})}

    latih, uji = deret.iloc[:-uji_n], deret.iloc[-uji_n:]
    musiman = len(latih) >= 2 * MUSIM

    hasil_uji = pd.DataFrame({"periode": uji.index, "Aktual": uji.values})
    ukuran, ordo_terpilih = {}, "—"

    terbaik = pasang_sarima(latih, musiman)
    if terbaik is not None:
        _, ordo, ordo_musiman, model = terbaik
        ordo_terpilih = (f"SARIMA{ordo}{ordo_musiman}"
                         .replace(" ", "").replace(",)", ")"))
        hasil_uji["SARIMA"] = np.clip(model.forecast(uji_n).values, 0, None)
        ukuran["SARIMA"] = ukur(uji.values, hasil_uji["SARIMA"])

    try:
        hw = pasang_hw(latih, musiman)
        hasil_uji["Holt-Winters"] = np.clip(hw.forecast(uji_n).values, 0, None)
        ukuran["Holt-Winters"] = ukur(uji.values, hasil_uji["Holt-Winters"])
    except Exception:
        pass

    # Pembanding dasar: harga bulan ini ditebak sama dengan 12 bulan lalu
    naif = deret.shift(MUSIM).iloc[-uji_n:]
    hasil_uji[NAMA_PEMBANDING] = naif.values
    ukuran[NAMA_PEMBANDING] = ukur(uji.values, naif.values)

    tabel_ukuran = (pd.DataFrame(ukuran).T
                    .reset_index().rename(columns={"index": "Metode"})
                    .sort_values("MAPE").reset_index(drop=True))

    pemenang = tabel_ukuran.loc[0, "Metode"]
    selain_naif = tabel_ukuran.loc[tabel_ukuran["Metode"] != NAMA_PEMBANDING,
                                   "Metode"]
    if pemenang != NAMA_PEMBANDING:
        metode_ramalan = pemenang
    elif len(selain_naif):
        metode_ramalan = selain_naif.iloc[0]
    else:
        metode_ramalan = NAMA_PEMBANDING

    if metode_ramalan == "SARIMA":
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        # Pengaturan dipilih dari data LATIH saja. Memilih dengan mengintip
        # data uji sama dengan membocorkan kunci jawaban.
        _, ordo, ordo_musiman, _ = terbaik
        akhir = SARIMAX(deret, order=ordo, seasonal_order=ordo_musiman,
                        enforce_stationarity=False,
                        enforce_invertibility=False).fit(disp=False)
        ramal = akhir.get_forecast(langkah)
        nilai = ramal.predicted_mean
        batas = ramal.conf_int(alpha=SELANG)
        bawah, atas = batas.iloc[:, 0].values, batas.iloc[:, 1].values
    elif metode_ramalan == "Holt-Winters":
        akhir = pasang_hw(deret, musiman)
        ramal = akhir.get_prediction(start=len(deret),
                                     end=len(deret) + langkah - 1)
        nilai = ramal.predicted_mean
        batas = ramal.pred_int(alpha=SELANG)
        bawah, atas = batas.iloc[:, 0].values, batas.iloc[:, 1].values
    else:
        # Cadangan terakhir: ulangi pola 12 bulan terakhir, rentang dari
        # besar kesalahan pada data uji
        pola = deret.iloc[-MUSIM:].values
        nilai = np.array([pola[i % MUSIM] for i in range(langkah)])
        sigma = float(np.std(uji.values - naif.values))
        bawah, atas = nilai - 1.2816 * sigma, nilai + 1.2816 * sigma

    ramalan = pd.DataFrame({
        "periode": bulan_depan,
        "ramalan": np.clip(np.asarray(nilai, float), 0, None),
        "bawah": np.clip(np.asarray(bawah, float), 0, None),
        "atas": np.clip(np.asarray(atas, float), 0, None)})

    return {"mandek": mandek, "deret": tabel_deret, "panjang_uji": uji_n,
            "musiman": musiman, "akhir_latih": latih.index[-1],
            "uji": hasil_uji, "ukuran": tabel_ukuran, "ordo": ordo_terpilih,
            "pemenang": pemenang, "metode_ramalan": metode_ramalan,
            "ramalan": ramalan}


# --------------------------------------------------------------------------
# Pemeriksaan model (praproses dan validasi ala analisis deret waktu)
# --------------------------------------------------------------------------
def periksa_model(deret: pd.Series) -> dict:
    """Tiga pemeriksaan standar pada deret waktu:
      1. uji stasioneritas ADF pada data asli dan setelah diselisih;
      2. ACF dan PACF pada data yang sudah diselisih;
      3. uji Ljung-Box pada sisaan SARIMA (apakah masih ada pola tersisa).
    Setiap pemeriksaan dibungkus sendiri-sendiri: bila satu gagal, yang lain
    tetap jalan dan hasilnya kosong (None) untuk yang gagal."""
    from statsmodels.tsa.stattools import acf, adfuller, pacf
    from statsmodels.stats.diagnostic import acorr_ljungbox

    y = deret.astype(float)
    n = len(y)
    hasil = {"adf": [], "acf": None, "pacf": None, "lag": None, "batas": None,
             "ljung": None, "sisa": None, "ordo": None}

    d1 = y.diff().dropna()
    kandidat = [("Data asli (harga)", y),
                ("Setelah selisih bulanan (d=1)", d1)]
    if n >= 36:
        kandidat.append(("Selisih bulanan, lalu selisih tahunan (d=1, D=1)",
                         d1.diff(MUSIM).dropna()))
    for nama, seri in kandidat:
        try:
            if seri.nunique() < 3 or len(seri) < 10:
                continue
            stat, pnilai = adfuller(seri, autolag="AIC")[:2]
            hasil["adf"].append({"Perlakuan": nama,
                                 "Statistik ADF": float(stat),
                                 "p-value": float(pnilai),
                                 "Stasioner": bool(pnilai < 0.05)})
        except Exception:
            continue

    try:
        lag = int(min(24, len(d1) // 2 - 1))
        hasil["acf"] = np.asarray(acf(d1, nlags=lag, fft=False))[1:]
        hasil["pacf"] = np.asarray(pacf(d1, nlags=lag))[1:]
        hasil["lag"] = lag
        hasil["batas"] = float(1.96 / np.sqrt(len(d1)))
    except Exception:
        pass

    try:
        terbaik = pasang_sarima(y, n >= 36)
        if terbaik is not None:
            _, ordo, ordo_musiman, model = terbaik
            buang = max(1, int(ordo[1] + ordo_musiman[1] * ordo_musiman[3]))
            sisa = model.resid.iloc[buang:]
            lag_lb = int(max(1, min(12, len(sisa) // 4)))
            lb = acorr_ljungbox(sisa, lags=[lag_lb], return_df=True)
            pnilai = float(lb["lb_pvalue"].iloc[0])
            hasil["ljung"] = {"lag": lag_lb, "p": pnilai, "acak": pnilai > 0.05,
                              "n": int(len(sisa))}
            hasil["sisa"] = pd.DataFrame({"periode": sisa.index,
                                          "sisa": sisa.values})
            hasil["ordo"] = (f"SARIMA{ordo}{ordo_musiman}"
                             .replace(" ", "").replace(",)", ")"))
    except Exception:
        pass
    return hasil
