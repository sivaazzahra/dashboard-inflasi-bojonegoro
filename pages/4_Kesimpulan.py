"""
HALAMAN 4 — KESIMPULAN
======================

Dari data menjadi keputusan. Halaman ini merangkum temuan, memperlihatkan
gerak inflasi yang bisa diputar ulang, lalu menerjemahkannya menjadi bahan
pertimbangan kebijakan.

Kerangkanya adalah empat tingkat analitik dalam kecerdasan bisnis:
deskriptif (apa yang terjadi), diagnostik (mengapa), prediktif (apa yang
akan terjadi), dan preskriptif (apa yang sebaiknya dilakukan).
"""

import plotly.graph_objects as go
import streamlit as st

from alat import (BULAN_ID, CATATAN_SASARAN, SASARAN_ATAS, SASARAN_BAWAH, WARNA,
                  angka, atur_halaman, bacaan, bagian, catatan_kaki, gaya,
                  gaya_titik, info, istilah, kartu, kepala, muat_harga,
                  muat_inflasi, muat_jembatan, nama_bulan, periksa_data, persen,
                  pil, status_sasaran, sumber, tambah_sasaran, wawasan)

atur_halaman("Kesimpulan")

if not periksa_data():
    st.stop()

inflasi = muat_inflasi()
harga = muat_harga()
jembatan = muat_jembatan()

umum = inflasi[inflasi["adalah_umum"]].sort_values("periode").reset_index(drop=True)
rinci = inflasi[~inflasi["adalah_umum"]]
terakhir = umum.iloc[-1]
yoy = float(terakhir["inflasi_yoy"])
pangan_terakhir = harga["periode"].max()
status_teks, status_warna = status_sasaran(yoy)

kepala("Kesimpulan dan Rekomendasi",
       "Dari data menjadi keputusan: apa temuan utamanya, bagaimana inflasi "
       "bergerak, dan apa yang layak dilakukan berikutnya.",
       f"Inflasi sampai {nama_bulan(terakhir['periode'])} · "
       f"harga pangan sampai {nama_bulan(pangan_terakhir)}",
       latar="latar_beranda")


def label_pendek(t) -> str:
    return f"{BULAN_ID[t.month - 1][:3]} {t.year}"


GERAK = dict(frame=dict(duration=170, redraw=True),
             transition=dict(duration=0), fromcurrent=True, mode="immediate")
BERHENTI = dict(frame=dict(duration=0, redraw=False),
                transition=dict(duration=0), mode="immediate")


def kendali(fig, label_langkah: list, nama_bingkai: list) -> None:
    """Tombol putar-jeda dan penggeser bulan untuk grafik bergerak."""
    fig.update_layout(
        updatemenus=[dict(
            type="buttons", direction="left", showactive=False,
            x=0.0, y=-0.2, xanchor="left", yanchor="top", pad=dict(t=0, r=8),
            buttons=[dict(label="▶ Putar", method="animate", args=[None, GERAK]),
                     dict(label="⏸ Jeda", method="animate",
                          args=[[None], BERHENTI])])],
        sliders=[dict(
            active=len(nama_bingkai) - 1, x=0.2, y=-0.2, len=0.8,
            xanchor="left", yanchor="top", pad=dict(t=0, b=0),
            currentvalue=dict(visible=False),
            steps=[dict(method="animate", label=lbl,
                        args=[[nama], dict(mode="immediate",
                                           frame=dict(duration=0, redraw=True),
                                           transition=dict(duration=0))])
                   for lbl, nama in zip(label_langkah, nama_bingkai)])])


# --------------------------------------------------------------------------
# 1. Gerak inflasi
# --------------------------------------------------------------------------
bagian("Bergerak", "Perjalanan inflasi, bisa diputar ulang"
       + info("Tekan Putar untuk melihat inflasi setahun bergerak bulan demi "
              "bulan. Geser penggeser untuk berhenti di bulan tertentu."),
       "Garis menunjukkan kenaikan harga setahun terakhir. Pita hijau adalah "
       "sasaran pemerintah. Lihat kapan garis keluar dari pita, dan kapan "
       "kembali.")

