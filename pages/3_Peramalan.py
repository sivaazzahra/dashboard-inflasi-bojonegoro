"""
HALAMAN 3 — PERAMALAN
=====================

Meramalkan harga komoditas beberapa bulan ke depan, dan yang sama
pentingnya: mengukur seberapa bisa ramalan itu dipercaya.

Data yang diramal bisa data bawaan dashboard (SISKAPERBAPO Bojonegoro) atau
data yang diunggah pengguna sendiri. Seluruh hitungan ada di mesin_ramal.py.
"""

import io

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import mesin_ramal as mesin
from alat import (WARNA, angka, atur_halaman, bacaan, bagian, gaya, gaya_titik,
                  istilah, kartu, kepala, muat_harga, nama_bulan, periksa_data,
                  rupiah, sumber, wawasan)

atur_halaman("Peramalan")

if not periksa_data():
    st.stop()

harga = muat_harga()
PEMBANDING = mesin.NAMA_PEMBANDING


@st.cache_data(show_spinner="Memasang model dan menghitung ketepatannya…")
def jalankan(deret: pd.Series, langkah: int) -> dict:
    """Perhitungan satu deret, disimpan di tembolok. Hasilnya hanya tabel
    dan angka, bukan obyek model, supaya bisa disimpan Streamlit."""
    return mesin.hitung(deret, langkah)


# --------------------------------------------------------------------------
# Menu samping
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Atur tampilan")
    asal = st.radio(
        "Data yang diramal", ["Data bawaan Bojonegoro", "Unggah data sendiri"],
        help="Data bawaan berasal dari SISKAPERBAPO. Pilih unggah bila ingin "
             "meramal data harga milikmu sendiri, misalnya data terbaru "
             "yang kamu ambil dari SISKAPERBAPO.")
    pakai_unggahan = asal == "Unggah data sendiri"

    hanya_pangan = True
    if not pakai_unggahan:
        hanya_pangan = st.toggle("Hanya kelompok pangan", value=True)
        tersedia = harga[harga["pangan"]] if hanya_pangan else harga
        kelompok = st.selectbox("Kelompok",
                                options=sorted(tersedia["kelompok"].unique()))
        komoditas = st.selectbox(
            "Komoditas",
            options=sorted(tersedia[tersedia["kelompok"] == kelompok]
                           ["komoditas"].unique()))

    langkah = st.slider("Berapa bulan ke depan", 3, 12, 6,
                        help="Makin jauh ke depan, makin lebar rentang "
                             "kemungkinannya dan makin kurang bisa diandalkan.")

kepala("Peramalan Harga Komoditas",
       "Perkiraan harga beberapa bulan ke depan, beserta bukti seberapa "
       "bisa perkiraan itu dipercaya.",
       "Data bawaan atau unggahan sendiri · tiga cara menebak dibandingkan · "
       "diuji pada data yang disembunyikan",
       latar="latar_peramalan")

# --------------------------------------------------------------------------
# Sumber deret
# --------------------------------------------------------------------------
if not pakai_unggahan:
    deret = mesin.deret_dari_tabel(harga, komoditas)
