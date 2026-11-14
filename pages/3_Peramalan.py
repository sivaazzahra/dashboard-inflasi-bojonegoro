"""
HALAMAN 3 — PERAMALAN
=====================

Meramalkan harga komoditas beberapa bulan ke depan, dan yang sama
pentingnya: mengukur seberapa bisa ramalan itu dipercaya.

Alur kerjanya:
  1. Data dibelah dua. Dua belas bulan terakhir disembunyikan dari model
     dan dipakai sebagai kunci jawaban.
  2. Tiga metode dijalankan pada bagian latih, lalu disuruh meramal
     dua belas bulan yang disembunyikan tadi.
  3. Ketepatan ketiganya diukur dengan RMSE, MAE, dan MAPE.
  4. Metode dengan MAPE terkecil dipasang ulang memakai seluruh data,
     barulah dipakai meramal ke depan.

Langkah 1 sampai 3 itu yang membedakan peramalan dari tebakan. Tanpa
pengujian pada data yang disembunyikan, tidak ada dasar untuk mengatakan
ramalannya layak dipakai.
"""

import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from alat import (WARNA, angka, atur_halaman, bacaan, bagian, gaya,
                  gaya_titik, kartu, kepala, muat_harga, nama_bulan,
                  periksa_data, rupiah, sumber)

# statsmodels gemar memperingatkan soal konvergensi pada deret pendek.
# Peringatan itu tidak mengubah hasil, jadi disenyapkan agar tidak
# memenuhi layar pengguna.
warnings.filterwarnings("ignore")
from statsmodels.tsa.exponential_smoothing.ets import ETSModel  # noqa: E402
from statsmodels.tsa.statespace.sarimax import SARIMAX  # noqa: E402

atur_halaman("Peramalan")

if not periksa_data():
    st.stop()

harga = muat_harga()

PANJANG_UJI = 12          # bulan yang disembunyikan sebagai kunci jawaban
MUSIM = 12                # satu siklus musiman = 12 bulan
SELANG = 0.20             # 1 - 0,20 = selang kepercayaan 80%

# Enam calon ordo SARIMA. Dipilih yang AIC-nya terkecil pada data latih.
# Daftarnya sengaja pendek dan tetap, bukan pencarian menyeluruh, supaya
# halaman tidak lambat dan hasilnya bisa diulang oleh orang lain.
CALON_ORDO = [((1, 1, 1), (1, 1, 1, MUSIM)),
              ((0, 1, 1), (0, 1, 1, MUSIM)),
              ((1, 1, 0), (1, 1, 0, MUSIM)),
              ((2, 1, 1), (1, 1, 1, MUSIM)),
              ((1, 1, 1), (0, 1, 1, MUSIM)),
              ((0, 1, 1), (1, 1, 1, MUSIM))]


# --------------------------------------------------------------------------
# Perhitungan
# --------------------------------------------------------------------------
def ukur(aktual, ramalan) -> dict:
    """Tiga ukuran ketepatan yang lazim dipakai pada peramalan.

    RMSE dan MAE bersatuan rupiah, jadi tidak bisa dibandingkan antar
    komoditas yang harganya berbeda jauh. MAPE bersatuan persen, sehingga
    bisa. Karena itu pemenang ditentukan dengan MAPE.
    """
    a, r = np.asarray(aktual, float), np.asarray(ramalan, float)
    bukan_nol = a != 0
    return {
        "RMSE": float(np.sqrt(np.mean((a - r) ** 2))),
        "MAE": float(np.mean(np.abs(a - r))),
        "MAPE": (float(np.mean(np.abs((a[bukan_nol] - r[bukan_nol])
                                      / a[bukan_nol])) * 100)
                 if bukan_nol.any() else np.nan),
    }


def ambil_deret(df: pd.DataFrame, komoditas: str) -> pd.Series:
    """Mengubah data panjang menjadi satu deret waktu bulanan yang rapat.

    Model deret waktu menuntut jarak antarpengamatan yang tetap, jadi
    frekuensinya dipaksa bulanan dan lubang kecil ditambal dengan
    interpolasi linear.
    """
    s = df[df["komoditas"] == komoditas].set_index("periode")["harga"].sort_index()
    s.index = pd.DatetimeIndex(s.index).to_period("M").to_timestamp()
    return s.asfreq("MS").interpolate()