x = list(umum["periode"])
y = list(umum["inflasi_yoy"])
fig = go.Figure(
    data=[go.Scatter(x=x, y=y, mode="lines", name="Inflasi setahun",
                     line=dict(color=WARNA["seri1"], width=3),
                     hovertemplate="%{y:+.2f}%<extra></extra>"),
          go.Scatter(x=[x[-1]], y=[y[-1]], mode="markers+text",
                     marker=dict(size=11, color=WARNA["naik"],
                                 line=dict(width=2, color="white")),
                     text=[f"{y[-1]:+.2f}%".replace(".", ",")],
                     textposition="top center", showlegend=False,
                     hoverinfo="skip")],
    frames=[go.Frame(
        name=str(k),
        data=[go.Scatter(x=x[:k + 1], y=y[:k + 1]),
              go.Scatter(x=[x[k]], y=[y[k]],
                         text=[f"{y[k]:+.2f}%".replace(".", ",")])],
        traces=[0, 1]) for k in range(len(x))])
tambah_sasaran(fig)
fig.update_yaxes(ticksuffix="%", range=[min(min(y), 0) - 0.5,
                                        max(max(y), SASARAN_ATAS) + 1.0])
fig.update_xaxes(range=[x[0], x[-1]])
fig.update_layout(showlegend=False)
kendali(fig, [label_pendek(t) for t in x], [str(k) for k in range(len(x))])
fig = gaya(fig, 460)
fig.update_layout(margin=dict(l=8, r=12, t=16, b=90))
st.plotly_chart(fig, use_container_width=True)
catatan_kaki(CATATAN_SASARAN)

# --------------------------------------------------------------------------
# 2. Temuan utama
# --------------------------------------------------------------------------
sebelumnya = umum.iloc[-2]
arah = "naik" if yoy > sebelumnya["inflasi_yoy"] else "turun"
tertinggi_yoy = umum.loc[umum["inflasi_yoy"].idxmax()]
terendah_yoy = umum.loc[umum["inflasi_yoy"].idxmin()]
bulan_deflasi = int((umum["inflasi_mom"] < 0).sum())

rinci_akhir = rinci[rinci["periode"] == terakhir["periode"]]
paling_tinggi = rinci_akhir.sort_values("inflasi_yoy", ascending=False).iloc[0]
penyumbang = rinci_akhir.sort_values("andil_yoy", ascending=False).iloc[0]

pangan_kini = harga[(harga["periode"] == pangan_terakhir) & (harga["pangan"])]
naik_waspada = pangan_kini[pangan_kini["status"] == "Waspada naik"]
sah = jembatan.dropna(subset=["harga_pangan_mom", "inflasi_makanan_mom"])
r = float(sah["harga_pangan_mom"].corr(sah["inflasi_makanan_mom"]))

if paling_tinggi["kelompok"] == penyumbang["kelompok"]:
    kalimat_kelompok = "sekaligus yang paling terasa dampaknya."
else:
    kalimat_kelompok = (
        f"tetapi yang paling terasa dampaknya justru "
        f"<b>{penyumbang['kelompok_pendek']}</b>, karena porsinya dalam "
        "belanja rumah tangga jauh lebih besar. Harga yang naik paling cepat "
        "belum tentu yang paling terasa di dompet.")
if len(naik_waspada):
    terjauh = naik_waspada.sort_values("simpangan_pct").iloc[-1]["komoditas"]
    kalimat_waspada = f", yang paling jauh di atas biasanya: <b>{terjauh}</b>."
else:
    kalimat_waspada = "."

sejak_2025 = umum[umum["periode"] >= "2025-01-01"]
dalam = int(sejak_2025["inflasi_yoy"].between(SASARAN_BAWAH, SASARAN_ATAS).sum())