else:
    bagian("Data kamu", "Unggah data harga untuk diramal",
           "Siapa pun bisa memakai halaman ini: ambil data harga terbaru "
           "(misalnya dari SISKAPERBAPO, yang datanya rilis tiap hari), "
           "unggah di sini, lalu lihat uji dan ramalannya.")
    k1, k2 = st.columns([2, 1])
    with k1:
        berkas = st.file_uploader("Berkas harga (CSV atau Excel)",
                                  type=["csv", "xlsx", "xls"])
    with k2:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.download_button("Unduh contoh format", mesin.contoh_berkas(harga),
                           file_name="contoh_format_harga.csv",
                           mime="text/csv", use_container_width=True)
    istilah(
        "<b>Format berkas.</b> Minimal dua kolom: <b>tanggal</b> dan "
        "<b>harga</b>. Satu kolom <b>komoditas</b> boleh ditambahkan bila "
        "berkasnya memuat beberapa komoditas. Data harian atau mingguan "
        "otomatis dirata-ratakan per bulan. Dibutuhkan <b>minimal 24 bulan</b>; "
        "idealnya 36 bulan atau lebih agar pola tahunan bisa dipelajari. "
        "Ramalan dimulai dari bulan setelah data terakhirmu: bila datamu "
        "berakhir Desember 2025, ramalannya mulai Januari 2026.")
    if berkas is None:
        st.info("Unggah berkas untuk mulai. Belum punya? Unduh contoh format "
                "di atas, lalu ganti isinya dengan datamu.")
        st.stop()
    try:
        tabel_unggah = mesin.baca_berkas(berkas.name, berkas.getvalue())
    except Exception as galat:
        st.error(f"Berkas tidak bisa dibaca: {galat}")
        st.stop()
    tebakan = mesin.tebak_kolom(tabel_unggah)
    kolom = list(tabel_unggah.columns)
    c1, c2, c3 = st.columns(3)
    kol_tanggal = c1.selectbox(
        "Kolom tanggal", kolom,
        index=kolom.index(tebakan["tanggal"]) if tebakan["tanggal"] in kolom else 0)
    kol_harga = c2.selectbox(
        "Kolom harga", kolom,
        index=kolom.index(tebakan["harga"]) if tebakan["harga"] in kolom
        else min(1, len(kolom) - 1))
    pilihan_kom = ["(tidak ada)"] + kolom
    kol_kom = c3.selectbox(
        "Kolom komoditas (opsional)", pilihan_kom,
        index=pilihan_kom.index(tebakan["komoditas"])
        if tebakan["komoditas"] in pilihan_kom else 0)
    komoditas = "Data unggahan"
    pilih_kom = None
    if kol_kom != "(tidak ada)":
        daftar = sorted(tabel_unggah[kol_kom].dropna().astype(str).unique())
        pilih_kom = st.selectbox("Komoditas yang diramal", daftar)
        komoditas = pilih_kom
    try:
        deret, catatan = mesin.siapkan_unggahan(
            tabel_unggah, kol_tanggal, kol_harga,
            None if kol_kom == "(tidak ada)" else kol_kom, pilih_kom)
    except ValueError as galat:
        st.error(str(galat))
        st.stop()
    depan = deret.index[-1] + pd.offsets.MonthBegin()
    st.success(
        f"Terbaca **{len(deret)} bulan**, dari {nama_bulan(deret.index[0])} "
        f"sampai {nama_bulan(deret.index[-1])}. Ramalan akan dimulai "
        f"{nama_bulan(depan)}.")
    for c in catatan:
        st.caption(c)

try:
    hasil = jalankan(deret, langkah)
except ValueError as galat:
    st.error(str(galat))
    st.stop()

deret_df = hasil["deret"]
ramalan = hasil["ramalan"]
harga_kini = float(deret_df["harga"].iloc[-1])
harga_akhir = float(ramalan["ramalan"].iloc[-1])
selisih = (harga_akhir / harga_kini - 1) * 100
nama_berkas = str(komoditas).replace("/", "_").replace(" ", "_")


# --------------------------------------------------------------------------
# Berkas unduhan
# --------------------------------------------------------------------------
def buat_excel() -> bytes:
    """Seluruh hasil dalam satu berkas Excel, satu lembar per tabel."""
    keluar = io.BytesIO()
    with pd.ExcelWriter(keluar, engine="openpyxl") as penulis:
        ramalan.rename(columns={"periode": "Bulan", "ramalan": "Ramalan",
                                "bawah": "Batas bawah 80%",
                                "atas": "Batas atas 80%"}).to_excel(
            penulis, sheet_name="Ramalan", index=False)
        if hasil["ukuran"] is not None:
            hasil["ukuran"].to_excel(penulis, sheet_name="Ketepatan uji",
                                     index=False)
            hasil["uji"].to_excel(penulis, sheet_name="Hasil uji", index=False)
        deret_df.rename(columns={"periode": "Bulan", "harga": "Harga"}).to_excel(
            penulis, sheet_name="Data bulanan", index=False)
    return keluar.getvalue()