def pasang_sarima(latih: pd.Series):
    """Memasang SARIMA dengan ordo terbaik menurut AIC."""
    terbaik = None
    for ordo, ordo_musiman in CALON_ORDO:
        try:
            model = SARIMAX(latih, order=ordo, seasonal_order=ordo_musiman,
                            enforce_stationarity=False,
                            enforce_invertibility=False).fit(disp=False)
            if terbaik is None or model.aic < terbaik[0]:
                terbaik = (model.aic, ordo, ordo_musiman, model)
        except Exception:
            continue
    return terbaik


def pasang_hw(latih: pd.Series):
    """Memasang Holt-Winters aditif (galat, tren, dan musiman aditif)."""
    return ETSModel(latih, error="add", trend="add", seasonal="add",
                    seasonal_periods=MUSIM,
                    initialization_method="estimated").fit(disp=False)


@st.cache_data(show_spinner="Memasang model dan menghitung ketepatannya…")
def jalankan(komoditas: str, langkah: int) -> dict:
    """Seluruh perhitungan satu komoditas, disimpan di tembolok.

    Hasilnya hanya berisi tabel dan angka, bukan obyek model, supaya bisa
    disimpan Streamlit dan tidak dihitung ulang setiap kali layar disegarkan.
    """
    deret = ambil_deret(harga, komoditas)
    latih, uji = deret.iloc[:-PANJANG_UJI], deret.iloc[-PANJANG_UJI:]

    hasil_uji = pd.DataFrame({"periode": uji.index, "Aktual": uji.values})
    ukuran, ordo_terpilih = {}, "—"

    # --- SARIMA
    terbaik = pasang_sarima(latih)
    if terbaik is not None:
        _, ordo, ordo_musiman, model = terbaik
        ordo_terpilih = (f"SARIMA{ordo}{ordo_musiman}"
                         .replace(" ", "").replace(",)", ")"))
        hasil_uji["SARIMA"] = model.forecast(PANJANG_UJI).values
        ukuran["SARIMA"] = ukur(uji.values, hasil_uji["SARIMA"])

    # --- Holt-Winters
    try:
        hw = pasang_hw(latih)
        hasil_uji["Holt-Winters"] = hw.forecast(PANJANG_UJI).values
        ukuran["Holt-Winters"] = ukur(uji.values, hasil_uji["Holt-Winters"])
    except Exception:
        pass

    # --- Naif musiman: harga bulan ini diramal sama dengan 12 bulan lalu.
    # Pembanding dasar. Model yang tidak mampu mengalahkannya tidak layak
    # dipakai, sebab berarti kerumitannya tidak menghasilkan apa-apa.
    naif = deret.shift(MUSIM).iloc[-PANJANG_UJI:]
    hasil_uji["Naif musiman"] = naif.values
    ukuran["Naif musiman"] = ukur(uji.values, naif.values)

    tabel_ukuran = (pd.DataFrame(ukuran).T
                    .reset_index().rename(columns={"index": "Metode"})
                    .sort_values("MAPE").reset_index(drop=True))

    # --- Pemenang dipasang ulang pada SELURUH data, lalu meramal ke depan.
    # Memasang ulang itu penting: model akhir harus memanfaatkan semua
    # pengamatan yang ada, termasuk dua belas bulan yang tadi disembunyikan.
    pemenang = tabel_ukuran.loc[0, "Metode"]
    metode_ramalan = pemenang if pemenang != "Naif musiman" else tabel_ukuran.loc[
        tabel_ukuran["Metode"] != "Naif musiman", "Metode"].iloc[0]

    if metode_ramalan == "SARIMA":
        # Ordo yang dipakai adalah ordo yang terpilih pada data LATIH, bukan
        # hasil pencarian ulang pada seluruh data. Ini disengaja: memilih
        # ordo dengan melihat data uji berarti model sudah mengintip kunci
        # jawaban, sehingga ketepatan yang dilaporkan jadi terlalu bagus.
        _, ordo, ordo_musiman, _ = terbaik
        akhir = SARIMAX(deret, order=ordo, seasonal_order=ordo_musiman,
                        enforce_stationarity=False,
                        enforce_invertibility=False).fit(disp=False)
        ramal = akhir.get_forecast(langkah)
        nilai = ramal.predicted_mean
        batas = ramal.conf_int(alpha=SELANG)
        bawah, atas = batas.iloc[:, 0].values, batas.iloc[:, 1].values
    else:
        akhir = pasang_hw(deret)
        ramal = akhir.get_prediction(start=len(deret),
                                     end=len(deret) + langkah - 1)
        nilai = ramal.predicted_mean
        batas = ramal.pred_int(alpha=SELANG)
        bawah, atas = batas.iloc[:, 0].values, batas.iloc[:, 1].values

    bulan_depan = pd.date_range(deret.index[-1] + pd.offsets.MonthBegin(),
                                periods=langkah, freq="MS")
    ramalan = pd.DataFrame({
        "periode": bulan_depan,
        "ramalan": np.asarray(nilai, float),
        "bawah": np.asarray(bawah, float),
        "atas": np.asarray(atas, float)})

    return {
        "deret": deret.reset_index().rename(columns={"index": "periode",
                                                     0: "harga"}),
        "akhir_latih": latih.index[-1],
        "uji": hasil_uji,
        "ukuran": tabel_ukuran,
        "ordo": ordo_terpilih,
        "pemenang": pemenang,
        "metode_ramalan": metode_ramalan,
        "ramalan": ramalan,
    }