butir = [
    f"Kenaikan harga setahun terakhir <b>{arah}</b> dari "
    f"{persen(sebelumnya['inflasi_yoy'])} ({nama_bulan(sebelumnya['periode'])}) "
    f"menjadi <b>{persen(yoy)}</b>, posisi <b>{status_teks.lower()}</b>. "
    f"Tertinggi sepanjang data {persen(tertinggi_yoy['inflasi_yoy'])} pada "
    f"{nama_bulan(tertinggi_yoy['periode'])}, terendah "
    f"{persen(terendah_yoy['inflasi_yoy'])} pada "
    f"{nama_bulan(terendah_yoy['periode'])}.",
    f"Sejak Januari 2025, kenaikan harga setahun berada dalam rentang sasaran "
    f"pada <b>{dalam} dari {len(sejak_2025)} bulan</b>.",
    f"Dari {len(umum)} bulan yang tercatat, <b>{bulan_deflasi} bulan</b> "
    "mengalami penurunan harga (deflasi). Harga di Bojonegoro tidak naik "
    "terus-menerus, melainkan naik-turun.",
    f"Kelompok yang harganya naik paling cepat adalah "
    f"<b>{paling_tinggi['kelompok_pendek']}</b> "
    f"({persen(paling_tinggi['inflasi_yoy'])}), " + kalimat_kelompok,
    f"Di pasar, <b>{len(naik_waspada)} dari {len(pangan_kini)}</b> komoditas "
    f"pangan harganya <i>perlu diwaspadai karena naik</i> pada "
    f"{nama_bulan(pangan_terakhir)}" + kalimat_waspada,
    f"Harga di pasar dan angka resmi BPS untuk makanan bergerak searah "
    f"(keeratan hubungan <b>{angka(r, 2, tanda=True)}</b>; makin dekat ke 1 "
    "makin erat), sehingga harga pasar harian bisa jadi tanda awal sebelum "
    "angka resmi BPS terbit.",
]
bagian("Temuan", "Apa yang bisa dibaca dari data ini",
       "Semua kalimat di bawah dihitung dari data terbaru, jadi ikut berubah "
       "setiap kali data diperbarui.")
wawasan("Temuan utama", butir)

# --------------------------------------------------------------------------
# 3. Sumbangan tiap kelompok, bergerak
# --------------------------------------------------------------------------
bagian("Pendorong", "Siapa yang mendorong harga, bulan demi bulan"
       + info("Setiap batang adalah sumbangan satu kelompok pengeluaran "
              "terhadap kenaikan harga setahun. Merah mendorong naik, biru "
              "menarik turun."),
       "Tekan Putar untuk melihat kelompok mana yang paling menyumbang pada "
       "tiap bulan. Perhatikan betapa seringnya makanan berada di puncak.")

bulan_semua = sorted(rinci["periode"].unique())
urutan_kel = (rinci.groupby("kelompok_pendek")["andil_yoy"].mean()
              .sort_values().index.tolist())
batas_a = float(max(abs(rinci["andil_yoy"].min()), abs(rinci["andil_yoy"].max())))


def batang(bulan):
    d = (rinci[rinci["periode"] == bulan].set_index("kelompok_pendek")
         .reindex(urutan_kel))
    return go.Bar(
        x=d["andil_yoy"], y=urutan_kel, orientation="h",
        marker=dict(color=[WARNA["naik"] if v >= 0 else WARNA["turun"]
                           for v in d["andil_yoy"]], line=dict(width=0)),
        text=[f"{v:+.2f}".replace(".", ",") for v in d["andil_yoy"]],
        textposition="outside", textfont=dict(size=11, color=WARNA["tinta2"]),
        hovertemplate="<b>%{y}</b><br>sumbangan %{x:+.2f} poin<extra></extra>")


fig = go.Figure(
    data=[batang(bulan_semua[-1])],
    frames=[go.Frame(name=str(k), data=[batang(b)],
                     layout=go.Layout(title=dict(
                         text=f"Sumbangan tiap kelompok · {label_pendek(b)}",
                         font=dict(size=13, color=WARNA["tinta2"]), x=0.01)))
            for k, b in enumerate(bulan_semua)])
fig.add_vline(x=0, line_width=1, line_color=WARNA["redup"])
fig.update_xaxes(ticksuffix=" poin", range=[-batas_a - 0.4, batas_a + 0.6])
fig.update_layout(title=dict(
    text=f"Sumbangan tiap kelompok · {label_pendek(bulan_semua[-1])}",
    font=dict(size=13, color=WARNA["tinta2"]), x=0.01), showlegend=False)
kendali(fig, [label_pendek(b) for b in bulan_semua],
        [str(k) for k in range(len(bulan_semua))])
fig = gaya_titik(fig, 520)
fig.update_layout(margin=dict(l=8, r=16, t=44, b=90))
st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# 4. Analisis kebijakan
# --------------------------------------------------------------------------
STAPEL = ["Beras Medium", "Beras Premium", "Telur Ayam Ras", "Daging Ayam Ras",
          "Cabe Rawit Merah", "Cabe Merah Keriting", "Bawang Merah",
          "Bawang Putih Sinco/Honan", "Gula Kristal Putih",
          "Minyak Goreng Curah", "Daging Sapi Paha Belakang", "Tomat Merah"]