def blok_unduh() -> None:
    a, b = st.columns(2)
    a.download_button(
        "Unduh hasil lengkap (Excel)", buat_excel(),
        file_name=f"ramalan_{nama_berkas}_{langkah}bulan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)
    b.download_button(
        "Unduh ramalan saja (CSV)",
        ramalan.to_csv(index=False).encode("utf-8"),
        file_name=f"ramalan_{nama_berkas}_{langkah}bulan.csv",
        mime="text/csv", use_container_width=True)


# --------------------------------------------------------------------------
# Kasus khusus: harga tidak berubah
# --------------------------------------------------------------------------
if hasil["mandek"] >= mesin.BULAN_MANDEK:
    n = hasil["mandek"]
    bagian("Peringatan data", f"Harga {komoditas} tidak berubah selama {n} bulan")
    bacaan(
        f"Harga <b>{komoditas}</b> tercatat persis <b>{rupiah(harga_kini)}</b> "
        f"selama <b>{n} bulan</b> terakhir. Harga barang di pasar hampir tidak "
        "pernah diam selama itu, sehingga kemungkinan besar angkanya "
        "<b>tidak diperbarui di sumber data</b> (bukan karena harganya benar-"
        "benar tetap). Model statistik tidak punya pola untuk dipelajari dari "
        "deretan angka yang sama, jadi dashboard <b>tidak menampilkan "
        "ramalan</b> untuk komoditas ini daripada memberi angka yang "
        "menyesatkan.")
    riw = deret_df.tail(48)
    fig = go.Figure(go.Scatter(
        x=riw["periode"], y=riw["harga"], mode="lines",
        line=dict(color=WARNA["seri1"], width=2.6),
        hovertemplate="Rp %{y:,.0f}<extra></extra>"))
    fig.update_yaxes(tickprefix="Rp ", separatethousands=True)
    st.plotly_chart(gaya(fig, 300), use_container_width=True)
    istilah(
        "<b>Apa yang bisa dilakukan?</b> Cek apakah komoditas ini memang "
        "diperbarui rutin oleh petugas pemantau harga. Bila data sumbernya "
        "sudah dikoreksi, unggah data terbaru melalui pilihan "
        "<b>Unggah data sendiri</b> di menu samping, lalu ramalannya bisa "
        "dihitung.")
    blok_unduh()
    st.stop()

ukuran = hasil["ukuran"]
uji = hasil["uji"]
terbaik = ukuran.iloc[0]
dipakai = ukuran[ukuran["Metode"] == hasil["metode_ramalan"]].iloc[0]
uji_n = hasil["panjang_uji"]
kolom_harga = "harga"

# --------------------------------------------------------------------------
# Ringkasan angka
# --------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
kartu(k1, "Cara menebak yang dipakai", hasil["metode_ramalan"],
      "mengikuti tren dan pola musim" if hasil["musiman"]
      else "mengikuti tren (data terlalu pendek untuk pola musim)", kecil=True)
kartu(k2, "Rata-rata meleset (MAPE)", angka(dipakai["MAPE"], 2) + "%",
      f"rata-rata ramalan meleset sebesar itu dari harga sebenarnya "
      f"pada {uji_n} bulan uji")
kartu(k3, f"Harga kini ({nama_bulan(deret_df['periode'].iloc[-1])})",
      rupiah(harga_kini), "pengamatan terakhir yang tersedia")
kartu(k4, f"Ramalan {nama_bulan(ramalan['periode'].iloc[-1])}",
      rupiah(harga_akhir),
      f"{angka(selisih, 1, tanda=True)}% dari harga kini")

# --------------------------------------------------------------------------
# 1. Pengujian
# --------------------------------------------------------------------------
bagian("Pengujian", "Seberapa tepat ramalannya ketika diuji",
       f"Seperti ujian: data {uji_n} bulan terakhir disembunyikan, lalu "
       f"tiga cara menebak diminta memperkirakannya. Garis hitam adalah harga "
       f"sebenarnya. Makin dekat sebuah garis ramalan dengan garis hitam, "
       f"makin tepat cara itu untuk {komoditas}.")
istilah(
    f"<b>Tiga cara menebak.</b> <b>{PEMBANDING}</b>: harga bulan ini "
    "ditebak sama dengan 12 bulan lalu. Ini cara paling sederhana, dipakai "
    "sebagai tolok ukur. <b>SARIMA</b> dan <b>Holt-Winters</b> adalah cara "
    "statistik yang mempelajari tren dan pola musiman. Cara statistik baru "
    "berguna kalau hasilnya lebih tepat daripada sekadar menyalin harga "
    "tahun lalu.")

fig = go.Figure()
riwayat = deret_df[deret_df["periode"] <= hasil["akhir_latih"]].tail(24)
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
                    (PEMBANDING, WARNA["redup"])]:
    if nama in uji:
        fig.add_trace(go.Scatter(
            x=uji["periode"], y=uji[nama], name=nama, mode="lines",
            line=dict(color=warna, width=2,
                      dash="dot" if nama == PEMBANDING else "dash"),
            hovertemplate=nama + " Rp %{y:,.0f}<extra></extra>"))
fig.add_vline(x=hasil["akhir_latih"], line_width=1, line_dash="dot",
              line_color=WARNA["redup"])
fig.update_yaxes(tickprefix="Rp ", separatethousands=True)
st.plotly_chart(gaya(fig, 380), use_container_width=True)

tampil = ukuran.copy()
tampil["RMSE"] = tampil["RMSE"].map(rupiah)
tampil["MAE"] = tampil["MAE"].map(rupiah)
tampil["MAPE"] = tampil["MAPE"].map(lambda v: angka(v, 2) + "%")
tampil = tampil.rename(columns={"RMSE": "RMSE (Rp)", "MAE": "MAE (Rp)",
                                "MAPE": "MAPE (%)"})