# --------------------------------------------------------------------------
# Penyaring
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Penyaring")
    hanya_pangan = st.toggle("Hanya kelompok pangan", value=True)
    tersedia = harga[harga["pangan"]] if hanya_pangan else harga

    kelompok = st.selectbox("Kelompok",
                            options=sorted(tersedia["kelompok"].unique()))
    komoditas = st.selectbox(
        "Komoditas",
        options=sorted(tersedia[tersedia["kelompok"] == kelompok]["komoditas"].unique()))
    langkah = st.slider("Berapa bulan diramalkan", 3, 12, 6,
                        help="Makin jauh ke depan, makin lebar selang "
                             "kepercayaannya — dan makin tipis gunanya.")

hasil = jalankan(komoditas, langkah)
deret = hasil["deret"]
kolom_harga = deret.columns[-1]
ukuran = hasil["ukuran"]
ramalan = hasil["ramalan"]
terbaik = ukuran.iloc[0]

kepala("Peramalan Harga Komoditas",
       "Ramalan beberapa bulan ke depan, beserta pengujian yang menjadi "
       "dasar untuk memercayainya.",
       f"{komoditas} · tiga metode dibandingkan · "
       f"diuji pada {PANJANG_UJI} bulan terakhir")

# --------------------------------------------------------------------------
# Ringkasan angka
# --------------------------------------------------------------------------
harga_kini = float(deret[kolom_harga].iloc[-1])
harga_akhir = float(ramalan["ramalan"].iloc[-1])
selisih = (harga_akhir / harga_kini - 1) * 100

k1, k2, k3, k4 = st.columns(4)
kartu(k1, "Metode terpilih", hasil["metode_ramalan"],
      hasil["ordo"] if hasil["metode_ramalan"] == "SARIMA"
      else "galat, tren, dan musiman aditif", kecil=True)
kartu(k2, "MAPE pada data uji", angka(terbaik["MAPE"], 2) + "%",
      f"rata-rata meleset sebesar itu dari harga sebenarnya "
      f"selama {PANJANG_UJI} bulan uji")
kartu(k3, f"Harga kini ({nama_bulan(deret['periode'].iloc[-1])})",
      rupiah(harga_kini), "pengamatan terakhir yang tersedia")
kartu(k4, f"Ramalan {nama_bulan(ramalan['periode'].iloc[-1])}",
      rupiah(harga_akhir),
      f"{angka(selisih, 1, tanda=True)}% dari harga kini")

# --------------------------------------------------------------------------
# 1. Pengujian
# --------------------------------------------------------------------------
bagian("Pengujian", "Seberapa tepat ramalannya ketika diuji",
       f"Dua belas bulan terakhir disembunyikan dari model, lalu ketiga "
       f"metode disuruh menebaknya. Garis hitam adalah harga sebenarnya. "
       f"Makin rapat sebuah garis ramalan menempel padanya, makin tepat "
       f"metode itu untuk {komoditas}.")

uji = hasil["uji"]
fig = go.Figure()
riwayat = deret[deret["periode"] <= hasil["akhir_latih"]].tail(24)
fig.add_trace(go.Scatter(
    x=riwayat["periode"], y=riwayat[kolom_harga], name="Data latih",
    mode="lines", line=dict(color=WARNA["redup"], width=1.8),
    hovertemplate="Rp %{y:,.0f}<extra></extra>"))
