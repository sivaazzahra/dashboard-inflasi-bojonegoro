"""
HALAMAN 5 — METODE
==================

Bagaimana angka-angka di dashboard ini dibuat: sumber data, pembersihan,
rumus, cara peramalan diuji, dan batasannya. Semua angka bersifat dinamis
(dibaca dari data), sehingga halaman ini ikut berubah bila data diperbarui.
"""

import streamlit as st

import mesin_ramal as mesin
from alat import (SASARAN_ATAS, SASARAN_BAWAH, SASARAN_TENGAH, angka,
                  atur_halaman, bacaan, bagian, istilah, kartu, kepala,
                  muat_harga, muat_inflasi, nama_bulan, periksa_data, sumber,
                  wawasan)

atur_halaman("Metode")

if not periksa_data():
    st.stop()

inflasi = muat_inflasi()
harga = muat_harga()
umum = inflasi[inflasi["adalah_umum"]]
n_bulan_inflasi = umum["periode"].nunique()
n_kom = harga["komoditas"].nunique()
n_bulan_harga = harga["periode"].nunique()

kepala("Metode dan Cara Kerja",
       "Dari mana angkanya datang, bagaimana diolah, dan bagaimana "
       "ketepatannya diuji, supaya hasilnya bisa diperiksa orang lain.",
       f"{n_bulan_inflasi} bulan inflasi · {n_kom} komoditas · "
       f"{len(harga):,} catatan harga".replace(",", "."),
       latar="latar_peramalan")

k1, k2, k3, k4 = st.columns(4)
kartu(k1, "Data inflasi", f"{n_bulan_inflasi} bulan",
      f"{nama_bulan(umum['periode'].min())} – {nama_bulan(umum['periode'].max())}",
      kecil=True)
kartu(k2, "Data harga", f"{n_kom} komoditas",
      f"{n_bulan_harga} bulan, sampai {nama_bulan(harga['periode'].max())}",
      kecil=True)
kartu(k3, "Cara meramal", "3 metode", "SARIMA, Holt-Winters, salin tahun lalu",
      kecil=True)
kartu(k4, "Uji ramalan", f"{mesin.MUSIM} bulan", "data terakhir disembunyikan",
      kecil=True)

# --------------------------------------------------------------------------
bagian("Alur", "Dari data mentah ke dashboard",
       "Mengikuti alur kecerdasan bisnis: kumpulkan, bersihkan, simpan, "
       "analisis, sajikan.")
istilah(
    "<b>1. Ambil (Extract).</b> Inflasi dari publikasi BPS Kabupaten "
    "Bojonegoro; harga dari SISKAPERBAPO (Dinas Perindustrian dan "
    "Perdagangan Provinsi Jawa Timur).<br>"
    "<b>2. Bersihkan (Transform).</b> Menyeragamkan nama kelompok dan "
    "komoditas, mengubah format tanggal dan angka, menghitung ulang "
    "perubahan bulanan, serta memberi status pada tiap harga.<br>"
    "<b>3. Simpan (Load).</b> Hasilnya disimpan sebagai tiga tabel siap pakai "
    "(inflasi, harga, dan tabel penghubung keduanya) oleh skrip "
    "<code>siapkan_data.py</code>.<br>"
    "<b>4. Analisis.</b> Deskriptif (apa yang terjadi), diagnostik (mengapa), "
    "prediktif (peramalan), preskriptif (langkah kebijakan).<br>"
    "<b>5. Sajikan.</b> Dashboard interaktif dengan Streamlit dan Plotly.")

# --------------------------------------------------------------------------
bagian("Inflasi", "Cara membaca angka inflasi")
st.markdown("Tiga ukuran dipakai, semuanya dari indeks harga konsumen (IHK):")
st.latex(r"\text{Bulanan} = \left(\frac{IHK_t}{IHK_{t-1}} - 1\right)\times 100\%")
st.latex(r"\text{Tahunan} = \left(\frac{IHK_t}{IHK_{t-12}} - 1\right)\times 100\%")
st.latex(r"\text{Sumbangan kelompok} = \text{bobot} \times \text{inflasi kelompok}")
istilah(
    "<b>Inflasi tahunan</b> dipakai sebagai ukuran utama karena itulah yang "
    "dibandingkan dengan sasaran pemerintah. <b>Sumbangan (andil)</b> "
    "menjawab: dari total kenaikan harga, berapa poin berasal dari tiap "
    "kelompok. Kelompok yang harganya naik cepat tetapi porsinya kecil dalam "
    "belanja akan menyumbang sedikit.")
