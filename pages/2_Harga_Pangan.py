"""
HALAMAN 2 — HARGA PANGAN
========================

Menjawab empat pertanyaan:
  1. Bagaimana perkembangan harga sebuah komoditas?
  2. Komoditas mana yang paling bergejolak?
  3. Adakah pola musimannya?
  4. Apakah harga pasar ini memang sejalan dengan inflasi resmi BPS?

Pertanyaan keempat yang paling penting. Data harga berasal dari Disperindag
Jawa Timur, sedangkan inflasi dihitung BPS. Keduanya sumber berbeda, jadi
kaitannya perlu dibuktikan, bukan diandaikan.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from alat import (WARNA, angka, atur_halaman, bacaan, bagian, gaya,
                  gaya_titik, kartu, kepala, muat_harga, navigasi, muat_jembatan,
                  nama_bulan, periksa_data, persen, rupiah, sumber, BULAN_ID,
                  wawasan, istilah)

atur_halaman("Harga Pangan")

if not periksa_data():
    st.stop()

harga = muat_harga()
jembatan = muat_jembatan()

bulan_akhir = harga["periode"].max()
terkini = harga[harga["periode"] == bulan_akhir]

# --------------------------------------------------------------------------
# Penyaring
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Atur tampilan")
    hanya_pangan = st.toggle("Hanya kelompok pangan", value=True,
                             help="Mematikannya akan memunculkan bahan "
                                  "bangunan dan pupuk.")
    sumber_pilihan = harga[harga["pangan"]] if hanya_pangan else harga

    kelompok = st.selectbox(
        "Kelompok", options=sorted(sumber_pilihan["kelompok"].unique()),
        index=0)
    daftar_komoditas = sorted(
        sumber_pilihan[sumber_pilihan["kelompok"] == kelompok]["komoditas"].unique())
    komoditas = st.selectbox("Komoditas", options=daftar_komoditas, index=0)

    tahun_tersedia = sorted(harga["periode"].dt.year.unique())
    th_awal, th_akhir = st.select_slider(
        "Rentang tahun", options=tahun_tersedia,
        value=(tahun_tersedia[0], tahun_tersedia[-1]))

satu = harga[(harga["komoditas"] == komoditas)
             & (harga["periode"].dt.year >= th_awal)
             & (harga["periode"].dt.year <= th_akhir)].sort_values("periode")

kepala("Harga Pangan di Pasar Bojonegoro",
       "Harga bahan pokok yang dipantau tiap hari, diringkas per bulan. "
       "Inilah yang menggerakkan kenaikan harga makanan.",
       f"{harga.komoditas.nunique()} komoditas · "
       f"{harga.periode.nunique()} bulan · sampai {nama_bulan(bulan_akhir)}",
       latar="latar_harga")
navigasi()

# --------------------------------------------------------------------------
# Ringkasan angka
# --------------------------------------------------------------------------
waspada = terkini[terkini["status"].str.startswith("Waspada")]
tergejolak = (harga.drop_duplicates("komoditas")
              .nlargest(1, "volatilitas_pct").iloc[0])
baris_akhir = satu.iloc[-1]

k1, k2, k3, k4 = st.columns(4)
kartu(k1, f"Harga {komoditas} terkini", rupiah(baris_akhir["harga"]),
      f"{nama_bulan(baris_akhir['periode'])} · "
      f"{persen(baris_akhir['perubahan_mom_pct'])} dari bulan lalu")
kartu(k2, "Perubahan harga dalam setahun",
      persen(baris_akhir["perubahan_yoy_pct"]),
      "dibanding bulan yang sama tahun lalu")
kartu(k3, "Harga yang perlu diwaspadai", f"{len(waspada)} dari {len(terkini)}",
      "harganya lebih dari 15% di atas atau di bawah rata-rata setahun terakhir")
kartu(k4, "Paling naik-turun", tergejolak["komoditas"],
      f"harganya naik-turun sekitar {angka(tergejolak['volatilitas_pct'])}% tiap bulan",
      kecil=True)

# --------------------------------------------------------------------------
# 1. Tren harga satu komoditas
# --------------------------------------------------------------------------
bagian("Perkembangan", f"Harga {komoditas}, {th_awal}–{th_akhir}",
       "Garis biru adalah harga tiap bulan; garis putus-putus adalah rata-rata "
       "setahun terakhir sebagai patokan harga \"normal\". Kalau garis biru "
       "jauh di atas atau di bawah garis putus-putus, harganya sedang tidak biasa.")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=satu["periode"], y=satu["rata2_12bln"], name="Rata-rata 12 bulan",
    mode="lines", line=dict(color=WARNA["redup"], width=1.6, dash="dash"),
    hovertemplate="rata-rata 12 bln Rp %{y:,.0f}<extra></extra>"))
fig.add_trace(go.Scatter(
    x=satu["periode"], y=satu["harga"], name="Harga bulanan",
    mode="lines", line=dict(color=WARNA["seri1"], width=2.5),
    fill="tonexty", fillcolor="rgba(42,120,214,0.08)",
    hovertemplate="harga Rp %{y:,.0f}<extra></extra>"))
fig.update_yaxes(tickprefix="Rp ", separatethousands=True)
st.plotly_chart(gaya(fig, 340), use_container_width=True)

awal_h, akhir_h = satu["harga"].iloc[0], satu["harga"].iloc[-1]
ubah = (akhir_h / awal_h - 1) * 100
bacaan(
    f"Harga {komoditas} bergerak dari <b>{rupiah(awal_h)}</b> pada "
    f"{nama_bulan(satu['periode'].iloc[0])} menjadi <b>{rupiah(akhir_h)}</b> "
    f"pada {nama_bulan(satu['periode'].iloc[-1])}, "
    + (f"naik <b>{angka(ubah)}%</b>" if ubah >= 0
       else f"turun <b>{angka(abs(ubah))}%</b>")
    + f" selama {th_akhir - th_awal + 1} tahun. Harga tertinggi sepanjang "
      f"periode ini {rupiah(satu['harga'].max())}, terendah "
      f"{rupiah(satu['harga'].min())}.")

bln_tinggi = satu.loc[satu["harga"].idxmax(), "periode"]
bln_rendah = satu.loc[satu["harga"].idxmin(), "periode"]
cv = satu["harga"].std() / satu["harga"].mean() * 100
selisih_normal = baris_akhir["simpangan_pct"]
butir = [
    f"Harga tertinggi pertama kali tercapai pada <b>{nama_bulan(bln_tinggi)}</b> "
    f"dan terendah pada <b>{nama_bulan(bln_rendah)}</b>. Harga tertinggi itu "
    f"{angka((satu['harga'].max() / satu['harga'].min() - 1) * 100, 1)}% lebih "
    "mahal daripada yang terendah.",
    f"Harga bulan terakhir berada <b>{angka(abs(selisih_normal), 1)}% "
    f"{'di atas' if selisih_normal >= 0 else 'di bawah'}</b> rata-rata 12 "
    f"bulannya, berstatus <b>{baris_akhir['status']}</b>.",
    f"Naik-turun harga ({angka(cv, 1)}% dari harga rata-ratanya) tergolong "
    + ("kecil, harganya relatif stabil." if cv < 10
       else "sedang, ada naik-turun yang cukup terasa." if cv < 25
       else "besar, harganya mudah melonjak.")
]
wawasan("Temuan", butir)

# --------------------------------------------------------------------------
# 2. Peringkat gejolak
# --------------------------------------------------------------------------
bagian("Peringkat", "Komoditas mana yang paling bergejolak",
       "Diukur dari seberapa besar harga berubah tiap bulan. Makin tinggi "
       "angkanya, makin sulit ditebak harganya, dan makin perlu "
       "diawasi menjelang hari besar.")

peringkat = (sumber_pilihan.drop_duplicates("komoditas")
             .nlargest(12, "volatilitas_pct")
             .sort_values("volatilitas_pct"))
warna_peringkat = [WARNA["seri2"] if k == komoditas else WARNA["seri1"]
                   for k in peringkat["komoditas"]]

fig = go.Figure(go.Bar(
    x=peringkat["volatilitas_pct"], y=peringkat["komoditas"],
    orientation="h",
    marker=dict(color=warna_peringkat, line=dict(width=0)),
    text=[angka(v, 1) + "%" for v in peringkat["volatilitas_pct"]],
    textposition="outside", textfont=dict(color=WARNA["tinta2"], size=11),
    customdata=peringkat[["kelompok"]],
    hovertemplate="<b>%{y}</b><br>%{customdata[0]}"
                  "<br>gejolak %{x:.1f}%<extra></extra>"))
fig.update_xaxes(ticksuffix="%",
                 range=[0, peringkat["volatilitas_pct"].max() * 1.16])
st.plotly_chart(gaya_titik(fig, 400), use_container_width=True)

# Keterangan hanya ditulis kalau komoditas pilihan memang ada di grafik,
# supaya tidak menyuruh pembaca mencari batang jingga yang tidak ada.
semua_peringkat = (sumber_pilihan.drop_duplicates("komoditas")
                   .sort_values("volatilitas_pct", ascending=False)
                   .reset_index(drop=True))
if komoditas in list(peringkat["komoditas"]):
    st.caption(f"Batang jingga menandai {komoditas}, komoditas yang "
               "sedang dipilih.")
else:
    urutan_ke = semua_peringkat.index[
        semua_peringkat["komoditas"] == komoditas][0] + 1
    nilai = semua_peringkat.loc[urutan_ke - 1, "volatilitas_pct"]
    st.caption(f"{komoditas} tidak masuk dua belas besar — gejolaknya "
               f"{angka(nilai, 1)}%, peringkat ke-{urutan_ke} dari "
               f"{len(semua_peringkat)} komoditas.")

kelompok_gejolak = (sumber_pilihan.drop_duplicates("komoditas")
                    .groupby("kelompok")["volatilitas_pct"].mean()
                    .sort_values(ascending=False))
wawasan("Temuan", [
    f"Kelompok dengan harga paling bergejolak rata-rata adalah "
    f"<b>{kelompok_gejolak.index[0]}</b> ({angka(kelompok_gejolak.iloc[0], 1)}%), "
    f"yang paling tenang <b>{kelompok_gejolak.index[-1]}</b> "
    f"({angka(kelompok_gejolak.iloc[-1], 1)}%).",
    f"Komoditas yang paling mudah berubah harganya adalah <b>{semua_peringkat.loc[0, 'komoditas']}</b> "
    f"({angka(semua_peringkat.loc[0, 'volatilitas_pct'], 1)}%), sedangkan yang "
    f"paling stabil <b>{semua_peringkat.loc[len(semua_peringkat) - 1, 'komoditas']}</b> "
    f"({angka(semua_peringkat.loc[len(semua_peringkat) - 1, 'volatilitas_pct'], 1)}%). "
    "Perbedaan ini yang membuat ramalan harga sebagian komoditas jauh lebih "
    "sulit daripada yang lain.",
])

# --------------------------------------------------------------------------
# 3. Pola musiman
# --------------------------------------------------------------------------
bagian("Musiman", f"Pola bulanan {komoditas}",
       "Tiap baris satu tahun, tiap kolom satu bulan. Kalau warna merah "
       "muncul di bulan yang sama tiap tahun, artinya ada pola musiman "
       "(misalnya naik menjelang hari raya) yang bisa diantisipasi.")

musim = satu.copy()
musim["tahun"] = musim["periode"].dt.year
musim["bulan_ke"] = musim["periode"].dt.month
kisi = (musim.pivot_table(index="tahun", columns="bulan_ke",
                          values="perubahan_mom_pct", aggfunc="mean")
        .reindex(columns=range(1, 13)))

batas_m = np.nanpercentile(np.abs(kisi.values), 95) if kisi.notna().any().any() else 1.0
batas_m = max(float(batas_m), 1.0)

fig = go.Figure(go.Heatmap(
    z=kisi.values, x=BULAN_ID, y=[str(t) for t in kisi.index],
    colorscale=[[0.0, WARNA["turun"]], [0.5, WARNA["netral"]],
                [1.0, WARNA["naik"]]],
    zmid=0, zmin=-batas_m, zmax=batas_m, xgap=2, ygap=2,
    colorbar=dict(title=dict(text="% per bulan", side="right"),
                  thickness=11, outlinewidth=0, tickfont=dict(size=10),
                  ticksuffix="%"),
    hovertemplate="%{y} %{x}<br>%{z:+.2f}%<extra></extra>"))
fig.update_yaxes(type="category", dtick=1)   # tampilkan semua tahun
st.plotly_chart(gaya_titik(fig, 40 + 42 * len(kisi)), use_container_width=True)

n_sel = int(kisi.notna().sum().sum())
n_nol = int((kisi.abs() < 0.005).sum().sum())
istilah(
    "<b>Cara membaca warnanya.</b><br>"
    "• <b>Merah tua</b>: harga naik tajam pada bulan itu. "
    "<b>Merah muda atau pink</b>: naik sedikit.<br>"
    "• <b>Biru tua</b>: harga turun tajam. <b>Biru muda</b>: turun sedikit.<br>"
    "• <b>Abu-abu atau putih keabu-abuan</b>: harga hampir tidak berubah "
    "dibanding bulan sebelumnya.<br>"
    "• <b>Kotak kosong</b>: tidak ada data pada bulan itu.<br>"
    "Cara memakainya: lihat satu kolom (satu bulan) dari atas ke bawah. "
    "Kalau warnanya sering sama di kolom itu, berarti ada kebiasaan musiman. "
    "Arahkan kursor ke kotak untuk melihat angka persisnya."
    + (f"<br><b>Catatan:</b> {n_nol} dari {n_sel} kotak ({n_nol / max(n_sel, 1) * 100:.0f}%) "
       f"harganya tidak berubah sama sekali, sehingga polanya sulit terbaca. "
       "Biasanya itu tanda harga di sumber data jarang diperbarui, bukan "
       "tanda harga benar-benar tetap." if n_nol / max(n_sel, 1) >= 0.4 else ""))

rata_bulan = musim.groupby("bulan_ke")["perubahan_mom_pct"].mean()
if rata_bulan.notna().any():
    bl_naik, bl_turun = rata_bulan.idxmax(), rata_bulan.idxmin()
    bacaan(
        f"Dirata-ratakan menurut bulan, harga {komoditas} paling sering naik "
        f"pada <b>{BULAN_ID[bl_naik - 1]}</b> "
        f"(rata-rata {persen(rata_bulan.max())}) dan paling sering turun pada "
        f"<b>{BULAN_ID[bl_turun - 1]}</b> "
        f"(rata-rata {persen(rata_bulan.min())}).")

# --------------------------------------------------------------------------
# 4. Hubungan dengan inflasi resmi
# --------------------------------------------------------------------------
bagian("Pembuktian", "Apakah harga pasar sejalan dengan angka resmi BPS",
       "Tiap titik adalah satu bulan. Makin ke kanan, harga di pasar naik "
       "makin tinggi. Makin ke atas, kenaikan harga makanan menurut BPS "
       "makin tinggi. Kalau titik-titik membentuk garis menanjak, berarti "
       "harga pasar dan angka resmi BPS memang bergerak seirama.")

v = jembatan.dropna(subset=["harga_pangan_mom", "inflasi_makanan_mom"])
r = float(v["harga_pangan_mom"].corr(v["inflasi_makanan_mom"]))
# Garis kecenderungan dihitung dengan numpy agar tidak perlu paket tambahan
kemiringan, potongan = np.polyfit(v["harga_pangan_mom"],
                                  v["inflasi_makanan_mom"], 1)
garis_x = np.array([v["harga_pangan_mom"].min(), v["harga_pangan_mom"].max()])

kiri, kanan = st.columns([3, 2])

with kiri:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=garis_x, y=kemiringan * garis_x + potongan, mode="lines",
        name="Garis kecenderungan",
        line=dict(color=WARNA["seri2"], width=2, dash="dash"),
        hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=v["harga_pangan_mom"], y=v["inflasi_makanan_mom"], mode="markers",
        name="Bulan",
        marker=dict(size=10, color=WARNA["seri1"],
                    line=dict(width=1.5, color="white")),
        customdata=np.stack([v["periode"].dt.strftime("%b %Y")], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>harga pangan %{x:+.2f}%"
                      "<br>inflasi makanan %{y:+.2f}%<extra></extra>"))
    fig.add_hline(y=0, line_width=1, line_color=WARNA["garis"])
    fig.add_vline(x=0, line_width=1, line_color=WARNA["garis"])
    fig.update_xaxes(title="Perubahan harga pangan di pasar (%)", ticksuffix="%")
    fig.update_yaxes(title="Kenaikan harga makanan menurut BPS (%)", ticksuffix="%")
    st.plotly_chart(gaya_titik(fig, 380), use_container_width=True)

with kanan:
    kartu(st, "Keeratan hubungan (r)", angka(r, 3, tanda=True),
          f"dihitung dari {len(v)} bulan; makin dekat ke +1, makin seirama")
    st.markdown("")
    kartu(st, "Seberapa terjelaskan (R²)", angka(r ** 2 * 100, 1) + "%",
          "bagian naik-turunnya harga makanan versi BPS yang bisa "
          "dijelaskan oleh harga pasar")
    st.markdown("")
    kartu(st, "Pengaruh harga pasar", angka(kemiringan, 3),
          "setiap 1% kenaikan harga pangan di pasar sejalan dengan kenaikan "
          f"harga makanan versi BPS sekitar {angka(kemiringan, 2)} persen",
          kecil=True)

istilah(
    "<b>Cara membaca grafik titik di kiri.</b><br>"
    "• Setiap <b>titik biru</b> adalah satu bulan. Posisi ke kanan berarti "
    "harga pangan di pasar naik; posisi ke atas berarti harga makanan "
    "versi BPS naik.<br>"
    "• <b>Garis putus-putus jingga</b> adalah garis kecenderungan: arah umum "
    "hubungan keduanya. Makin banyak titik yang menempel ke garis itu, makin "
    "seirama kedua angka.<br>"
    "• Titik di <b>kanan atas</b> adalah bulan ketika harga pasar dan angka BPS "
    "sama-sama naik; titik di <b>kiri bawah</b> sama-sama turun. Titik yang "
    "<b>jauh dari garis</b> adalah bulan ketika keduanya tidak sepakat.<br>"
    "• Garis tegak di angka 0% memisahkan bulan harga pasar naik (kanan) dan "
    "turun (kiri), dan garis datar di 0% memisahkan kenaikan dan penurunan "
    "harga makanan versi BPS.")

bacaan(
    f"Keeratan hubungannya <b>{angka(r, 3, tanda=True)}</b>, tergolong "
    f"<b>{'kuat' if abs(r) >= 0.7 else 'sedang' if abs(r) >= 0.4 else 'lemah'}</b>. "
    f"Artinya harga pasar (data Disperindag) bergerak searah dengan angka "
    "resmi BPS untuk makanan, sehingga bisa dipakai sebagai tanda awal. "
    "Catatan penting: hubungan ini terjadi <b>pada bulan yang sama</b>, "
    "bukan mendahului. Harga pasar tidak meramal inflasi bulan depan, tetapi "
    "sudah memberi gambaran bulan ini jauh sebelum angka resmi terbit.")

# Contoh nyata untuk menjelaskan keterkaitan
sama_arah = int(((v["harga_pangan_mom"] > 0) == (v["inflasi_makanan_mom"] > 0)).sum())
istilah(
    f"<b>Cara membaca R².</b> Nilai {angka(r ** 2 * 100, 1)}% berarti sekitar "
    f"{angka(r ** 2 * 100, 0)} dari tiap 100 bagian naik-turunnya harga "
    "makanan versi BPS bisa dijelaskan oleh pergerakan harga pasar. Sisanya berasal "
    "dari hal yang tidak terpantau di data harga ini, seperti komoditas lain "
    f"dan perbedaan cara hitung. Pada {len(v)} bulan, kedua angka searah "
    f"(sama-sama naik atau sama-sama turun) di <b>{sama_arah} bulan</b>.")

# --------------------------------------------------------------------------
# 5. Tabel status
# --------------------------------------------------------------------------
bagian("Pemantauan", f"Status harga per {nama_bulan(bulan_akhir)}",
       "Status dilihat dari seberapa jauh harga sekarang dari rata-rata "
       "setahun terakhir: lebih dari 15% disebut \"waspada\", lebih dari 7% "
       "disebut \"naik\" atau \"turun\", selebihnya \"normal\".")

ringkas = terkini["status"].value_counts()
urutan = ["Waspada naik", "Naik", "Normal", "Turun", "Waspada turun"]
kols = st.columns(5)
for kol, nama in zip(kols, urutan):
    kartu(kol, nama, str(int(ringkas.get(nama, 0))), "komoditas")

with st.expander("Lihat daftar komoditas yang di luar kebiasaan"):
    luar = (terkini[terkini["status"] != "Normal"]
            .sort_values("simpangan_pct", ascending=False)
            [["komoditas", "kelompok", "harga", "rata2_12bln",
              "simpangan_pct", "perubahan_yoy_pct", "status"]]
            .rename(columns={"komoditas": "Komoditas", "kelompok": "Kelompok",
                             "harga": "Harga (Rp)",
                             "rata2_12bln": "Rata-rata 12 bulan (Rp)",
                             "simpangan_pct": "Simpangan (%)",
                             "perubahan_yoy_pct": "Perubahan setahun (%)",
                             "status": "Status"}))
    st.dataframe(luar, use_container_width=True, hide_index=True)
    st.download_button(
        "Unduh daftar ini (CSV)",
        luar.to_csv(index=False).encode("utf-8"),
        file_name=f"status_harga_bojonegoro_{bulan_akhir:%Y_%m}.csv",
        mime="text/csv")

sumber(
    "Sumber: Sistem Informasi Ketersediaan dan Perkembangan Harga Bahan "
    "Pokok (SISKAPERBAPO), Dinas Perindustrian dan Perdagangan Provinsi "
    "Jawa Timur, diolah. Angka inflasi pembanding berasal dari Berita Resmi "
    "Statistik BPS Kabupaten Bojonegoro.")