fig.add_trace(go.Scatter(
    x=uji["periode"], y=uji["Aktual"], name="Harga sebenarnya",
    mode="lines+markers", line=dict(color=WARNA["tinta"], width=2.6),
    marker=dict(size=7),
    hovertemplate="sebenarnya Rp %{y:,.0f}<extra></extra>"))
for nama, warna in [("SARIMA", WARNA["seri1"]),
                    ("Holt-Winters", WARNA["seri2"]),
                    ("Naif musiman", WARNA["redup"])]:
    if nama in uji:
        fig.add_trace(go.Scatter(
            x=uji["periode"], y=uji[nama], name=nama, mode="lines",
            line=dict(color=warna, width=2,
                      dash="dot" if nama == "Naif musiman" else "dash"),
            hovertemplate=nama + " Rp %{y:,.0f}<extra></extra>"))
fig.add_vline(x=hasil["akhir_latih"], line_width=1, line_dash="dot",
              line_color=WARNA["redup"])
fig.update_yaxes(tickprefix="Rp ", separatethousands=True)
st.plotly_chart(gaya(fig, 380), use_container_width=True)

tampil = ukuran.copy()
tampil["RMSE"] = tampil["RMSE"].map(rupiah)
tampil["MAE"] = tampil["MAE"].map(rupiah)
tampil["MAPE"] = tampil["MAPE"].map(lambda v: angka(v, 2) + "%")
tampil.insert(0, "Peringkat", range(1, len(tampil) + 1))
st.dataframe(tampil, use_container_width=True, hide_index=True)
st.caption("RMSE dan MAE bersatuan rupiah sehingga hanya berlaku untuk "
           "komoditas ini. MAPE bersatuan persen sehingga bisa dibandingkan "
           "antarkomoditas — karena itu pemenang ditentukan dengan MAPE.")

naif = ukuran[ukuran["Metode"] == "Naif musiman"]["MAPE"].iloc[0]
lebih_baik = naif - terbaik["MAPE"]
if terbaik["Metode"] == "Naif musiman":
    bacaan(
        f"Perlu dicatat: untuk {komoditas}, pembanding dasar <b>naif "
        f"musiman</b> justru paling tepat (MAPE {angka(naif, 2)}%). Artinya "
        "kedua model yang lebih rumit tidak memberi nilai tambah pada "
        "komoditas ini, dan ramalan di bawah memakai metode terbaik kedua. "
        "Temuan seperti ini tetap dilaporkan apa adanya, karena justru "
        "menunjukkan pengujiannya berjalan sebagaimana mestinya.")
else:
    bacaan(
        f"Metode terbaik untuk {komoditas} adalah <b>{terbaik['Metode']}</b> "
        f"dengan MAPE <b>{angka(terbaik['MAPE'], 2)}%</b>, artinya rata-rata "
        f"ramalannya meleset sekitar segitu dari harga sebenarnya. "
        f"Pembanding dasar naif musiman mencatat MAPE {angka(naif, 2)}%, "
        f"jadi model ini <b>{angka(lebih_baik, 2)} poin lebih baik</b> "
        "daripada sekadar menyalin harga tahun lalu — itulah bukti bahwa "
        "pemodelannya memang memberi nilai tambah.")

# --------------------------------------------------------------------------
# 2. Ramalan ke depan
# --------------------------------------------------------------------------
bagian("Proyeksi", f"Ramalan {langkah} bulan ke depan",
       f"Dihitung dengan {hasil['metode_ramalan']} yang dipasang ulang "
       "memakai seluruh data, termasuk dua belas bulan uji tadi. Pita biru "
       "muda adalah selang kepercayaan 80%: harga sebenarnya diperkirakan "
       "jatuh di dalam pita itu pada delapan dari sepuluh kejadian.")

riwayat2 = deret.tail(36)
# Pita digambar lebih dulu agar garis ramalan berada di atasnya
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=list(ramalan["periode"]) + list(ramalan["periode"][::-1]),
    y=list(ramalan["atas"]) + list(ramalan["bawah"][::-1]),
    fill="toself", fillcolor="rgba(42,120,214,0.14)",
    mode="lines",           # tanpa ini Plotly ikut menggambar titik di tepi pita
    line=dict(width=0), name="Selang kepercayaan 80%",
    hoverinfo="skip"))