# Komoditas yang harganya tidak berubah berbulan-bulan tidak dipakai: pola
# musimannya tidak bisa dipercaya.
mandek = {k for k, g in harga.sort_values("periode").groupby("komoditas")
          if g["harga"].tail(6).nunique() == 1}

bulan_terakhir_harga = pangan_terakhir.month
tiga_depan = [((bulan_terakhir_harga + i - 1) % 12) + 1 for i in (1, 2, 3)]
stapel = harga[harga["komoditas"].isin(STAPEL)
               & ~harga["komoditas"].isin(mandek)].copy()
stapel["bulan_ke"] = stapel["periode"].dt.month
musim = (stapel.groupby(["komoditas", "bulan_ke"])["perubahan_mom_pct"].mean()
         .unstack().reindex(columns=tiga_depan))
naik_musim = musim[(musim >= 2.0).any(axis=1)]

bagian("Kebijakan", "Apa artinya, dan apa yang layak dilakukan?"
       + info("Ini bahan diskusi yang dihitung dari data, bukan keputusan "
              "resmi. Keputusan tetap memerlukan informasi lapangan."),
       "Temuan di atas diterjemahkan menjadi langkah, memakai kerangka 4K "
       "yang lazim dipakai tim pengendalian inflasi daerah: keterjangkauan "
       "harga, ketersediaan pasokan, kelancaran distribusi, dan komunikasi "
       "yang efektif.")

top_stabil = (harga[harga["pangan"] & ~harga["komoditas"].isin(mandek)]
              .drop_duplicates("komoditas").nlargest(1, "volatilitas_pct")
              .iloc[0])
nama_bulan_depan = ", ".join(BULAN_ID[m - 1] for m in tiga_depan)
daftar_musim = "; ".join(
    f"<b>{k}</b> ({BULAN_ID[int(musim.loc[k].idxmax()) - 1]} "
    f"{angka(musim.loc[k].max(), 1, tanda=True)}%)"
    for k in naik_musim.index) or "tidak ada yang menonjol"
daftar_waspada = ", ".join(
    f"<b>{k}</b> ({angka(v, 0, tanda=True)}% dari kebiasaan)"
    for k, v in naik_waspada.sort_values("simpangan_pct", ascending=False)
    .head(3).set_index("komoditas")["simpangan_pct"].items()) or "tidak ada"

st.markdown(
    f"""
<div class="wawasan"><div class="judul">Empat langkah (4K)</div>
<ul>
<li><b>1. Keterjangkauan harga.</b> Data: {len(naik_waspada)} komoditas pangan
berstatus waspada naik, terutama {daftar_waspada}. Pendorong terbesar inflasi
adalah <b>{penyumbang['kelompok_pendek']}</b>. Langkah yang bisa dipertimbangkan:
pasar murah atau operasi pasar untuk komoditas yang berstatus waspada naik,
dengan prioritas komoditas yang porsinya besar dalam belanja rumah tangga.</li>
<li><b>2. Ketersediaan pasokan.</b> Data: untuk tiga bulan ke depan
({nama_bulan_depan}), komoditas yang biasanya naik dari pola tahun-tahun
sebelumnya adalah {daftar_musim}. Langkah: periksa stok dan jadwal panen
sebelum bulan-bulan itu, dan jalin pasokan dari daerah penghasil lain
sebagai cadangan.</li>
<li><b>3. Kelancaran distribusi.</b> Data: komoditas pangan yang paling
naik-turun adalah <b>{top_stabil['komoditas']}</b> (rata-rata berubah
{angka(top_stabil['volatilitas_pct'], 1)}% per bulan), tanda rantai pasokannya
rentan gangguan. Langkah: pantau jalur distribusi dan penyimpanan komoditas
yang gejolaknya tinggi.</li>
<li><b>4. Komunikasi efektif.</b> Data: kenaikan harga setahun berada di posisi
<b>{status_teks.lower()}</b> ({persen(yoy)}). Langkah: sampaikan perkiraan
harga sebagai rentang, bukan angka tunggal; hindari pesan yang memicu belanja
panik; rilis kabar harga secara berkala agar pedagang dan pembeli memegang
informasi yang sama.</li>
</ul></div>""", unsafe_allow_html=True)

