"""
HALAMAN DEPAN
=============

Berkas inilah yang dijalankan untuk menyalakan dashboard:

    streamlit run Beranda.py

Halaman-halaman lain berada di folder pages/ dan otomatis muncul
di menu sebelah kiri, berurutan sesuai angka di depan namanya.

Beranda sengaja tidak mengulang isi halaman lain. Ia hanya menjawab tiga
hal: bagaimana keadaan hari ini, apa artinya bagi orang awam, dan dari
mana sebaiknya pembaca mulai.
"""

import streamlit as st

from alat import (CATATAN_SASARAN, SASARAN_ATAS, SASARAN_BAWAH, SASARAN_TENGAH,
                  angka, angka_gerak, atur_halaman, bacaan, bagian,
                  catatan_kaki, info, istilah, kartu, kepala, muat_harga,
                  muat_inflasi, muat_jembatan, nama_bulan, periksa_data, persen,
                  pengukur_sasaran, pil, rupiah, status_sasaran, sumber)

atur_halaman("Beranda")

if not periksa_data():
    st.stop()

inflasi = muat_inflasi()
harga = muat_harga()
jembatan = muat_jembatan()

umum = inflasi[inflasi["adalah_umum"]].sort_values("periode")
terakhir = umum.iloc[-1]
yoy = float(terakhir["inflasi_yoy"])
bulan_ini = nama_bulan(terakhir["periode"])
bulan_lalu_tahun = nama_bulan(terakhir["periode"].replace(
    year=terakhir["periode"].year - 1))
status_teks, status_warna = status_sasaran(yoy)

kepala(
    "Seberapa Cepat Harga Naik di Bojonegoro?",
    "Pantau inflasi resmi BPS dan harga pasar harian dalam satu tempat, "
    "dijelaskan dengan bahasa yang mudah dipahami semua orang.",
    f"Data inflasi sampai {bulan_ini} · "
    f"harga pangan sampai {nama_bulan(harga['periode'].max())}",
    latar="latar_beranda")

# --------------------------------------------------------------------------
# Keadaan hari ini
# --------------------------------------------------------------------------
bagian("Kabar terbaru", f"Bagaimana harga-harga per {bulan_ini}?")

kiri, kanan = st.columns([1, 1.15])

with kiri:
    pengukur_sasaran(
        yoy, "Kenaikan harga setahun terakhir",
        f"dibanding {bulan_lalu_tahun}")

with kanan:
    contoh = 100_000 * (1 + yoy / 100)
    arah = "lebih mahal" if yoy >= 0 else "lebih murah"
    bacaan(
        f"Rata-rata, harga barang dan jasa di Bojonegoro "
        f"<b>{persen(abs(yoy), tanda=False)} {arah}</b> dibanding "
        f"{bulan_lalu_tahun}. Artinya belanjaan yang setahun lalu seharga "
        f"<b>Rp100.000</b>, sekarang kira-kira <b>{rupiah(contoh)}</b>.")
    st.markdown(
        f"<div style='margin:10px 2px 4px 2px;font-size:.88rem'>"
        f"Posisi terhadap sasaran pemerintah: {pil(status_teks, status_warna)}"
        f"{info('Sasaran inflasi IHK tahunan (YoY) periode 2025–2027 sebesar 2,5% ± 1% (1,5%–3,5%), mengacu pada Peraturan Menteri Keuangan (PMK) No. 31 Tahun 2024.')}"
        f"</div>", unsafe_allow_html=True)
    catatan_kaki(CATATAN_SASARAN)

# Angka yang menghitung naik. Sengaja hanya soal cakupan data, bukan angka
# inflasi, supaya tidak mengulang kartu pada halaman Inflasi.
angka_gerak([
    dict(label="Bulan data inflasi resmi", nilai=int(inflasi.periode.nunique()),
         ket="dari BPS Kabupaten Bojonegoro"),
    dict(label="Kelompok pengeluaran", nilai=int(inflasi.kelompok.nunique()) - 1,
         ket="makanan, transportasi, pendidikan, dll."),
    dict(label="Komoditas dipantau", nilai=int(harga.komoditas.nunique()),
         ket="harga pasar dari SISKAPERBAPO"),
    dict(label="Catatan harga", nilai=int(len(harga)),
         ket="per komoditas per bulan"),
])