fig.add_trace(go.Scatter(
    x=riwayat2["periode"], y=riwayat2[kolom_harga], name="Harga tercatat",
    mode="lines", line=dict(color=WARNA["tinta"], width=2.4),
    hovertemplate="tercatat Rp %{y:,.0f}<extra></extra>"))
# Satu titik riwayat terakhir disambungkan agar garis ramalan tidak terputus
sambung = pd.concat([
    pd.DataFrame({"periode": [deret["periode"].iloc[-1]],
                  "ramalan": [harga_kini]}),
    ramalan[["periode", "ramalan"]]])
fig.add_trace(go.Scatter(
    x=sambung["periode"], y=sambung["ramalan"], name="Ramalan",
    mode="lines+markers", line=dict(color=WARNA["seri1"], width=2.6,
                                    dash="dash"),
    marker=dict(size=7),
    hovertemplate="ramalan Rp %{y:,.0f}<extra></extra>"))
fig.add_vline(x=deret["periode"].iloc[-1], line_width=1, line_dash="dot",
              line_color=WARNA["redup"])
fig.update_yaxes(tickprefix="Rp ", separatethousands=True)
st.plotly_chart(gaya(fig, 400), use_container_width=True)

lebar_awal = (ramalan["atas"].iloc[0] - ramalan["bawah"].iloc[0]) / harga_kini * 100
lebar_akhir = (ramalan["atas"].iloc[-1] - ramalan["bawah"].iloc[-1]) / harga_kini * 100
bacaan(
    f"Harga {komoditas} diramalkan bergerak dari <b>{rupiah(harga_kini)}</b> "
    f"menjadi <b>{rupiah(harga_akhir)}</b> pada "
    f"{nama_bulan(ramalan['periode'].iloc[-1])}, "
    + ("naik" if selisih >= 0 else "turun")
    + f" <b>{angka(abs(selisih), 1)}%</b>. Perhatikan pita kepercayaannya "
      f"melebar dari {angka(lebar_awal, 1)}% pada bulan pertama menjadi "
      f"{angka(lebar_akhir, 1)}% pada bulan terakhir. Itu wajar dan harus "
      "dibaca sebagai peringatan: makin jauh ke depan, makin tidak pasti. "
      "Ramalan satu sampai tiga bulan jauh lebih bisa dipegang daripada "
      "ramalan dua belas bulan.")

# --------------------------------------------------------------------------
# 3. Tabel ramalan
# --------------------------------------------------------------------------
with st.expander("Lihat angka ramalannya dalam tabel"):
    tabel = ramalan.copy()
    tabel["Bulan"] = tabel["periode"].map(nama_bulan)
    tabel["Ramalan"] = tabel["ramalan"].map(rupiah)
    tabel["Batas bawah (80%)"] = tabel["bawah"].map(rupiah)
    tabel["Batas atas (80%)"] = tabel["atas"].map(rupiah)
    tabel["Perubahan dari harga kini"] = (
        (tabel["ramalan"] / harga_kini - 1) * 100).map(
            lambda v: angka(v, 1, tanda=True) + "%")
    tampil_tabel = tabel[["Bulan", "Ramalan", "Batas bawah (80%)",
                          "Batas atas (80%)", "Perubahan dari harga kini"]]
    st.dataframe(tampil_tabel, use_container_width=True, hide_index=True)
    st.download_button(
        "Unduh ramalan ini (CSV)",
        tampil_tabel.to_csv(index=False).encode("utf-8"),
        file_name=f"ramalan_{komoditas.replace('/', '_')}_{langkah}bulan.csv",
        mime="text/csv")

# --------------------------------------------------------------------------
# 4. Ketepatan seluruh komoditas
# --------------------------------------------------------------------------
bagian("Perbandingan", "Komoditas mana yang memang bisa diramalkan",
       "Ketepatan peramalan berbeda jauh antarkomoditas. Bahan pokok yang "
       "harganya stabil bisa diramalkan dengan baik; bumbu yang harganya "
       "melonjak-lonjak hampir tidak bisa. Perhitungan ini memasang model "
       "untuk seluruh komoditas sehingga memakan waktu, jadi dijalankan "
       "hanya bila diminta.")


@st.cache_data(show_spinner="Menghitung ketepatan seluruh komoditas, "
                            "mohon tunggu…")
