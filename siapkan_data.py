"""
TAHAP 1 — Penyediaan Data (Data Provisioning)
=============================================

Skrip ini mengubah dua berkas mentah menjadi tiga berkas siap pakai untuk
dashboard. Inilah tahap ETL: Extract (membaca), Transform (membersihkan dan
menghitung), Load (menyimpan).

MASUKAN  (letakkan di folder data/mentah/)
    data_inflasi_1.xlsx                  -- BPS Kabupaten Bojonegoro
    harga_bojonegoro_bulanan_semua.csv   -- SISKAPERBAPO Jawa Timur

KELUARAN (otomatis dibuat di folder data/siap/)
    inflasi.csv     -- inflasi per kelompok pengeluaran per bulan
    harga.csv       -- harga per komoditas per bulan, plus kolom turunan
    jembatan.csv    -- penghubung kedua sumber, satu baris per bulan

Menjalankan:
    python siapkan_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Pengaturan
# --------------------------------------------------------------------------
AKAR = Path(__file__).resolve().parent
MENTAH = AKAR / "data" / "mentah"
SIAP = AKAR / "data" / "siap"

BERKAS_INFLASI = MENTAH / "data_inflasi_1.xlsx"
BERKAS_HARGA = MENTAH / "harga_bojonegoro_bulanan_semua.csv"

NAMA_BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

# Berkas harga mentah hanya memuat nama komoditas tanpa pengelompokan.
# Pengelompokan disusun di sini agar dashboard bisa menyaring per kelompok.
# Inilah pengayaan skema: menambah dimensi baru pada data mentah.
PETA_KELOMPOK = {
    "Beras dan Serealia": [
        "Beras Medium", "Beras Premium", "Jagung Pipilan Kering",
        "KETELA POHON", "Terigu Protein Sedang (Kemasan)"],
    "Bumbu": [
        "Bawang Merah", "Bawang Putih Sinco/Honan", "Cabe Merah Besar",
        "Cabe Merah Keriting", "Cabe Rawit Merah"],
    "Daging dan Telur": [
        "Daging Ayam Kampung", "Daging Ayam Ras", "Daging Sapi Paha Belakang",
        "Telur Ayam Kampung", "Telur Ayam Ras"],
    "Ikan": [
        "Ikan Asin Teri", "Ikan Bandeng", "Ikan Cakalang", "Ikan Kembung",
        "Ikan Tongkol", "Ikan Tuna"],
    "Kacang dan Kedelai": [
        "KACANG HIJAU", "KACANG TANAH", "Kedelai Impor", "Kedelai Lokal"],
    "Minyak dan Gula": [
        "Gula Kristal Putih", "Minyak Goreng Curah",
        "Minyak Goreng Kemasan Premium", "Minyak Goreng Kemasan Sederhana",
        "Minyak Goreng MINYAKITA"],
    "Sayur dan Buah": [
        "BUNCIS", "KENTANG", "KOL/KUBIS", "Tomat Merah", "WORTEL"],
    "Susu dan Olahan": [
        "Indomie Rasa Kari Ayam", "Susu Bubuk Merk Bendera (Instant)",
        "Susu Bubuk Merk Indomilk (Instant)", "Susu Kental Manis Merk Bendera",
        "Susu Kental Manis Merk Indomilk"],
    "Energi": ["GAS ELPIGI 3 Kg"],
    "Bahan Bangunan": [
        "Bata", "Besi Beton 10 mm (12/9m)", "Besi Beton 12 mm (12/9m)",
        "Besi Beton 6 mm (12/9m)", "Besi Beton 8 mm (12/9m)", "Halus",
        "KAYU BALOK MERANTI (4 X 10)", "Paku Ukuran 10Cm", "Paku Ukuran 2 Cm",
        "Paku Ukuran 3Cm", "Paku Ukuran 4Cm", "Paku Ukuran 5Cm",
        "Paku Ukuran 7Cm", "Papan Meranti (4m X 3cm X 20mm)", "Semen Bosowa",
        "Semen Dynamix", "Semen Gresik", "Semen Padang", "Semen Tiga Roda",
        "Semen Tonasa", "TRIPLEK (6MM)"],
    "Pupuk": [
        "Pupuk KCL Non Subsidi", "Pupuk NPK Non Subsidi",
        "Pupuk SP 35 Non Subsidi", "Pupuk Urea Non Subsidi",
        "Pupuk ZA Non Subsidi"],
}

# Kelompok yang termasuk pangan, yaitu yang sepadan dengan kelompok
# Makanan, Minuman dan Tembakau pada data inflasi BPS
KELOMPOK_PANGAN = {"Beras dan Serealia", "Bumbu", "Daging dan Telur", "Ikan",
                   "Kacang dan Kedelai", "Minyak dan Gula", "Sayur dan Buah",
                   "Susu dan Olahan"}

# Komoditas yang dipakai menyusun indeks harga pangan pada berkas jembatan.
# Dipilih yang bobotnya besar dalam belanja rumah tangga.
KOMODITAS_PANGAN = [
    "Beras Medium", "Beras Premium", "Telur Ayam Ras", "Daging Ayam Ras",
    "Cabe Rawit Merah", "Cabe Merah Keriting", "Bawang Merah",
    "Bawang Putih Sinco/Honan", "Gula Kristal Putih", "Minyak Goreng Curah",
    "Daging Sapi Paha Belakang", "Tomat Merah", "KENTANG", "WORTEL",
]

# Batas untuk menandai harga yang menyimpang jauh dari kebiasaannya
BATAS_WASPADA = 15.0
BATAS_PERHATIAN = 7.0


def judul(teks: str) -> None:
    print(f"\n{'=' * 70}\n{teks}\n{'=' * 70}")


# --------------------------------------------------------------------------
# 1. INFLASI
# --------------------------------------------------------------------------
def siapkan_inflasi() -> pd.DataFrame:
    """Membaca dan membersihkan data inflasi BPS."""
    judul("1. DATA INFLASI")

    df = pd.read_excel(BERKAS_INFLASI)
    print(f"   terbaca          : {len(df)} baris, {df.shape[1]} kolom")

    # Nama kolom pada berkas asli mengandung spasi berlebih
    df.columns = [str(c).strip() for c in df.columns]

    # Nama kelompok pengeluaran terpotong baris baru di berkas Excel,
    # misalnya "Makanan, Minuman, dan\n Tembakau". Rapikan jadi satu baris.
    df["kelompok"] = (df["KELOMPOK PENGELUARAN"].astype(str)
                      .str.replace(r"\s+", " ", regex=True).str.strip())

    # Gabungkan tahun dan nama bulan menjadi satu kolom tanggal
    peta_bulan = {b: i + 1 for i, b in enumerate(NAMA_BULAN)}
    df["bulan_ke"] = df["BULAN"].map(peta_bulan)
    if df["bulan_ke"].isna().any():
        tidak_dikenal = df.loc[df["bulan_ke"].isna(), "BULAN"].unique()
        raise ValueError(f"Nama bulan tidak dikenali: {tidak_dikenal}")

    df["periode"] = pd.to_datetime(dict(
        year=df["TAHUN"].astype(int), month=df["bulan_ke"], day=1))

    # Tandai baris ringkasan supaya mudah dipisahkan dari kelompok rinci
    df["adalah_umum"] = df["kelompok"].str.contains("umum", case=False)

    hasil = (df[["periode", "kelompok", "adalah_umum",
                 "Inflasi m-to-m", "Inflasi y-on-y",
                 "andil m-to-m", "andil y-on-y", "Inflasi y-to-d"]]
             .rename(columns={
                 "Inflasi m-to-m": "inflasi_mom",
                 "Inflasi y-on-y": "inflasi_yoy",
                 "andil m-to-m": "andil_mom",
                 "andil y-on-y": "andil_yoy",
                 "Inflasi y-to-d": "inflasi_ytd"})
             .sort_values(["periode", "kelompok"]))

    print(f"   periode          : {hasil.periode.min():%b %Y} - {hasil.periode.max():%b %Y}"
          f"  ({hasil.periode.nunique()} bulan)")
    print(f"   kelompok         : {hasil.kelompok.nunique()}")
    print(f"   nilai hilang     : {hasil.isna().sum().sum()}")

    # Pemeriksaan kelengkapan: tiap bulan semestinya punya semua kelompok
    harusnya = hasil.periode.nunique() * hasil.kelompok.nunique()
    print(f"   kelengkapan      : {len(hasil)} dari {harusnya} baris "
          f"({'lengkap' if len(hasil) == harusnya else 'ADA YANG KOSONG'})")
    return hasil


# --------------------------------------------------------------------------
# 2. HARGA
# --------------------------------------------------------------------------
def siapkan_harga() -> pd.DataFrame:
    """Membaca data harga dan menambahkan kolom turunan untuk dashboard."""
    judul("2. DATA HARGA")

    df = pd.read_csv(BERKAS_HARGA)
    print(f"   terbaca          : {len(df):,} baris")

    df["periode"] = pd.to_datetime(df["bulan"], format="%Y-%m")
    df = df.sort_values(["komoditas", "periode"])

    # --- pengayaan skema -------------------------------------------------
    # Balik PETA_KELOMPOK menjadi kamus komoditas -> kelompok
    peta = {k: kel for kel, daftar in PETA_KELOMPOK.items() for k in daftar}
    df["kelompok"] = df["komoditas"].map(peta)

    belum_terpeta = sorted(df.loc[df["kelompok"].isna(), "komoditas"].unique())
    if belum_terpeta:
        raise ValueError(
            "Komoditas berikut belum ada di PETA_KELOMPOK, tambahkan dulu:\n  "
            + "\n  ".join(belum_terpeta))

    df["pangan"] = df["kelompok"].isin(KELOMPOK_PANGAN)

    # --- kolom turunan ---------------------------------------------------
    # Dikelompokkan per komoditas supaya perhitungan tidak tercampur
    per_komoditas = df.groupby("komoditas", group_keys=False)

    # Perubahan dibanding bulan lalu dan dibanding bulan yang sama tahun lalu
    df["perubahan_mom_pct"] = per_komoditas["harga"].pct_change() * 100
    df["perubahan_yoy_pct"] = per_komoditas["harga"].pct_change(12) * 100

    # Indeks harga dengan bulan pertama sebagai basis 100,
    # supaya komoditas dengan satuan harga berbeda bisa dibandingkan
    bulan_awal = df["periode"].min()
    basis = df[df["periode"] == bulan_awal].set_index("komoditas")["harga"]
    df["indeks"] = df["harga"] / df["komoditas"].map(basis) * 100

    # Rata-rata bergerak 12 bulan sebagai patokan harga normal
    df["rata2_12bln"] = per_komoditas["harga"].transform(
        lambda s: s.rolling(12, min_periods=6).mean())
    df["simpangan_pct"] = (df["harga"] / df["rata2_12bln"] - 1) * 100

    # Gejolak: seberapa besar harga biasanya berubah tiap bulan
    gejolak = df.groupby("komoditas")["perubahan_mom_pct"].std().rename("volatilitas_pct")
    df = df.merge(gejolak, on="komoditas")

    # Status berdasarkan jarak harga terhadap kebiasaannya
    df["status"] = np.select(
        [df["simpangan_pct"] > BATAS_WASPADA,
         df["simpangan_pct"] > BATAS_PERHATIAN,
         df["simpangan_pct"] < -BATAS_WASPADA,
         df["simpangan_pct"] < -BATAS_PERHATIAN],
        ["Waspada naik", "Naik", "Waspada turun", "Turun"],
        default="Normal")

    print(f"   periode          : {df.periode.min():%b %Y} - {df.periode.max():%b %Y}"
          f"  ({df.periode.nunique()} bulan)")
    print(f"   komoditas        : {df.komoditas.nunique()}")
    print(f"   kelompok         : {df.kelompok.nunique()}")
    print(f"   kolom turunan    : perubahan_mom_pct, perubahan_yoy_pct, indeks, "
          f"rata2_12bln, simpangan_pct, volatilitas_pct, status")
    return df.sort_values(["komoditas", "periode"])


# --------------------------------------------------------------------------
# 3. JEMBATAN
# --------------------------------------------------------------------------
def siapkan_jembatan(inflasi: pd.DataFrame, harga: pd.DataFrame) -> pd.DataFrame:
    """Menggabungkan kedua sumber menjadi satu baris per bulan.

    Inilah bagian integrasi skema: dua sumber dengan struktur berbeda
    disatukan pada kunci yang sama, yaitu periode bulanan.
    """
    judul("3. JEMBATAN ANTAR DUA SUMBER")

    # Indeks harga pangan: rata-rata indeks komoditas pangan terpilih,
    # dengan basis bulan pertama yang beririsan dengan data inflasi
    pangan = harga[harga["komoditas"].isin(KOMODITAS_PANGAN)]
    tersedia = sorted(pangan["komoditas"].unique())
    hilang = sorted(set(KOMODITAS_PANGAN) - set(tersedia))
    print(f"   komoditas pangan : {len(tersedia)} dipakai"
          + (f", {len(hilang)} tidak ada: {hilang}" if hilang else ""))

    lebar = pangan.pivot(index="periode", columns="komoditas", values="harga")
    awal_inflasi = inflasi["periode"].min()
    if awal_inflasi not in lebar.index:
        raise ValueError("Periode awal data inflasi tidak ada pada data harga.")

    basis = lebar.loc[awal_inflasi]
    indeks_pangan = (lebar / basis * 100).mean(axis=1).rename("indeks_harga_pangan")

    # Ambil baris inflasi yang dibutuhkan
    umum = (inflasi[inflasi["adalah_umum"]]
            .set_index("periode")[["inflasi_mom", "inflasi_yoy"]]
            .rename(columns={"inflasi_mom": "inflasi_umum_mom",
                             "inflasi_yoy": "inflasi_umum_yoy"}))
    makanan = (inflasi[inflasi["kelompok"].str.startswith("Makanan")]
               .set_index("periode")[["inflasi_mom", "andil_yoy"]]
               .rename(columns={"inflasi_mom": "inflasi_makanan_mom",
                                "andil_yoy": "andil_makanan_yoy"}))

    gabung = (pd.concat([umum, makanan, indeks_pangan], axis=1, sort=True)
              .dropna(subset=["inflasi_umum_mom"])
              .reset_index())
    gabung["harga_pangan_mom"] = gabung["indeks_harga_pangan"].pct_change() * 100

    # Periksa apakah hubungannya memang ada
    valid = gabung.dropna(subset=["harga_pangan_mom", "inflasi_makanan_mom"])
    korelasi = valid["harga_pangan_mom"].corr(valid["inflasi_makanan_mom"])
    print(f"   periode irisan   : {gabung.periode.min():%b %Y} - "
          f"{gabung.periode.max():%b %Y}  ({len(gabung)} bulan)")
    print(f"   korelasi harga pangan dengan inflasi kelompok makanan : {korelasi:+.3f}")
    if abs(korelasi) < 0.4:
        print("   PERINGATAN: hubungan lemah, periksa kembali pilihan komoditas.")
    return gabung


# --------------------------------------------------------------------------
# Alur utama
# --------------------------------------------------------------------------
def main() -> None:
    for berkas in (BERKAS_INFLASI, BERKAS_HARGA):
        if not berkas.exists():
            raise SystemExit(
                f"Berkas tidak ditemukan: {berkas}\n"
                f"Letakkan kedua berkas mentah di folder: {MENTAH}")

    SIAP.mkdir(parents=True, exist_ok=True)

    inflasi = siapkan_inflasi()
    harga = siapkan_harga()
    jembatan = siapkan_jembatan(inflasi, harga)

    judul("4. MENYIMPAN")
    for nama, data in [("inflasi", inflasi), ("harga", harga), ("jembatan", jembatan)]:
        tujuan = SIAP / f"{nama}.csv"
        # Bulatkan hanya kolom angka, kolom tanggal dibiarkan apa adanya
        angka = data.select_dtypes("number").columns
        data.assign(**{k: data[k].round(4) for k in angka}).to_csv(tujuan, index=False)
        print(f"   {tujuan.relative_to(AKAR)}  ({len(data):,} baris, {data.shape[1]} kolom)")

    print("\nTahap 1 selesai. Lanjut ke Tahap 2: membangun halaman inflasi.")


if __name__ == "__main__":
    main()
