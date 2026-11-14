# Dashboard Pemantauan Inflasi dan Harga Pangan Kabupaten Bojonegoro

Dashboard interaktif yang menggabungkan statistik inflasi resmi BPS Kabupaten
Bojonegoro dengan pemantauan harga pangan harian dari SISKAPERBAPO Jawa Timur,
lalu memproyeksikan harga beberapa bulan ke depan.

Disusun sebagai keluaran kegiatan Magang Mandiri MBKM, Program Studi Sains
Data, Universitas Pembangunan Nasional Veteran Jawa Timur, di BPS Kabupaten
Bojonegoro. **Bukan publikasi resmi BPS.** Angka resmi inflasi Kabupaten
Bojonegoro tetap mengacu pada Berita Resmi Statistik yang diterbitkan BPS
Kabupaten Bojonegoro.

---

## Latar Belakang

Angka inflasi resmi terbit sebulan sekali, sekitar sepekan setelah bulannya
berakhir. Harga pangan di pasar, sebaliknya, dipantau setiap hari. Dashboard
ini menjembatani jeda tersebut: pergerakan harga pasar dipakai untuk
menggambarkan tekanan harga yang sedang berlangsung, jauh sebelum angka
resminya tersedia.

---

## Isi Dashboard

| Halaman | Pertanyaan yang dijawab | Jenis analisis |
|---|---|---|
| Beranda | Bagaimana gambaran umumnya? | ringkasan |
| Inflasi | Seberapa tinggi, dan dari kelompok mana? | deskriptif |
| Harga Pangan | Komoditas apa penggeraknya? | diagnostik |
| Peramalan | Ke mana arahnya? | prediktif |

---

## Data

| | Inflasi | Harga pangan |
|---|---|---|
| Sumber | Berita Resmi Statistik, BPS Kabupaten Bojonegoro | SISKAPERBAPO, Disperindag Provinsi Jawa Timur |
| Periode | Januari 2024 – September 2026 | Januari 2019 – November 2026 |
| Jumlah bulan | 33 | 95 |
| Cakupan | 12 kelompok pengeluaran | 67 komoditas |

Kedua sumber beririsan selama 33 bulan. Pada periode irisan itu, perubahan
indeks harga pangan dan inflasi kelompok makanan berkorelasi **+0,783**
(R² = 61,3%), sehingga data harga pasar layak dipakai sebagai penanda dini.

Hubungan tersebut bersifat **bersamaan waktu**, bukan mendahului. Harga pasar
tidak meramalkan inflasi bulan berikutnya, melainkan menggambarkan inflasi
bulan berjalan lebih cepat.

---

## Metode Peramalan

Tiga metode dibandingkan, dengan 12 bulan terakhir disembunyikan sebagai data
uji:

| Metode | Keterangan |
|---|---|
| SARIMA | ordo dipilih dari enam calon berdasarkan AIC pada data latih |
| Holt-Winters | galat, tren, dan musiman aditif |
| Naif musiman | pembanding dasar: harga bulan ini sama dengan 12 bulan lalu |

Pemenang ditentukan dengan MAPE, lalu dipasang ulang memakai seluruh data
sebelum meramal ke depan. Pembanding naif disertakan agar terlihat apakah
pemodelan memang memberi nilai tambah.

Hasil pengujian pada 40 komoditas pangan: SARIMA unggul pada 19 komoditas,
Holt-Winters pada 21. Ketepatannya sangat beragam — dari MAPE di bawah 1%
untuk beras hingga di atas 60% untuk cabe.

---

## Struktur Berkas

```
dashboard-bps/
├── Beranda.py              # pintu masuk aplikasi
├── alat.py                 # pemuatan data, warna, dan komponen tampilan
├── siapkan_data.py         # ETL: data mentah menjadi data siap pakai
├── requirements.txt
├── .streamlit/config.toml
├── aset/                   # logo
├── pages/
│   ├── 1_Inflasi.py
│   ├── 2_Harga_Pangan.py
│   └── 3_Peramalan.py
└── data/
    ├── mentah/             # berkas asli dari sumber
    └── siap/               # keluaran siapkan_data.py
```

---

## Cara Menjalankan

```bash
pip install -r requirements.txt
python siapkan_data.py        # hanya bila data mentah diperbarui
streamlit run Beranda.py
```

---

## Keterbatasan

- Yang diramalkan adalah harga komoditas, bukan angka inflasi.
- Pengujian dilakukan sekali pada 12 bulan terakhir, belum bergulir
  (*rolling origin*).
- Ordo SARIMA dipilih dari enam calon tetap, bukan pencarian menyeluruh.
- Selang kepercayaan mengandaikan galat menyebar normal, anggapan yang lemah
  pada komoditas yang harganya sering melonjak tajam.
- Model tidak memperhitungkan kejadian luar biasa seperti gagal panen atau
  perubahan kebijakan impor.