tampil.insert(0, "Peringkat", range(1, len(tampil) + 1))
st.dataframe(tampil, use_container_width=True, hide_index=True)
st.caption("RMSE dan MAE dalam rupiah, jadi hanya berlaku untuk komoditas "
           "ini. MAPE dalam persen, jadi bisa dibandingkan antarkomoditas. "
           "Karena itu pemenang ditentukan dari MAPE (makin kecil makin baik).")

istilah(
    "<b>Cara membaca tabel peringkat.</b> Baris teratas adalah cara yang "
    f"paling tepat <i>pada ujian</i> (MAPE terkecil). Pemenang ujian: "
    f"<b>{terbaik['Metode']}</b>. Metode yang dipakai untuk meramal ke depan: "
    f"<b>{hasil['metode_ramalan']}</b>."
    + (f"<br><b>Kenapa keduanya berbeda?</b> '{PEMBANDING}' hanyalah "
       "tolok ukur: ia menebak harga bulan depan sama dengan harga bulan yang "
       "sama tahun lalu. Cara itu tidak punya arah tren dan tidak bisa "
       "menghitung rentang kemungkinan, jadi tidak cocok sebagai alat meramal. "
       f"Karena itu ramalan memakai metode statistik terbaik berikutnya "
       f"({hasil['metode_ramalan']}). Tetapi karena metode statistik itu "
       f"<b>kalah tepat</b> dari sekadar menyalin harga tahun lalu, anggap ramalan "
       "di bawah sebagai gambaran kasar dan bandingkan dengan garis abu-abu "
       "putus-putus (harga tahun lalu) pada grafik proyeksi."
       if terbaik["Metode"] == PEMBANDING and hasil["metode_ramalan"] != PEMBANDING
       else ""))

mae_b, rmse_b = terbaik["MAE"], terbaik["RMSE"]
rasio = rmse_b / mae_b if mae_b else 1.0
istilah(
    "<b>Kenapa RMSE dan MAE bersatuan rupiah?</b> Karena keduanya dihitung "
    "langsung dari selisih antara harga sebenarnya dan harga ramalan, dan "
    "selisih dua harga satuannya tetap rupiah. "
    f"<br>• <b>MAE</b> adalah rata-rata selisih tanpa memandang arah. Untuk "
    f"{komoditas}, metode peringkat pertama ({terbaik['Metode']}) rata-rata "
    f"meleset <b>{rupiah(mae_b)}</b> dari harga sebenarnya. "
    f"<br>• <b>RMSE</b> mengkuadratkan selisih, merata-ratakannya, lalu "
    "diakarkan agar kembali ke rupiah. Kuadrat membuat meleset yang besar "
    f"dihukum lebih berat; nilainya {rupiah(rmse_b)}. "
    f"<br>• RMSE selalu sama dengan atau lebih besar dari MAE. Perbandingan "
    f"keduanya di sini <b>{angka(rasio, 2)}×</b>: "
    + ("hampir sama, jadi kesalahannya merata tiap bulan."
       if rasio < 1.25 else
       "cukup jauh, artinya ada beberapa bulan yang melesetnya jauh lebih "
       "besar dari bulan lain.")
    + "<br><b>Kelemahannya:</b> angka rupiah tidak adil dibandingkan antar "
      "komoditas. Meleset Rp 500 pada beras yang Rp 14.000 jauh lebih kecil "
      "artinya daripada pada komoditas yang Rp 2.000. Karena itu pemenang "
      "ditentukan dengan <b>MAPE</b>, yang berupa persen.")

naif = ukuran[ukuran["Metode"] == PEMBANDING]["MAPE"].iloc[0]
lebih_baik = naif - terbaik["MAPE"]
if terbaik["Metode"] == PEMBANDING:
    bacaan(
        f"Perlu dicatat: untuk {komoditas}, cara <b>{PEMBANDING.lower()}</b> "
        f"justru paling tepat (MAPE {angka(naif, 2)}%). Artinya model yang "
        "lebih rumit tidak memberi nilai tambah pada komoditas ini, dan "
        "ramalan di bawah memakai cara terbaik kedua. Temuan seperti ini tetap "
        "dilaporkan apa adanya, karena justru menunjukkan pengujiannya "
        "berjalan sebagaimana mestinya.")
else:
    bacaan(
        f"Cara terbaik untuk {komoditas} adalah <b>{terbaik['Metode']}</b> "
        f"dengan MAPE <b>{angka(terbaik['MAPE'], 2)}%</b>, artinya rata-rata "
        f"ramalannya meleset sekitar segitu dari harga sebenarnya. "
        f"Cara menyalin harga tahun lalu mencatat MAPE {angka(naif, 2)}%, "
        f"jadi model ini <b>{angka(lebih_baik, 2)} poin lebih baik</b> "
        "daripada sekadar menyalin harga tahun lalu, itulah bukti bahwa "
        "pemodelannya memberi nilai tambah.")