# --------------------------------------------------------------------------
# Inflasi yang baik itu seperti apa
# --------------------------------------------------------------------------
bagian("Dasar-dasar", "Inflasi yang baik itu seperti apa?",
       "Inflasi adalah kenaikan harga barang dan jasa secara umum. Menariknya, "
       "inflasi yang ideal bukan nol: yang dicari adalah inflasi yang rendah "
       "dan stabil.")

a, b, c = st.columns(3)
kartu(a, "Terlalu rendah · di bawah 1,5%",
      "Harga melemah", "Bisa jadi tanda belanja masyarakat lesu. Pedagang dan "
      "petani menerima harga yang tertekan.", kecil=True)
kartu(b, "Sehat · 1,5% sampai 3,5%",
      "Dalam sasaran", "Harga naik pelan dan terduga. Penghasilan masih "
      "sempat menyesuaikan, daya beli terjaga.", kecil=True)
kartu(c, "Terlalu tinggi · di atas 3,5%",
      "Harga melaju", "Uang yang sama membeli lebih sedikit. Keluarga "
      "berpenghasilan tetap paling terasa dampaknya.", kecil=True)

istilah(
    f"<b>Acuannya dari mana?</b> Pemerintah menetapkan sasaran inflasi "
    f"<b>{angka(SASARAN_TENGAH, 1)}% dengan batas ±1%</b>, yaitu rentang "
    f"{angka(SASARAN_BAWAH, 1)}% sampai {angka(SASARAN_ATAS, 1)}%, untuk "
    "tahun 2025 sampai 2027 (PMK No. 31 Tahun 2024). Sasaran itu untuk "
    "inflasi seluruh Indonesia; di dashboard ini dipakai sebagai pembanding "
    "bagi Bojonegoro.")

istilah(
    "<b>Tiga cara membaca angka inflasi.</b><br>"
    "• <b>Sebulan</b> (m-to-m): harga bulan ini dibanding bulan lalu. "
    "Cocok untuk melihat kejutan sesaat, misalnya menjelang hari raya.<br>"
    "• <b>Setahun</b> (y-on-y): harga bulan ini dibanding bulan yang sama "
    "tahun lalu. Inilah angka yang dipakai untuk menilai sasaran.<br>"
    "• <b>Sejak awal tahun</b> (y-to-d): harga bulan ini dibanding Desember "
    "tahun lalu. Cocok untuk melihat perjalanan sepanjang tahun berjalan.")

# --------------------------------------------------------------------------
# Peta dashboard
# --------------------------------------------------------------------------
bagian("Mulai dari mana", "Lima halaman, lima pertanyaan",
       "Pilih halaman di menu sebelah kiri. Urutannya mengikuti alur berpikir: "
       "dari melihat, mencari sebab, memperkirakan, sampai mengambil keputusan.")

h1, h2, h3 = st.columns(3)
kartu(h1, "1 · Inflasi", "Seberapa tinggi?",
      "Perjalanan inflasi dari waktu ke waktu, dan jenis pengeluaran apa "
      "(makanan, transportasi, dan lainnya) yang paling mendorongnya.",
      kecil=True)
kartu(h2, "2 · Harga Pangan", "Apa penggeraknya?",
      "Harga bahan pangan di pasar, mana yang paling naik-turun, dan apakah "
      "benar sejalan dengan angka resmi BPS.", kecil=True)
kartu(h3, "3 · Peramalan", "Ke mana arahnya?",
      "Perkiraan harga beberapa bulan ke depan, lengkap dengan uji "
      "ketepatannya. Bisa juga memakai data yang kamu unggah sendiri.",
      kecil=True)
st.markdown("")
h4, h5, _ = st.columns(3)
kartu(h4, "4 · Kesimpulan", "Apa artinya, apa yang dilakukan?",
      "Temuan utama, gerak inflasi yang bisa diputar ulang, dan bahan "
      "pertimbangan kebijakan.", kecil=True)
kartu(h5, "5 · Metode", "Bagaimana dihitung?",
      "Sumber data, rumus, dan cara pengujian, supaya semua angka bisa "
      "ditelusuri dan dipertanggungjawabkan.", kecil=True)

sumber(
    "Sumber — Inflasi: Berita Resmi Statistik, BPS Kabupaten Bojonegoro. "
    "Harga: Sistem Informasi Ketersediaan dan Perkembangan Harga Bahan Pokok "
    "(SISKAPERBAPO), Dinas Perindustrian dan Perdagangan Provinsi Jawa Timur. "
    "Sasaran inflasi: Peraturan Menteri Keuangan No. 31 Tahun 2024.")