istilah(
    f"<b>Sasaran inflasi.</b> Peraturan Menteri Keuangan No. 31 Tahun 2024 "
    f"menetapkan sasaran {angka(SASARAN_TENGAH, 1)}% ± 1 poin "
    f"({angka(SASARAN_BAWAH, 1)}%–{angka(SASARAN_ATAS, 1)}%) untuk 2025–2027. "
    "Sasaran ini <b>nasional</b> dan dipakai di sini hanya sebagai pembanding "
    "bagi Bojonegoro.")

# --------------------------------------------------------------------------
bagian("Harga", "Cara menilai harga pangan",
       "Setiap harga dibandingkan dengan kebiasaannya sendiri, bukan dengan "
       "komoditas lain.")
st.latex(r"\text{Simpangan} = \left(\frac{P_t}{\bar P_{12}} - 1\right)\times 100\%")
istilah(
    "<b>Simpangan</b> membandingkan harga bulan ini dengan rata-rata 12 bulan "
    "sebelumnya. Dari angka itu, status diberikan: <i>Waspada naik</i> bila "
    "jauh di atas kebiasaan, <i>Normal</i> bila wajar, dan <i>Lebih murah</i> "
    "bila jauh di bawah. <b>Volatilitas</b> adalah rata-rata besar "
    "perubahan harga per bulan; makin besar, makin tidak stabil.")
istilah(
    "<b>Hubungan dengan inflasi.</b> Indeks harga pangan dibandingkan dengan "
    "inflasi kelompok makanan memakai <b>korelasi Pearson</b>. Nilainya "
    "antara −1 dan +1; makin dekat +1, makin searah. Korelasi hanya menunjukkan "
    "keduanya bergerak bersama, bukan bahwa yang satu menyebabkan yang lain.")

# --------------------------------------------------------------------------
bagian("Peramalan", "Cara meramal dan menguji",
       "Ramalan hanya berguna kalau terbukti lebih baik daripada cara paling "
       "sederhana. Karena itu tiga cara dipertandingkan.")
istilah(
    f"<b>{mesin.NAMA_PEMBANDING}.</b> Harga bulan ini ditebak sama dengan "
    "harga bulan yang sama tahun lalu. Dipakai sebagai tolok ukur.<br>"
    "<b>SARIMA.</b> Model deret waktu yang belajar dari hubungan harga dengan "
    "bulan-bulan sebelumnya dan dengan pola tahunan. Enam kombinasi "
    "pengaturan dicoba, dan yang terbaik dipilih dengan kriteria AIC "
    "<b>hanya dari data latih</b>.<br>"
    "<b>Holt-Winters (ETS).</b> Menghaluskan data lalu meneruskan tren dan "
    "pola musim. Bila data kurang dari dua tahun latihan, dipakai versi tanpa "
    "musim dengan tren yang diredam.")
istilah(
    f"<b>Cara menguji.</b> {mesin.MUSIM} bulan terakhir disembunyikan (6 bulan "
    "bila datanya hanya 24–35 bulan). Model belajar dari sisanya, lalu "
    "ditanya memperkirakan bulan yang disembunyikan itu. Hasilnya dibandingkan "
    "dengan harga sebenarnya. Setelah pemenang ditentukan, model dipasang "
    "ulang memakai seluruh data untuk meramal ke depan.")
st.latex(r"MAE=\frac{1}{n}\sum|A_t-F_t| \qquad "
         r"RMSE=\sqrt{\frac{1}{n}\sum(A_t-F_t)^2} \qquad "
         r"MAPE=\frac{100\%}{n}\sum\left|\frac{A_t-F_t}{A_t}\right|")
istilah(
    "<b>A</b> adalah harga sebenarnya, <b>F</b> harga ramalan. MAE dan RMSE "
    "berstuan rupiah sehingga tidak adil dibandingkan antarkomoditas; "
    "<b>MAPE</b> berupa persen, jadi dipakai menentukan pemenang. Ambang "
    "MAPE di bawah 10% dianggap layak sebagai gambaran arah.")
istilah(
    "<b>Rentang kemungkinan 80%</b> dihitung dari sebaran kesalahan model "
    "dengan anggapan kesalahan menyebar mendekati normal.")

# --------------------------------------------------------------------------
bagian("Pemeriksaan", "Tiga pemeriksaan kelayakan model",
       "Mengikuti tahapan di RPS: praproses, visualisasi, ARIMA, dan validasi.")