n_model = len(ukuran) - 1
n_kalah = int(((ukuran["MAPE"] > naif) & (ukuran["Metode"] != PEMBANDING)).sum())
layak = dipakai["MAPE"] < 10
wawasan("Temuan", [
    f"Dari {n_model} metode pemodelan, <b>{n_kalah}</b> kalah tepat dibanding "
    "cara menyalin harga tahun lalu. Kalau pemodelan tidak mengalahkan "
    "tolok ukur ini, kerumitannya tidak ada gunanya.",
    f"Metode yang dipakai meramal ({hasil['metode_ramalan']}) mencatat MAPE "
    f"<b>{angka(dipakai['MAPE'], 2)}%</b> pada data uji, "
    + ("di bawah ambang 10%, sehingga ramalannya layak dipakai sebagai "
       "gambaran arah." if layak else
       "di atas ambang 10%, sehingga ramalannya sebaiknya dipakai hati-hati "
       "dan hanya untuk satu-dua bulan ke depan."),
])

# --------------------------------------------------------------------------
# 2. Metode yang cocok
# --------------------------------------------------------------------------
bagian("Metode", f"Metode mana yang cocok untuk {komoditas}?")
penjelasan_metode = {
    "SARIMA": "SARIMA belajar dari hubungan harga bulan ini dengan bulan-bulan "
              "sebelumnya serta pola tahunannya. Cocok bila harga punya "
              "kebiasaan yang cukup teratur.",
    "Holt-Winters": "Holt-Winters menghaluskan data lalu meneruskan arah naik-"
                    "turun (tren) dan pola musimnya. Cocok bila pergerakan "
                    "harga cukup mulus.",
    PEMBANDING: "Menyalin harga tahun lalu menang bila pola tahunan sangat "
                "kuat dan stabil, atau bila data terlalu berantakan untuk "
                "dipelajari model yang rumit.",
}
baris_metode = []
for _, r in ukuran.iterrows():
    penanda = " ← dipakai meramal" if r["Metode"] == hasil["metode_ramalan"] else ""
    baris_metode.append(
        f"• <b>{r['Metode']}</b> (MAPE {angka(r['MAPE'], 2)}%){penanda}. "
        f"{penjelasan_metode.get(r['Metode'], '')}")
catatan_musim = (
    "" if hasil["musiman"] else
    "<br><b>Catatan:</b> data latih kurang dari 24 bulan, sehingga pola musim "
    "tahunan tidak dipelajari. Untuk hasil lebih baik, gunakan data minimal "
    "36 bulan.")
istilah("<b>Perbandingan tiga cara menebak.</b><br>" + "<br>".join(baris_metode)
        + catatan_musim)

# --------------------------------------------------------------------------
# 3. Ramalan ke depan
# --------------------------------------------------------------------------
bagian("Proyeksi", f"Ramalan {langkah} bulan ke depan",
       f"Dihitung dengan {hasil['metode_ramalan']} memakai seluruh data. "
       "Pita biru muda adalah rentang kemungkinan 80%: dari sepuluh kejadian "
       "serupa, delapan kali harga sebenarnya jatuh di dalam pita itu.")

riwayat2 = deret_df.tail(36)
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=list(ramalan["periode"]) + list(ramalan["periode"][::-1]),
    y=list(ramalan["atas"]) + list(ramalan["bawah"][::-1]),
    fill="toself", fillcolor="rgba(42,120,214,0.14)",
    mode="lines", line=dict(width=0), name="Rentang kemungkinan 80%",
    hoverinfo="skip"))
fig.add_trace(go.Scatter(
    x=riwayat2["periode"], y=riwayat2[kolom_harga], name="Harga tercatat",
    mode="lines", line=dict(color=WARNA["tinta"], width=2.4),
    hovertemplate="tercatat Rp %{y:,.0f}<extra></extra>"))
sambung = pd.concat([
    pd.DataFrame({"periode": [deret_df["periode"].iloc[-1]],
                  "ramalan": [harga_kini]}),
    ramalan[["periode", "ramalan"]]])
fig.add_trace(go.Scatter(
    x=sambung["periode"], y=sambung["ramalan"], name="Ramalan",
    mode="lines+markers", line=dict(color=WARNA["seri1"], width=2.6,
                                    dash="dash"),
    marker=dict(size=7),
    hovertemplate="ramalan Rp %{y:,.0f}<extra></extra>"))
