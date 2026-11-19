"""
HALAMAN 1 — INFLASI
===================

Menjawab tiga pertanyaan:
  1. Berapa inflasi Kabupaten Bojonegoro dan bagaimana perkembangannya?
  2. Kelompok pengeluaran mana yang paling menyumbang inflasi?
  3. Kapan tiap kelompok bergejolak?
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from alat import (WARNA, angka, atur_halaman, bacaan, bagian, gaya,
                  gaya_titik, kartu, kepala, muat_inflasi, navigasi, nama_bulan,
                  periksa_data, persen, sumber, wawasan, istilah)

atur_halaman("Inflasi")

if not periksa_data():
    st.stop()

inflasi = muat_inflasi()
umum = inflasi[inflasi["adalah_umum"]].sort_values("periode").reset_index(drop=True)
rinci = inflasi[~inflasi["adalah_umum"]]

# --------------------------------------------------------------------------
# Penyaring
# --------------------------------------------------------------------------
daftar_bulan = list(umum["periode"])
label_bulan = [nama_bulan(t) for t in daftar_bulan]

with st.sidebar:
    st.markdown("### Penyaring")
    awal, akhir = st.select_slider(
        "Rentang periode", options=label_bulan,
        value=(label_bulan[0], label_bulan[-1]))
    bulan_sorot = st.selectbox(
        "Bulan yang disorot", options=label_bulan[::-1], index=0,
        help="Dipakai pada kartu angka dan grafik andil kelompok.")

i_awal, i_akhir = label_bulan.index(awal), label_bulan.index(akhir)
t_awal, t_akhir = daftar_bulan[i_awal], daftar_bulan[i_akhir]
t_sorot = daftar_bulan[label_bulan.index(bulan_sorot)]

umum_f = umum[(umum.periode >= t_awal) & (umum.periode <= t_akhir)]
rinci_f = rinci[(rinci.periode >= t_awal) & (rinci.periode <= t_akhir)]

kepala("Inflasi Kabupaten Bojonegoro",
       "Seberapa cepat harga naik, dan dari kelompok pengeluaran mana "
       "kenaikan itu berasal.",
       f"Disorot: {nama_bulan(t_sorot)} · rentang grafik {awal} – {akhir}",
       latar="latar_inflasi")
navigasi()

# --------------------------------------------------------------------------
# Ringkasan angka
# --------------------------------------------------------------------------
baris = umum[umum["periode"] == t_sorot].iloc[0]
andil_sorot = (rinci[rinci["periode"] == t_sorot]
               .sort_values("andil_yoy", ascending=False))
penyumbang = andil_sorot.iloc[0]

k1, k2, k3, k4 = st.columns(4)
kartu(k1, "Inflasi bulanan (m-to-m)", persen(baris["inflasi_mom"]),
      nama_bulan(t_sorot))
kartu(k2, "Inflasi tahunan (y-on-y)", persen(baris["inflasi_yoy"]),
      "dibanding bulan yang sama tahun lalu")
kartu(k3, "Tahun berjalan (y-to-d)", persen(baris["inflasi_ytd"]),
      "dibanding Desember tahun lalu")
kartu(k4, "Penyumbang terbesar", penyumbang["kelompok_pendek"],
      f"menyumbang {angka(penyumbang['andil_yoy'])} dari "
      f"{angka(baris['inflasi_yoy'])} poin", kecil=True)

# --------------------------------------------------------------------------
# 1. Perkembangan inflasi umum
# --------------------------------------------------------------------------
bagian("Perkembangan", "Inflasi umum dari waktu ke waktu",
       "Dua sudut pandang atas angka yang sama. Grafik kiri menunjukkan "
       "gejolak bulanan; grafik kanan menunjukkan arah jangka panjang.")

kiri, kanan = st.columns(2)

with kiri:
    st.caption("Inflasi bulanan (m-to-m) — merah berarti harga naik, "
               "biru berarti harga turun")
    # Batang dipakai karena tiap bulan berdiri sendiri, bukan nilai yang
    # mengalir. Warnanya dua kutub karena nilainya bisa positif dan negatif.
    fig = go.Figure(go.Bar(
        x=umum_f["periode"], y=umum_f["inflasi_mom"],
        marker=dict(color=[WARNA["naik"] if v >= 0 else WARNA["turun"]
                           for v in umum_f["inflasi_mom"]],
                    line=dict(width=0)),
        hovertemplate="m-to-m %{y:+.2f}%<extra></extra>"))
    fig.add_hline(y=0, line_width=1, line_color=WARNA["redup"])
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(gaya(fig, 310), use_container_width=True)

with kanan:
    st.caption("Inflasi tahunan (y-on-y) — arah jangka panjang")
    # Garis dipakai karena inflasi tahunan bergerak perlahan dan yang
    # dibaca adalah arahnya, bukan nilai tiap bulan.
    fig = go.Figure(go.Scatter(
        x=umum_f["periode"], y=umum_f["inflasi_yoy"],
        mode="lines", line=dict(color=WARNA["seri1"], width=2.5),
        fill="tozeroy", fillcolor="rgba(42,120,214,0.10)",
        hovertemplate="y-on-y %{y:.2f}%<extra></extra>"))
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(gaya(fig, 310), use_container_width=True)

tertinggi = umum_f.loc[umum_f["inflasi_mom"].idxmax()]
terendah = umum_f.loc[umum_f["inflasi_mom"].idxmin()]
bacaan(
    f"Sepanjang {awal} sampai {akhir}, kenaikan harga bulanan tertinggi "
    f"terjadi pada <b>{nama_bulan(tertinggi['periode'])}</b> "
    f"({persen(tertinggi['inflasi_mom'])}) dan penurunan terdalam pada "
    f"<b>{nama_bulan(terendah['periode'])}</b> "
    f"({persen(terendah['inflasi_mom'])}). Rata-rata inflasi tahunannya "
    f"<b>{angka(umum_f['inflasi_yoy'].mean())}%</b>.")

n_bulan = len(umum_f)
n_naik = int((umum_f["inflasi_mom"] > 0).sum())
n_negatif_yoy = int((umum_f["inflasi_yoy"] < 0).sum())
selisih_yoy = umum_f["inflasi_yoy"].iloc[-1] - umum_f["inflasi_yoy"].iloc[0]
butir = [
    f"Harga naik pada <b>{n_naik} dari {n_bulan} bulan</b> "
    f"({n_naik / n_bulan * 100:.0f}%); sisanya turun atau datar. Kenaikan "
    "harga di Bojonegoro cenderung bergelombang, bukan menanjak terus.",
    f"Inflasi tahunan bergerak dari {persen(umum_f['inflasi_yoy'].iloc[0])} "
    f"menjadi {persen(umum_f['inflasi_yoy'].iloc[-1])} "
    f"({angka(selisih_yoy, 2, tanda=True)} poin) antara {awal} dan {akhir}.",
]
if n_negatif_yoy:
    butir.append(
        f"Inflasi tahunan sempat negatif (deflasi tahunan) pada "
        f"<b>{n_negatif_yoy} bulan</b>, artinya harga secara umum lebih "
        "murah dibanding bulan yang sama setahun sebelumnya.")
butir.append(
    "Perbedaan dua grafik itu penting: inflasi bulanan menangkap kejutan "
    "sesaat (panen, hari raya, perubahan tarif), sedangkan inflasi tahunan "
    "menunjukkan tekanan harga yang benar-benar menumpuk.")
wawasan("Temuan", butir)

# --------------------------------------------------------------------------
# 2. Andil kelompok pengeluaran
# --------------------------------------------------------------------------
bagian("Pembagian", f"Inflasi {nama_bulan(t_sorot)} datang dari mana",
       "Andil menunjukkan berapa poin dari inflasi tahunan yang berasal "
       "dari tiap kelompok. Jumlah seluruh andil sama dengan inflasi umum, "
       "sehingga grafik ini membagi habis angka inflasi ke sumbernya.")

# Perkiraan bobot: andil = bobot x inflasi kelompok, jadi bobot kira-kira
# andil dibagi inflasi kelompok. Hanya dihitung bila inflasinya tidak nol.
andil_sorot = andil_sorot.assign(
    bobot=lambda d: d["andil_yoy"] / d["inflasi_yoy"].where(
        d["inflasi_yoy"].abs() > 0.2) * 100)
penyumbang = andil_sorot.iloc[0]          # ulang, kini beserta kolom bobot
istilah(
    "<b>Cara membacanya.</b> Setiap kelompok pengeluaran punya <b>bobot</b> "
    "(seberapa besar porsinya dalam belanja rumah tangga) dan <b>laju "
    "inflasi</b> (seberapa cepat harganya naik). Sumbangannya terhadap "
    "inflasi umum, yang disebut <b>andil</b>, adalah hasil kali keduanya: "
    "<b>andil = bobot × inflasi kelompok</b>. Jadi sebuah kelompok bisa "
    "menyumbang besar karena harganya naik cepat, karena porsinya dalam "
    "belanja besar, atau keduanya. Batang merah menambah inflasi, batang "
    "biru menariknya turun.")

andil = (andil_sorot.sort_values("andil_yoy")
         .assign(warna=lambda d: [WARNA["naik"] if v >= 0 else WARNA["turun"]
                                  for v in d["andil_yoy"]]))

fig = go.Figure(go.Bar(
    x=andil["andil_yoy"], y=andil["kelompok_pendek"], orientation="h",
    marker=dict(color=andil["warna"], line=dict(width=0)),
    text=[angka(v) for v in andil["andil_yoy"]],
    textposition="outside",
    textfont=dict(color=WARNA["tinta2"], size=11),
    customdata=andil[["inflasi_yoy"]],
    hovertemplate="<b>%{y}</b><br>andil %{x:+.2f} poin"
                  "<br>inflasi kelompok %{customdata[0]:.2f}%<extra></extra>"))
fig.add_vline(x=0, line_width=1, line_color=WARNA["redup"])
fig.update_xaxes(ticksuffix=" poin",
                 range=[andil["andil_yoy"].min() - 0.3,
                        andil["andil_yoy"].max() + 0.4])
st.plotly_chart(gaya_titik(fig, 420), use_container_width=True)

# Pembanding laju dan sumbangan, supaya terlihat bahwa keduanya berbeda
kembar = make_subplots(rows=1, cols=2, shared_yaxes=True,
                       horizontal_spacing=0.04,
                       subplot_titles=("Seberapa cepat harganya naik",
                                       "Seberapa besar sumbangannya"))
kembar.add_trace(go.Bar(
    x=andil["inflasi_yoy"], y=andil["kelompok_pendek"], orientation="h",
    marker=dict(color=WARNA["seri2"], line=dict(width=0)),
    text=[angka(v) + "%" for v in andil["inflasi_yoy"]],
    textposition="outside", textfont=dict(color=WARNA["tinta2"], size=10),
    hovertemplate="<b>%{y}</b><br>inflasi kelompok %{x:+.2f}%<extra></extra>"),
    row=1, col=1)
kembar.add_trace(go.Bar(
    x=andil["andil_yoy"], y=andil["kelompok_pendek"], orientation="h",
    marker=dict(color=WARNA["seri1"], line=dict(width=0)),
    text=[angka(v) for v in andil["andil_yoy"]],
    textposition="outside", textfont=dict(color=WARNA["tinta2"], size=10),
    hovertemplate="<b>%{y}</b><br>andil %{x:+.2f} poin<extra></extra>"),
    row=1, col=2)
kembar.update_xaxes(ticksuffix="%", row=1, col=1,
                    range=[min(0, andil["inflasi_yoy"].min()) - 3,
                           andil["inflasi_yoy"].max() * 1.25 + 1])
kembar.update_xaxes(ticksuffix=" poin", row=1, col=2,
                    range=[min(0, andil["andil_yoy"].min()) - 0.3,
                           andil["andil_yoy"].max() * 1.3 + 0.2])
kembar.update_annotations(font=dict(size=12, color=WARNA["tinta2"]))
kembar.update_layout(showlegend=False)
bagian("Laju dan bobot", "Kenaikan tercepat belum tentu penyumbang terbesar",
       "Kiri: seberapa cepat harga tiap kelompok naik. Kanan: berapa poin "
       "yang akhirnya disumbangkan ke inflasi umum. Bila urutannya berbeda, "
       "selisihnya berasal dari bobot belanja.")
kembar = gaya_titik(kembar, 460)
kembar.update_layout(margin=dict(l=12, r=16, t=44, b=10))   # ruang untuk judul panel
st.plotly_chart(kembar, use_container_width=True)

tercepat = andil_sorot.sort_values("inflasi_yoy", ascending=False).iloc[0]
if tercepat["kelompok"] == penyumbang["kelompok"]:
    bacaan(
        f"Bulan ini <b>{penyumbang['kelompok_pendek']}</b> unggul di dua "
        f"sisi: inflasinya paling tinggi ({persen(tercepat['inflasi_yoy'])}) "
        f"dan sumbangannya paling besar ({angka(penyumbang['andil_yoy'])} poin).")
else:
    b1 = tercepat["bobot"]
    b2 = penyumbang["bobot"]
    teks_b1 = f" (bobot kira-kira {b1:.0f}%)" if b1 == b1 else ""
    teks_b2 = f" (bobot kira-kira {b2:.0f}%)" if b2 == b2 else ""
    bacaan(
        f"<b>{tercepat['kelompok_pendek']}</b> mencatat inflasi tertinggi, "
        f"{persen(tercepat['inflasi_yoy'])}, tetapi hanya menyumbang "
        f"<b>{angka(tercepat['andil_yoy'])} poin</b>{teks_b1}. Sebaliknya "
        f"<b>{penyumbang['kelompok_pendek']}</b> inflasinya "
        f"{persen(penyumbang['inflasi_yoy'])} namun menyumbang "
        f"<b>{angka(penyumbang['andil_yoy'])} poin</b>{teks_b2}. Itulah sebabnya "
        "kenaikan harga di kelompok yang porsinya besar dalam belanja, "
        "terutama makanan, paling terasa pada inflasi umum.")

tiga = andil_sorot.head(3)
bacaan(
    "Tiga kelompok terbesar — <b>"
    + "</b>, <b>".join(tiga["kelompok_pendek"]) + "</b> — menyumbang "
    f"<b>{angka(tiga['andil_yoy'].sum())} poin</b> dari total "
    f"{angka(baris['inflasi_yoy'])} poin inflasi tahunan, atau sekitar "
    f"<b>{tiga['andil_yoy'].sum() / baris['inflasi_yoy'] * 100:.0f}%</b> "
    "dari seluruh kenaikan harga.")

# --------------------------------------------------------------------------
# 3. Peta panas
# --------------------------------------------------------------------------
lebar = (rinci_f.pivot(index="kelompok_pendek", columns="periode",
                       values="inflasi_mom")
         .reindex(columns=sorted(rinci_f["periode"].unique())))
# Diurutkan menaik berdasarkan simpangan baku. Sumbu tegak Plotly dibaca dari
# bawah ke atas, jadi urutan menaik menempatkan yang paling bergejolak di atas.
lebar = lebar.loc[lebar.std(axis=1).sort_values().index]

# Skala warna dipangkas pada persentil 92. Tanpa ini, satu bulan ekstrem
# (potongan tarif listrik awal 2025) menguasai seluruh skala dan bulan-bulan
# biasa menjadi putih semua sehingga polanya hilang.
batas = max(float(np.nanpercentile(np.abs(lebar.values), 92)), 0.5)
terpangkas = int(np.nansum(np.abs(lebar.values) > batas))

bagian("Sebaran", "Kapan tiap kelompok bergejolak",
       "Tiap kotak adalah satu kelompok pada satu bulan. Semakin merah "
       "semakin tinggi inflasi bulanannya, semakin biru semakin dalam "
       "penurunan harganya. Baris paling atas adalah kelompok yang paling "
       f"bergejolak. Skala warna dibatasi ±{angka(batas)}% agar pola bulan "
       f"biasa tetap terbaca; {terpangkas} kotak melampaui batas itu dan "
       "ditampilkan dengan warna paling pekat.")

fig = go.Figure(go.Heatmap(
    z=lebar.values,
    x=list(lebar.columns),          # tanggal asli, agar label sumbu dirapikan
    y=list(lebar.index),            # sendiri oleh Plotly dan tidak berdesakan
    # Skala dua kutub dengan abu-abu di tengah: nol harus terbaca "tidak ada
    # perubahan", bukan sebagai warna tersendiri.
    colorscale=[[0.0, WARNA["turun"]], [0.5, WARNA["netral"]],
                [1.0, WARNA["naik"]]],
    zmid=0, zmin=-batas, zmax=batas,
    xgap=2, ygap=2,
    colorbar=dict(title=dict(text="% m-to-m", side="right"),
                  thickness=11, outlinewidth=0, tickfont=dict(size=10),
                  ticksuffix="%"),
    hovertemplate="<b>%{y}</b><br>%{x|%b %Y}<br>%{z:+.2f}%<extra></extra>"))
fig.update_xaxes(dtick="M3", tickformat="%b %Y", tickangle=0)
st.plotly_chart(gaya_titik(fig, 440), use_container_width=True)

paling_gejolak = lebar.index[-1]
paling_tenang = lebar.index[0]
ekstrem = rinci_f.loc[rinci_f["inflasi_mom"].abs().idxmax()]
makanan = rinci_f[rinci_f["kelompok"].str.startswith("Makanan")]
n_mak_turun = int((makanan["inflasi_mom"] < 0).sum())
butir_peta = [
    f"Kelompok paling bergejolak: <b>{paling_gejolak}</b> (simpangan baku "
    f"{angka(lebar.std(axis=1).iloc[-1])} poin). Yang paling tenang: "
    f"<b>{paling_tenang}</b> ({angka(lebar.std(axis=1).iloc[0])} poin).",
    f"Perubahan bulanan terbesar dalam rentang ini terjadi pada "
    f"<b>{ekstrem['kelompok_pendek']}</b> di {nama_bulan(ekstrem['periode'])} "
    f"({persen(ekstrem['inflasi_mom'])}). Lonjakan sebesar ini biasanya bukan "
    "gejolak pasar biasa; kemungkinan dipicu perubahan tarif atau kebijakan, "
    "sehingga perlu dicek ke Berita Resmi Statistik.",
    f"Kelompok Makanan & Tembakau turun pada <b>{n_mak_turun} dari "
    f"{len(makanan)} bulan</b>. Karena porsinya besar, naik-turunnya "
    "kelompok ini sering menentukan arah inflasi umum bulan itu.",
]

# Efek basis. Inflasi tahunan membandingkan harga sekarang dengan bulan yang
# sama setahun lalu. Bila setahun lalu harganya anjlok, pembandingnya rendah
# dan inflasi tahunan melonjak walau harga bulan ini nyaris tidak bergerak.
# Dicari dari data: kelompok yang bulan ini tenang tetapi setahun sebelumnya
# turun tajam, lalu diambil yang inflasi tahunannya paling tinggi.
setahun = rinci[["periode", "kelompok", "inflasi_mom"]].copy()
setahun["periode"] = setahun["periode"].apply(lambda t: t.replace(year=t.year + 1))
setahun = setahun.rename(columns={"inflasi_mom": "mom_setahun_lalu"})
basis = (rinci_f.merge(setahun, on=["periode", "kelompok"])
         .query("mom_setahun_lalu <= -3 and -2 < inflasi_mom < 2")
         .sort_values("inflasi_yoy", ascending=False))
if len(basis):
    b = basis.iloc[0]
    bulan_lalu = b["periode"].replace(year=b["periode"].year - 1)
    # Penyebab hanya disebut bila memang cocok dengan catatan yang diketahui
    sebab = (" (potongan tarif listrik awal 2025)"
             if b["kelompok"].startswith("Perumahan") and bulan_lalu.year == 2025
             else "")
    butir_peta.append(
        f"<b>Hati-hati membaca angka tahunan.</b> Inflasi tahunan "
        f"<b>{b['kelompok_pendek']}</b> mencapai {persen(b['inflasi_yoy'])} pada "
        f"{nama_bulan(b['periode'])}, padahal harganya bulan itu hanya berubah "
        f"{persen(b['inflasi_mom'])}. Penyebabnya efek basis: pada "
        f"{nama_bulan(bulan_lalu)} harganya turun {persen(abs(b['mom_setahun_lalu']), tanda=False)}"
        f"{sebab}, sehingga pembanding setahunnya rendah dan angka tahunan "
        "terdongkrak. Ini bukan lonjakan harga baru.")
wawasan("Temuan", butir_peta)

# --------------------------------------------------------------------------
# 4. Tabel
# --------------------------------------------------------------------------
with st.expander(f"Lihat angka {nama_bulan(t_sorot)} dalam tabel"):
    tabel = (andil_sorot[["kelompok", "inflasi_mom", "inflasi_yoy",
                          "andil_mom", "andil_yoy", "inflasi_ytd"]]
             .rename(columns={"kelompok": "Kelompok pengeluaran",
                              "inflasi_mom": "Inflasi m-to-m (%)",
                              "inflasi_yoy": "Inflasi y-on-y (%)",
                              "andil_mom": "Andil m-to-m (poin)",
                              "andil_yoy": "Andil y-on-y (poin)",
                              "inflasi_ytd": "Inflasi y-to-d (%)"}))
    st.dataframe(tabel, use_container_width=True, hide_index=True)
    st.download_button(
        "Unduh tabel ini (CSV)",
        tabel.to_csv(index=False).encode("utf-8"),
        file_name=f"inflasi_bojonegoro_{t_sorot:%Y_%m}.csv",
        mime="text/csv")

sumber("Sumber: Berita Resmi Statistik, BPS Kabupaten Bojonegoro.")