istilah(
    "<b>1. Uji stasioneritas (ADF, praproses).</b> Menguji apakah rata-rata "
    "dan sebaran harga stabil dari waktu ke waktu. Hipotesis nol: data "
    "<i>tidak</i> stasioner. p-value di bawah 0,05 berarti hipotesis nol "
    "ditolak, data stasioner. Bila belum, data diselisih; jumlah selisih itu "
    "adalah <b>d</b> pada ARIMA(p,d,q).<br>"
    "<b>2. ACF dan PACF (visualisasi).</b> Korelasi perubahan harga dengan "
    "perubahan harga pada jeda 1 sampai 24 bulan. Batas kemaknaan "
    "±1,96/√n. Menjadi petunjuk bagi <b>q</b> (ACF) dan <b>p</b> (PACF), serta "
    "pola musiman pada jeda 12.<br>"
    "<b>3. Uji Ljung-Box (validasi).</b> Menguji apakah sisaan model masih "
    "berkorelasi satu sama lain. Hipotesis nol: sisaan acak. p-value di atas "
    "0,05 berarti model sudah menangkap pola yang ada.")
st.latex(r"Q = n(n+2)\sum_{k=1}^{h}\frac{\hat\rho_k^2}{n-k}")
istilah("Pemeriksaan ini dihitung pada model SARIMA terbaik yang dipasang di "
        "seluruh data, dan tampil di halaman Peramalan. Hasilnya menjadi "
        "catatan kelayakan, bukan syarat yang menggugurkan ramalan.")

bagian("Pengaman", "Pengaman yang dipasang")
wawasan("Agar ramalan tidak menyesatkan", [
    f"<b>Harga mandek.</b> Bila harga sama persis selama "
    f"{mesin.BULAN_MANDEK} bulan atau lebih, komoditas tidak diramal; "
    "kemungkinan besar datanya tidak diperbarui di sumber.",
    "<b>Data minimal.</b> Dibutuhkan paling sedikit 24 bulan. Di bawah itu, "
    "pola tahunan tidak bisa dipelajari.",
    "<b>Dua tahap pemilihan.</b> Pengaturan di dalam tiap model (misalnya "
    "susunan SARIMA) dipilih memakai data latih saja dengan kriteria AIC, "
    "sehingga data uji tidak ikut menentukan. Namun <b>pemenang di antara "
    "tiga metode</b> dipilih dari MAPE pada data uji yang sama dengan yang "
    "dilaporkan, sehingga MAPE pemenang cenderung sedikit lebih optimistis "
    "daripada kenyataan ke depan. Cara yang lebih ketat adalah menyisihkan "
    "bagian data ketiga khusus untuk menilai, atau mengulang ujian di beberapa "
    "titik waktu; keduanya belum dilakukan.",
    "<b>Tolok ukur jujur.</b> Bila model rumit kalah dari menyalin harga "
    "tahun lalu, hal itu ditampilkan apa adanya dan ramalan memakai cara "
    "terbaik berikutnya.",
])

# --------------------------------------------------------------------------
bagian("Unggah", "Cara kerja unggah data sendiri")
istilah(
    "Berkas CSV atau Excel dibaca, kolom tanggal, harga, dan komoditas "
    "ditebak otomatis (bisa diubah), format angka seperti <i>Rp 14.000</i> "
    "dibersihkan, lalu data harian atau mingguan dirata-ratakan menjadi bulanan. "
    "Bulan yang kosong diisi dengan interpolasi. Setelah itu data melewati "
    "proses uji dan peramalan yang sama dengan data bawaan. Ramalan selalu "
    "dimulai dari bulan setelah data terakhir: data sampai Desember 2025 "
    "diramal mulai Januari 2026. Data tidak disimpan oleh dashboard.")

# --------------------------------------------------------------------------
bagian("Batasan", "Yang tidak bisa dilakukan dashboard ini")
st.markdown(
    """
- Yang diramal adalah **harga komoditas**, bukan angka inflasi Bojonegoro.
- Pengujian dilakukan **sekali** pada bulan-bulan terakhir, belum diulang di
  banyak titik waktu.
- Guncangan mendadak (gagal panen, perubahan kebijakan impor, bencana) tidak
  bisa diperkirakan dari pola masa lalu.
- Data inflasi masih pendek, sehingga kesimpulan jangka panjang belum kuat.
- Analisis kebijakan adalah **bahan diskusi** yang dihitung dari data, bukan
  keputusan resmi.
""")

bagian("Teknologi", "Perangkat yang dipakai")
istilah("Python, pandas dan numpy (pengolahan data), statsmodels (SARIMA dan "
        "Holt-Winters), Plotly (grafik), Streamlit (dashboard), openpyxl "
        "(berkas Excel), dan GitHub bersama Streamlit Community Cloud "
        "(penayangan).")

sumber("BPS Kabupaten Bojonegoro; SISKAPERBAPO Disperindag Provinsi Jawa "
       "Timur; Peraturan Menteri Keuangan No. 31 Tahun 2024; Hyndman & "
       "Athanasopoulos, <i>Forecasting: Principles and Practice</i>.")
