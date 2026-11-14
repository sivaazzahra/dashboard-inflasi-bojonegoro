"""
HALAMAN DEPAN
=============

Berkas inilah yang dijalankan untuk menyalakan dashboard:

    streamlit run Beranda.py

Halaman-halaman lain berada di folder pages/ dan otomatis muncul
di menu sebelah kiri, berurutan sesuai angka di depan namanya.
"""

import streamlit as st

from alat import (atur_halaman, bacaan, bagian, kartu, kepala, muat_harga,
                  muat_inflasi, navigasi, muat_jembatan, nama_bulan, periksa_data,
                  persen, sumber)

atur_halaman("Beranda")

if not periksa_data():
    st.stop()

inflasi = muat_inflasi()
harga = muat_harga()
jembatan = muat_jembatan()

umum = inflasi[inflasi["adalah_umum"]].sort_values("periode")
terakhir = umum.iloc[-1]
pangan_terakhir = harga["periode"].max()

kepala(
    "Pemantauan Inflasi dan Harga Pangan",
    "Kabupaten Bojonegoro · menggabungkan statistik inflasi resmi BPS dengan "
    "pemantauan harga pasar harian",
    f"Data inflasi sampai {nama_bulan(terakhir['periode'])} · "
    f"harga pangan sampai {nama_bulan(pangan_terakhir)}")
navigasi()

# --------------------------------------------------------------------------
# Angka utama
# --------------------------------------------------------------------------
bagian("Posisi terakhir", f"Inflasi {nama_bulan(terakhir['periode'])}")

k1, k2, k3, k4 = st.columns(4)
kartu(k1, "Inflasi bulanan (m-to-m)", persen(terakhir["inflasi_mom"]),
      "dibanding bulan sebelumnya")
kartu(k2, "Inflasi tahunan (y-on-y)", persen(terakhir["inflasi_yoy"]),
      "dibanding bulan yang sama tahun lalu")
kartu(k3, "Inflasi tahun berjalan (y-to-d)", persen(terakhir["inflasi_ytd"]),
      "dibanding Desember tahun lalu")

# Dihitung ulang tiap kali data diperbarui, bukan ditulis tetap
penyumbang = (inflasi[(inflasi["periode"] == terakhir["periode"])
                      & (~inflasi["adalah_umum"])]
              .sort_values("andil_yoy", ascending=False).iloc[0])
kartu(k4, "Penyumbang inflasi terbesar", penyumbang["kelompok_pendek"],
      f"menyumbang {penyumbang['andil_yoy']:.2f} dari "
      f"{terakhir['inflasi_yoy']:.2f} poin".replace(".", ","),
      kecil=True)

bagi = penyumbang["andil_yoy"] / terakhir["inflasi_yoy"] * 100
bacaan(
    f"Dari inflasi tahunan sebesar <b>{persen(terakhir['inflasi_yoy'])}</b>, "
    f"sebanyak <b>{penyumbang['andil_yoy']:.2f} poin</b> ".replace(".", ",")
    + f"atau sekitar <b>{bagi:.0f}%</b> berasal dari kelompok "
      f"{penyumbang['kelompok']}. Karena itulah dashboard ini menaruh "
      "perhatian khusus pada harga pangan: di situ sebagian besar tekanan "
      "harga di Bojonegoro terbentuk.")

# --------------------------------------------------------------------------
# Isi dashboard
# --------------------------------------------------------------------------
bagian("Isi", "Tiga halaman, tiga pertanyaan")

h1, h2, h3 = st.columns(3)
kartu(h1, "Halaman 1 · Inflasi", "Seberapa tinggi?",
      "Perkembangan inflasi umum dan kelompok pengeluaran mana yang "
      "paling menyumbang kenaikannya.", kecil=True)
kartu(h2, "Halaman 2 · Harga Pangan", "Apa penggeraknya?",
      "Harga komoditas pangan di pasar, komoditas mana yang paling "
      "bergejolak, dan kaitannya dengan angka inflasi resmi.", kecil=True)
kartu(h3, "Halaman 3 · Peramalan", "Ke mana arahnya?",
      "Proyeksi harga beberapa bulan ke depan beserta ukuran "
      "ketepatannya.", kecil=True)

st.markdown("")
st.caption("Pilih halaman pada menu di sebelah kiri.")

# --------------------------------------------------------------------------
# Cakupan data
# --------------------------------------------------------------------------
bagian("Cakupan", "Data yang dipakai",
       "Dua sumber berbeda disatukan pada kunci yang sama, yaitu bulan.")

c1, c2, c3 = st.columns(3)
kartu(c1, "Statistik inflasi — BPS Kabupaten Bojonegoro",
      f"{inflasi.periode.nunique()} bulan",
      f"{inflasi.kelompok.nunique()} kelompok pengeluaran · "
      f"{nama_bulan(inflasi.periode.min())} – {nama_bulan(inflasi.periode.max())}")
kartu(c2, "Harga pasar — SISKAPERBAPO Jawa Timur",
      f"{harga.periode.nunique()} bulan",
      f"{harga.komoditas.nunique()} komoditas · "
      f"{nama_bulan(harga.periode.min())} – {nama_bulan(harga.periode.max())}")
kartu(c3, "Bulan yang beririsan", f"{len(jembatan)} bulan",
      "periode saat kedua sumber sama-sama tersedia, dipakai untuk "
      "menguji hubungan antarkeduanya")

sumber(
    "Sumber — Inflasi: Berita Resmi Statistik, BPS Kabupaten Bojonegoro. "
    "Harga: Sistem Informasi Ketersediaan dan Perkembangan Harga Bahan Pokok "
    "(SISKAPERBAPO), Dinas Perindustrian dan Perdagangan Provinsi Jawa Timur.")