def ketepatan_semua(pangan_saja: bool) -> pd.DataFrame:
    """Memasang Holt-Winters untuk semua komoditas sebagai gambaran kasar.

    Hanya satu metode yang dipakai di sini, bukan ketiganya, supaya
    perhitungannya tidak terlalu lama. Tujuannya memang hanya memeringkat
    komoditas menurut seberapa bisa diramalkan.
    """
    sumber_data = harga[harga["pangan"]] if pangan_saja else harga
    baris = []
    for kom in sorted(sumber_data["komoditas"].unique()):
        s = ambil_deret(harga, kom)
        latih, uji_s = s.iloc[:-PANJANG_UJI], s.iloc[-PANJANG_UJI:]
        try:
            r = pasang_hw(latih).forecast(PANJANG_UJI)
            baris.append({"Komoditas": kom,
                          "Kelompok": sumber_data.loc[
                              sumber_data["komoditas"] == kom,
                              "kelompok"].iloc[0],
                          "MAPE": ukur(uji_s.values, r.values)["MAPE"]})
        except Exception:
            continue
    return pd.DataFrame(baris).sort_values("MAPE").reset_index(drop=True)


if st.button("Hitung ketepatan untuk semua komoditas"):
    semua = ketepatan_semua(hanya_pangan)
    urut = semua.sort_values("MAPE", ascending=False)
    fig = go.Figure(go.Bar(
        x=urut["MAPE"], y=urut["Komoditas"], orientation="h",
        marker=dict(color=[WARNA["seri2"] if k == komoditas
                           else WARNA["seri1"] for k in urut["Komoditas"]],
                    line=dict(width=0)),
        customdata=urut[["Kelompok"]],
        hovertemplate="<b>%{y}</b><br>%{customdata[0]}"
                      "<br>MAPE %{x:.2f}%<extra></extra>"))
    fig.add_vline(x=10, line_width=1, line_dash="dash",
                  line_color=WARNA["naik"])
    fig.update_xaxes(ticksuffix="%")
    st.plotly_chart(gaya_titik(fig, 60 + 22 * len(urut)),
                    use_container_width=True)
    bisa = int((semua["MAPE"] < 10).sum())
    st.caption(
        f"Garis merah putus-putus pada 10% adalah ambang yang lazim dipakai: "
        f"di bawahnya ramalan tergolong layak pakai. {bisa} dari "
        f"{len(semua)} komoditas memenuhinya. Batang jingga menandai "
        f"{komoditas}.")

# --------------------------------------------------------------------------
# Catatan
# --------------------------------------------------------------------------
bagian("Catatan", "Batas dari apa yang bisa diklaim")
st.markdown(
    f"""
- Yang diramalkan di halaman ini adalah **harga komoditas**, bukan angka
  inflasi. Keduanya berkaitan erat — halaman Harga Pangan menunjukkan
  korelasinya +0,783 — tetapi hubungan itu bersamaan waktu, bukan
  mendahului. Jadi ramalan ini memberi gambaran arah tekanan harga, bukan
  ramalan inflasi Kabupaten Bojonegoro.
- Pengujian dilakukan sekali, pada {PANJANG_UJI} bulan terakhir. Cara yang
  lebih ketat adalah pengujian bergulir (*rolling origin*), yaitu mengulang
  pengujian pada beberapa titik potong yang berbeda. Itu belum dilakukan di
  sini karena akan memperlambat halaman.
- Ordo SARIMA dipilih dari enam calon tetap berdasarkan AIC, bukan
  pencarian menyeluruh. Pilihan ini membuat hasilnya bisa diulang orang
  lain, dengan risiko ada ordo lebih baik yang tidak tercoba. Ordonya
  dipilih hanya dengan melihat data latih, lalu dipakai apa adanya pada
  model akhir — supaya data uji benar-benar tidak pernah ikut menentukan
  bentuk model.
- Selang kepercayaan dihitung dengan anggapan galat model menyebar normal.
  Pada komoditas yang harganya sering melonjak tajam, anggapan itu lemah,
  sehingga selangnya cenderung terlalu sempit.
- Ramalan tidak memperhitungkan kejadian luar biasa: gagal panen, perubahan
  kebijakan impor, atau gangguan pasokan. Semua model di sini hanya belajar
  dari pola masa lalu.
""")

sumber(
    "Data: SISKAPERBAPO, Dinas Perindustrian dan Perdagangan Provinsi Jawa "
    "Timur, diolah. Pemodelan menggunakan statsmodels — SARIMAX untuk SARIMA "
    "dan ETSModel untuk Holt-Winters.")