if len(naik_musim):
    tabel = musim.copy()
    tabel.columns = [BULAN_ID[int(c) - 1] for c in tabel.columns]
    tabel = tabel.map(lambda v: "—" if v != v else f"{v:+.1f}%".replace(".", ","))
    tabel.index.name = "Komoditas"
    with st.expander("Lihat kalender musiman: rata-rata perubahan harga "
                     "per bulan"):
        st.dataframe(tabel, use_container_width=True)
        st.caption("Rata-rata perubahan harga bulanan pada bulan yang sama "
                   "di tahun-tahun sebelumnya. Hanya sebagai kebiasaan, "
                   "bukan ramalan. Komoditas yang harganya tidak berubah "
                   "berbulan-bulan tidak diikutkan.")

# --------------------------------------------------------------------------
# 5. Kecerdasan bisnis
# --------------------------------------------------------------------------
bagian("Kecerdasan bisnis", "Dari data mentah sampai keputusan",
       "Dashboard ini disusun mengikuti empat tingkat analitik dalam "
       "kecerdasan bisnis. Setiap halaman menjawab satu tingkat, dan "
       "semuanya bertumpu pada data yang sama.")

a, b = st.columns(2)
kartu(a, "Deskriptif · halaman Inflasi", "Apa yang terjadi?",
      f"Inflasi setahun {persen(yoy)}. Ringkasan angka (KPI), tren, dan "
      "pembagian menurut kelompok pengeluaran.", kecil=True)
kartu(b, "Diagnostik · halaman Harga Pangan", "Mengapa terjadi?",
      f"Makanan menyumbang sekitar "
      f"{penyumbang['andil_yoy'] / yoy * 100:.0f}% dari inflasi. Harga pasar "
      f"dan angka resmi berkeratan {angka(r, 2, tanda=True)}.", kecil=True)
st.markdown("")
c, d = st.columns(2)
kartu(c, "Prediktif · halaman Peramalan", "Apa yang akan terjadi?",
      "Perkiraan harga beberapa bulan ke depan, diuji pada data yang "
      "disembunyikan dan dibandingkan dengan cara paling sederhana.",
      kecil=True)
kartu(d, "Preskriptif · halaman ini", "Apa yang sebaiknya dilakukan?",
      "Ambang waspada, skenario, dan langkah 4K yang dihitung dari data.",
      kecil=True)

istilah(
    "<b>Alur datanya.</b> Dua sumber mentah (inflasi BPS dan harga "
    "SISKAPERBAPO) dibersihkan dan digabung melalui proses ETL "
    "(<i>extract, transform, load</i>) menjadi tiga tabel siap pakai, lalu "
    "disajikan sebagai dashboard interaktif. Rinciannya ada di halaman "
    "Metode.")

# --------------------------------------------------------------------------
# 6. Keterbatasan
# --------------------------------------------------------------------------
bagian("Catatan", "Hal yang perlu diingat sebelum memakai kesimpulan ini")
n_mandek = len(mandek)
st.markdown(
    f"""
- **Sasaran inflasi bersifat nasional.** Dashboard memakainya sebagai
  pembanding bagi Bojonegoro, bukan sebagai target resmi daerah.
- **Data inflasi baru {len(umum)} bulan.** Cukup untuk melihat pola, belum
  cukup untuk kesimpulan jangka panjang.
- **{n_mandek} dari {harga['komoditas'].nunique()} komoditas** di data harga
  nilainya tidak berubah selama enam bulan terakhir atau lebih. Kemungkinan
  besar datanya tidak diperbarui di sumber, jadi komoditas itu dikeluarkan
  dari ramalan dan kalender musiman.
- **Hubungan harga pasar dengan inflasi bersifat bersamaan waktu**, bukan
  mendahului. Harga pasar membantu melihat keadaan bulan berjalan lebih
  cepat, bukan meramal bulan depan.
- **Langkah kebijakan di atas adalah bahan diskusi.** Keputusan memerlukan
  informasi lapangan yang tidak ada di data ini.
""")

sumber(
    "Sumber: Berita Resmi Statistik BPS Kabupaten Bojonegoro; SISKAPERBAPO "
    "Dinas Perindustrian dan Perdagangan Provinsi Jawa Timur; Peraturan "
    "Menteri Keuangan No. 31 Tahun 2024 tentang Sasaran Inflasi 2025–2027. "
    "Kerangka 4K: strategi pengendalian inflasi oleh Tim Pengendalian "
    "Inflasi Pusat dan Daerah.")