if terbaik["Metode"] == PEMBANDING:
    # Garis pembanding: harga bulan yang sama tahun lalu
    peta = deret_df.set_index("periode")["harga"]
    tahun_lalu = [peta.get(t - pd.DateOffset(years=1)) for t in ramalan["periode"]]
    if all(v is not None for v in tahun_lalu):
        fig.add_trace(go.Scatter(
            x=ramalan["periode"], y=tahun_lalu, name="Harga tahun lalu (pembanding)",
            mode="lines", line=dict(color=WARNA["redup"], width=2, dash="dot"),
            hovertemplate="tahun lalu Rp %{y:,.0f}<extra></extra>"))
fig.add_vline(x=deret_df["periode"].iloc[-1], line_width=1, line_dash="dot",
              line_color=WARNA["redup"])
fig.update_yaxes(tickprefix="Rp ", separatethousands=True)
st.plotly_chart(gaya(fig, 400), use_container_width=True)
istilah(
    "<b>Cara membaca grafik.</b> Garis <b>hitam</b> adalah harga yang "
    "sudah tercatat. Garis <b>biru putus-putus</b> adalah ramalan. Pita "
    "<b>biru muda</b> adalah rentang kemungkinan 80%: harga sebenarnya "
    "diperkirakan jatuh di dalam pita itu. Pita yang melebar ke kanan "
    "berarti makin jauh ke depan, makin tidak pasti. Garis tegak titik-titik "
    "menandai batas antara data dan ramalan."
    + (" Garis <b>abu-abu putus-putus</b> adalah harga bulan yang sama tahun "
       "lalu, sebagai pembanding." if terbaik["Metode"] == PEMBANDING else ""))

lebar_awal = (ramalan["atas"].iloc[0] - ramalan["bawah"].iloc[0]) / harga_kini * 100
lebar_akhir = (ramalan["atas"].iloc[-1] - ramalan["bawah"].iloc[-1]) / harga_kini * 100
bacaan(
    f"Harga {komoditas} diramalkan bergerak dari <b>{rupiah(harga_kini)}</b> "
    f"menjadi <b>{rupiah(harga_akhir)}</b> pada "
    f"{nama_bulan(ramalan['periode'].iloc[-1])}, "
    + ("naik" if selisih >= 0 else "turun")
    + f" <b>{angka(abs(selisih), 1)}%</b>. Perhatikan pita kemungkinannya "
      f"melebar dari {angka(lebar_awal, 1)}% pada bulan pertama menjadi "
      f"{angka(lebar_akhir, 1)}% pada bulan terakhir. Itu wajar dan harus "
      "dibaca sebagai peringatan: makin jauh ke depan, makin tidak pasti. "
      "Ramalan satu sampai tiga bulan jauh lebih bisa dipegang daripada "
      "ramalan dua belas bulan.")

bln_puncak = ramalan.loc[ramalan["ramalan"].idxmax()]
bln_dasar = ramalan.loc[ramalan["ramalan"].idxmin()]
wawasan("Temuan", [
    f"Harga ramalan tertinggi jatuh pada <b>{nama_bulan(bln_puncak['periode'])}</b> "
    f"({rupiah(bln_puncak['ramalan'])}) dan terendah pada "
    f"<b>{nama_bulan(bln_dasar['periode'])}</b> ({rupiah(bln_dasar['ramalan'])}).",
    f"Pada bulan terakhir, harga diperkirakan berada antara "
    f"<b>{rupiah(ramalan['bawah'].iloc[-1])}</b> dan "
    f"<b>{rupiah(ramalan['atas'].iloc[-1])}</b>. Rentang selebar itu adalah "
    "ukuran ketidakpastian yang jujur, bukan kelemahan tampilan.",
    "Ramalan memakai pola masa lalu. Jika menjelang hari besar atau musim "
    "tanam pola itu berubah, angkanya perlu dibaca bersama informasi "
    "lapangan.",
])

# --------------------------------------------------------------------------
# 4. Unduh hasil
# --------------------------------------------------------------------------
bagian("Unduh", "Simpan hasilnya",
       "Berkas Excel berisi empat lembar: ramalan, ketepatan uji, hasil uji "
       "per bulan, dan data bulanan yang dipakai.")
blok_unduh()
with st.expander("Lihat angka ramalannya dalam tabel"):
    tabel = ramalan.copy()
    tabel["Bulan"] = tabel["periode"].map(nama_bulan)
    tabel["Ramalan"] = tabel["ramalan"].map(rupiah)
    tabel["Batas bawah (80%)"] = tabel["bawah"].map(rupiah)
    tabel["Batas atas (80%)"] = tabel["atas"].map(rupiah)
    tabel["Perubahan dari harga kini"] = (
        (tabel["ramalan"] / harga_kini - 1) * 100).map(
            lambda v: angka(v, 1, tanda=True) + "%")
    st.dataframe(tabel[["Bulan", "Ramalan", "Batas bawah (80%)",
                        "Batas atas (80%)", "Perubahan dari harga kini"]],
                 use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------
# 5. Analisis kebijakan
# --------------------------------------------------------------------------
bagian("Kebijakan", "Apa artinya bagi pengambil keputusan?",
       "Ramalan baru berguna kalau mengubah keputusan. Bagian ini "
       "menerjemahkan angka menjadi bahan pertimbangan, dihitung otomatis "
       "dari ramalan di atas.")

pertama_batas_atas = ramalan["atas"].iloc[0]
skenario = pd.DataFrame({
    "Skenario": ["Harga lebih murah dari perkiraan", "Perkiraan dasar",
                 "Harga lebih mahal dari perkiraan"],
    "Dasar": ["Batas bawah pita", "Garis ramalan", "Batas atas pita"],
    f"Harga {nama_bulan(ramalan['periode'].iloc[-1])}": [
        rupiah(ramalan["bawah"].iloc[-1]), rupiah(harga_akhir),
        rupiah(ramalan["atas"].iloc[-1])],
    "Dibanding harga kini": [
        angka((ramalan["bawah"].iloc[-1] / harga_kini - 1) * 100, 1, tanda=True) + "%",
        angka(selisih, 1, tanda=True) + "%",
        angka((ramalan["atas"].iloc[-1] / harga_kini - 1) * 100, 1, tanda=True) + "%"],
})
st.dataframe(skenario, use_container_width=True, hide_index=True)

butir = []
if selisih >= 5:
    butir.append(
        f"<b>Harga diperkirakan naik cukup berarti ({angka(selisih, 1)}%).</b> "
        "Bahan pertimbangan: periksa stok dan jalur pasokan di daerah "
        "penghasil, siapkan pasar murah atau operasi pasar bila harga "
        "mendekati batas atas pita, dan sampaikan perkiraan kepada pedagang "
        "dan masyarakat agar tidak terjadi belanja panik.")
elif selisih <= -5:
    butir.append(
        f"<b>Harga diperkirakan turun ({angka(abs(selisih), 1)}%).</b> Kabar "
        "baik bagi pembeli, tetapi waspadai tekanan di sisi produsen (petani, "
        "nelayan, peternak). Pantau harga di tingkat produsen, dan "
        "pertimbangkan dukungan penyerapan hasil bila harga jatuh jauh di "
        "bawah kebiasaan.")
else:
    butir.append(
        f"<b>Harga diperkirakan relatif stabil ({angka(selisih, 1, tanda=True)}%).</b> "
        "Pemantauan rutin sudah cukup. Tidak ada sinyal yang menuntut "
        "intervensi khusus dari ramalan ini.")
butir.append(
    f"<b>Titik pemicu.</b> Bila harga sebenarnya pada "
    f"{nama_bulan(ramalan['periode'].iloc[0])} melampaui "
    f"<b>{rupiah(pertama_batas_atas)}</b> (batas atas pita bulan pertama), "
    "itu pertanda ada gangguan di luar kebiasaan, misalnya pasokan atau "
    "distribusi, dan perlu pengecekan lapangan.")
if dipakai["MAPE"] >= 10:
    butir.append(
        f"<b>Ketepatan ujinya kurang baik (MAPE {angka(dipakai['MAPE'], 1)}%).</b> "
        "Jangan jadikan ramalan ini satu-satunya dasar keputusan. Gunakan "
        "untuk satu sampai tiga bulan pertama dan padukan dengan informasi "
        "lapangan.")
if lebar_akhir > 30:
    butir.append(
        f"<b>Ketidakpastian tinggi.</b> Pita kemungkinan melebar sampai "
        f"{angka(lebar_akhir, 0)}% dari harga kini. Untuk perencanaan, lebih "
        "aman memakai batas atas pita sebagai skenario terburuk daripada "
        "garis ramalannya.")
butir.append(
    "<b>Kaitannya dengan pengendalian inflasi daerah.</b> Langkah-langkah di "
    "atas sejalan dengan kerangka 4K yang lazim dipakai tim pengendalian "
    "inflasi: keterjangkauan harga, ketersediaan pasokan, kelancaran "
    "distribusi, dan komunikasi yang efektif. Ini bahan diskusi, bukan "
    "keputusan resmi.")
wawasan("Bahan pertimbangan kebijakan", butir)

# --------------------------------------------------------------------------
# 6. Ketepatan seluruh komoditas (hanya untuk data bawaan)
# --------------------------------------------------------------------------
if not pakai_unggahan:
    bagian("Perbandingan", "Komoditas mana yang memang bisa diramalkan",
           "Ketepatan peramalan berbeda jauh antarkomoditas. Bahan pokok yang "
           "harganya stabil bisa diramalkan dengan baik; bumbu yang harganya "
           "melonjak-lonjak hampir tidak bisa. Perhitungan ini memasang model "
           "untuk seluruh komoditas sehingga memakan waktu, jadi dijalankan "
           "hanya bila diminta.")

    @st.cache_data(show_spinner="Menghitung ketepatan seluruh komoditas, "
                                "mohon tunggu…")
    def ketepatan_semua(pangan_saja: bool) -> tuple:
        """Memasang Holt-Winters untuk semua komoditas sebagai gambaran kasar.
        Komoditas yang harganya mandek dikeluarkan, karena ketepatannya tidak
        bermakna."""
        sumber_data = harga[harga["pangan"]] if pangan_saja else harga
        baris, mandek_daftar = [], []
        for kom in sorted(sumber_data["komoditas"].unique()):
            s = mesin.deret_dari_tabel(harga, kom)
            if mesin.bulan_sama_di_ujung(s) >= mesin.BULAN_MANDEK:
                mandek_daftar.append(kom)
                continue
            latih, uji_s = s.iloc[:-mesin.MUSIM], s.iloc[-mesin.MUSIM:]
            try:
                r = mesin.pasang_hw(latih, True).forecast(mesin.MUSIM)
                baris.append({"Komoditas": kom,
                              "Kelompok": sumber_data.loc[
                                  sumber_data["komoditas"] == kom,
                                  "kelompok"].iloc[0],
                              "MAPE": mesin.ukur(uji_s.values, r.values)["MAPE"]})
            except Exception:
                continue
        tabel = (pd.DataFrame(baris).sort_values("MAPE")
                 .reset_index(drop=True))
        return tabel, mandek_daftar

    if st.button("Hitung ketepatan untuk semua komoditas"):
        semua, mandek_daftar = ketepatan_semua(hanya_pangan)
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
        if mandek_daftar:
            st.caption(
                f"{len(mandek_daftar)} komoditas tidak diikutkan karena "
                f"harganya tidak berubah selama {mesin.BULAN_MANDEK} bulan "
                "terakhir atau lebih (kemungkinan data tidak diperbarui): "
                + ", ".join(mandek_daftar) + ".")

# --------------------------------------------------------------------------
# Catatan
# --------------------------------------------------------------------------
bagian("Catatan", "Hal yang perlu diingat")
st.markdown(
    f"""
- **Yang diramalkan adalah harga komoditas, bukan angka inflasi.** Keduanya
  berkaitan erat (halaman Harga Pangan menunjukkan keeratan hubungannya),
  tetapi terjadi pada bulan yang sama, bukan satu mendahului yang lain. Jadi
  ini gambaran arah harga, bukan ramalan inflasi Kabupaten Bojonegoro.
- **Ujiannya baru dilakukan sekali**, pada {uji_n} bulan terakhir. Cara yang
  lebih ketat adalah mengulang ujian di beberapa titik waktu berbeda; itu
  belum dilakukan agar halaman tidak lambat.
- **Pengaturan model dibatasi pada beberapa pilihan tetap** supaya hasilnya
  bisa diulang orang lain. Bisa jadi ada pengaturan yang lebih baik yang
  tidak tercoba. Pemilihannya hanya memakai data latih, sehingga data uji
  benar-benar tidak ikut menentukan.
- **Rentang kemungkinan (pita biru) dihitung dengan anggapan** kesalahan
  tebakan menyebar merata. Pada komoditas yang harganya sering melonjak
  tajam, anggapan itu kurang pas, sehingga pita bisa terlalu sempit.
- **Kejadian luar biasa tidak diperhitungkan:** gagal panen, perubahan
  kebijakan impor, atau gangguan pasokan. Semua cara menebak di sini hanya
  belajar dari pola masa lalu.
- **Harga yang tidak berubah berbulan-bulan tidak diramal.** Itu biasanya
  tanda data tidak diperbarui di sumbernya, bukan tanda harga yang stabil.
""")

sumber(
    "Data bawaan: SISKAPERBAPO, Dinas Perindustrian dan Perdagangan Provinsi "
    "Jawa Timur, diolah. Data unggahan sepenuhnya milik pengunggah dan tidak "
    "disimpan oleh dashboard. Pemodelan menggunakan statsmodels: SARIMAX "
    "untuk SARIMA dan ETSModel untuk Holt-Winters.")
