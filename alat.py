"""
ALAT BERSAMA
============

Berisi hal-hal yang dipakai berulang oleh semua halaman dashboard:
pemuatan data, warna, gaya tampilan, dan komponen tampilan.

Dikumpulkan di satu berkas supaya kalau ada yang perlu diubah (misalnya
warna atau sumber data) cukup diubah di sini, tidak di tiap halaman.
"""

import base64
from pathlib import Path

import html as _html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as komponen

AKAR = Path(__file__).resolve().parent
SIAP = AKAR / "data" / "siap"
ASET = AKAR / "aset"          # tempat berkas logo

# --------------------------------------------------------------------------
# Warna
# --------------------------------------------------------------------------
# Palet sempit dan dipakai konsisten. Biru dan jingga untuk membedakan dua
# seri; biru dan merah sebagai kutub berlawanan pada nilai yang bisa positif
# maupun negatif. Pasangan ini sudah diperiksa agar tetap terbedakan oleh
# pembaca dengan buta warna.
WARNA = {
    "seri1": "#2a78d6",      # biru
    "seri2": "#eb6834",      # jingga
    "naik": "#d03b3b",       # merah, untuk inflasi (harga naik)
    "turun": "#2a78d6",      # biru, untuk deflasi (harga turun)
    "netral": "#f0efec",     # abu-abu, titik tengah
    "aksen": "#123a6b",      # biru tua, untuk judul dan kepala halaman
    "tinta": "#101828",
    "tinta2": "#55606e",
    "redup": "#8a94a3",
    "garis": "#e6e8ec",
    "latar": "#ffffff",
    "halaman": "#f6f7f9",
}

# Nama kelompok pengeluaran BPS panjang-panjang, tidak muat di sumbu grafik.
# Versi pendek dipakai untuk label, versi panjang tetap dipakai di tabel.
PENDEK = {
    "umum(headline)": "Umum",
    "Makanan, Minuman, dan Tembakau": "Makanan & Tembakau",
    "Pakaian dan Alas Kaki": "Pakaian",
    "Perumahan, Air, Listrik, dan Bahan Bakar Rumah Tangga": "Perumahan & Energi",
    "Perlengkapan, Peralatan, dan Pemeliharaan Rutin Rumah Tangga": "Perlengkapan RT",
    "Kesehatan": "Kesehatan",
    "Transportasi": "Transportasi",
    "Informasi, Komunikasi, dan Jasa Keuangan": "Infokom & Keuangan",
    "Rekreasi, Olahraga, dan Budaya": "Rekreasi & Budaya",
    "Pendidikan": "Pendidikan",
    "Penyediaan Makanan dan Minuman/Restoran": "Restoran",
    "Perawatan Pribadi dan Jasa Lainnya": "Perawatan Pribadi",
}


# --------------------------------------------------------------------------
# Sasaran inflasi
# --------------------------------------------------------------------------
# Peraturan Menteri Keuangan No. 31 Tahun 2024: sasaran inflasi IHK tahunan
# (year-on-year) 2,5% dengan deviasi 1,0% untuk tahun 2025, 2026, dan 2027.
# Sasaran ini berlaku untuk inflasi nasional. Di dashboard ini dipakai sebagai
# acuan pembanding bagi Kabupaten Bojonegoro, bukan sebagai target resmi daerah.
SASARAN_TENGAH = 2.5
SASARAN_BAWAH = 1.5
SASARAN_ATAS = 3.5
CATATAN_SASARAN = (
    "Sasaran inflasi 2,5% ± 1% (rentang 1,5%–3,5%) untuk 2025–2027 mengacu "
    "pada PMK No. 31 Tahun 2024 dan berlaku untuk inflasi nasional. Di sini "
    "dipakai sebagai pembanding bagi Bojonegoro. Data realisasi: BPS.")

BULAN_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


# --------------------------------------------------------------------------
# Pemuatan data
# --------------------------------------------------------------------------
# @st.cache_data membuat berkas hanya dibaca sekali. Tanpa ini, setiap kali
# pengguna menggeser filter, seluruh CSV dibaca ulang dan dashboard melambat.
@st.cache_data
def muat_inflasi() -> pd.DataFrame:
    df = pd.read_csv(SIAP / "inflasi.csv", parse_dates=["periode"])
    df["kelompok_pendek"] = df["kelompok"].map(PENDEK).fillna(df["kelompok"])
    return df


@st.cache_data
def muat_harga() -> pd.DataFrame:
    return pd.read_csv(SIAP / "harga.csv", parse_dates=["periode"])


@st.cache_data
def muat_jembatan() -> pd.DataFrame:
    return pd.read_csv(SIAP / "jembatan.csv", parse_dates=["periode"])


def periksa_data() -> bool:
    """Memastikan Tahap 1 sudah dijalankan sebelum dashboard dibuka."""
    kurang = [n for n in ("inflasi.csv", "harga.csv", "jembatan.csv")
              if not (SIAP / n).exists()]
    if kurang:
        st.error(
            "Data siap pakai belum ada: " + ", ".join(kurang)
            + "\n\nJalankan dulu di Terminal:  python siapkan_data.py")
        return False
    return True


# --------------------------------------------------------------------------
# Pemformatan
# --------------------------------------------------------------------------
def angka(x, desimal: int = 2, tanda: bool = False) -> str:
    """Angka gaya Indonesia: titik untuk ribuan, koma untuk desimal."""
    if pd.isna(x):
        return "—"
    pola = f"{{:{'+' if tanda else ''},.{desimal}f}}"
    return pola.format(x).replace(",", " ").replace(".", ",").replace(" ", ".")


def persen(x, desimal: int = 2, tanda: bool = True) -> str:
    return "—" if pd.isna(x) else angka(x, desimal, tanda) + "%"


def rupiah(x) -> str:
    return "—" if pd.isna(x) else "Rp " + angka(x, 0)


def nama_bulan(tanggal) -> str:
    """Timestamp -> 'September 2026'"""
    return f"{BULAN_ID[tanggal.month - 1]} {tanggal.year}"


# --------------------------------------------------------------------------
# Gaya tampilan
# --------------------------------------------------------------------------
# Streamlit menyediakan tampilan seadanya. Lembar gaya di bawah ini mengganti
# huruf, memberi jarak yang lebih lega, membungkus grafik dalam kartu, dan
# menyembunyikan bilah bawaan Streamlit yang tidak perlu dilihat pembaca.
_GAYA = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="st-"], button, input, select, textarea {
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
}
/* Ikon bawaan Streamlit (panah menu samping, panah expander) digambar dari
   huruf khusus bernama Material Symbols. Aturan huruf di atas ikut menimpanya,
   sehingga ikon muncul sebagai tulisan "keyboard_double_arrow_left". Baris
   ini mengembalikan hurufnya. */
[data-testid="stIconMaterial"], .material-symbols-rounded,
.material-symbols-outlined {
    font-family: "Material Symbols Rounded", "Material Symbols Outlined" !important;
}
.stApp { background: linear-gradient(180deg, #e6eefa 0px, %(halaman)s 560px); }
/* Bilah atas dibuat bening, bukan disembunyikan. Tombol pembuka menu
   samping tinggal di dalamnya — kalau bilahnya dihilangkan, tombolnya
   ikut hilang dan pembaca kehilangan jalan ke halaman lain. */
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* Tombol pembuka menu samping. Muncul di pojok kiri atas begitu menunya
   ditutup. Dipaksa tampil dan diberi bingkai agar mudah terlihat. */
/* stExpandSidebarButton adalah tombolnya sendiri, sedangkan
   stSidebarCollapseButton adalah pembungkus berisi tombol. Keduanya
   ditulis agar gayanya kena pada dua-duanya. */
button[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] button {
    visibility: visible !important; opacity: 1 !important;
    background: %(latar)s !important; border: 1px solid %(garis)s !important;
    border-radius: 10px !important; color: %(aksen)s !important;
    box-shadow: 0 1px 3px rgba(16,24,40,0.12) !important;
    width: 34px !important; height: 34px !important;
}
button[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
    border-color: %(seri1)s !important; background: #f4f8fe !important;
}
button[data-testid="stExpandSidebarButton"] span { color: %(aksen)s !important; }

[data-testid="stMainBlockContainer"] {
    padding-top: 1.2rem; padding-bottom: 4rem;
    max-width: 1500px;
}

/* Kepala halaman */
.kepala {
    background: linear-gradient(135deg, %(aksen)s 0%%, #1d5aa8 100%%);
    border-radius: 16px; padding: 26px 30px; margin-bottom: 22px;
    color: #fff;
}
.logo-baris {
    display: flex; align-items: center; gap: 10px; margin-bottom: 16px;
}
.logo-baris img {
    height: 52px; width: auto; background: #fff;
    border-radius: 10px; padding: 6px 9px;
}
.kepala h1 {
    font-size: 1.85rem; font-weight: 700; margin: 0 0 6px 0;
    letter-spacing: -0.02em; color: #fff; line-height: 1.2;
}
.kepala p { margin: 0; font-size: 0.9rem; color: rgba(255,255,255,0.78); }
.lencana {
    display: inline-block; margin-top: 14px; padding: 5px 12px;
    background: rgba(255,255,255,0.15); border-radius: 999px;
    font-size: 0.76rem; font-weight: 500; color: #fff;
}

.kepala { position: relative; overflow: hidden; min-height: 190px;
    box-shadow: 0 6px 22px rgba(18,58,107,0.22); }
.kepala h1, .kepala p { text-shadow: 0 1px 6px rgba(0,0,0,0.35); }

/* Kotak temuan: daftar insight yang dihitung dari data */
.wawasan {
    background: %(latar)s; border: 1px solid %(garis)s;
    border-left: 4px solid %(seri2)s; border-radius: 12px;
    padding: 15px 20px 10px 20px; margin: 10px 0 4px 0;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}
.wawasan .judul {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: %(seri2)s; margin-bottom: 8px;
}
.wawasan ul { margin: 0; padding-left: 18px; }
.wawasan li { font-size: 0.88rem; color: %(tinta)s; line-height: 1.65; margin-bottom: 6px; }
.wawasan li b { color: %(aksen)s; }

/* Kotak penjelasan istilah */
.istilah {
    background: #f4f8fe; border: 1px dashed #b9d0ee; border-radius: 12px;
    padding: 14px 18px; margin: 8px 0; font-size: 0.87rem;
    color: %(tinta)s; line-height: 1.65;
}
.istilah b { color: %(aksen)s; }

/* Tautan antarhalaman */
[data-testid="stPageLink"] a {
    background: %(latar)s; border: 1px solid %(garis)s; border-radius: 10px;
    padding: 9px 12px; justify-content: center;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}
[data-testid="stPageLink"] a:hover { border-color: %(seri1)s; background: #f4f8fe; }
[data-testid="stPageLink"] a p { font-weight: 600; font-size: 0.86rem; color: %(aksen)s; }

/* Judul bagian */
.bagian { margin: 30px 0 12px 0; }
.bagian .mata {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: %(seri1)s; margin-bottom: 3px;
}
.bagian h2 {
    font-size: 1.22rem; font-weight: 700; color: %(tinta)s;
    margin: 0 0 3px 0; letter-spacing: -0.01em;
}
.bagian p { font-size: 0.86rem; color: %(tinta2)s; margin: 0; line-height: 1.55; }

/* Kartu angka */
.kartu {
    background: %(latar)s; border: 1px solid %(garis)s; border-radius: 14px;
    padding: 16px 18px; height: 100%%;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}
.kartu .label {
    font-size: 0.76rem; color: %(tinta2)s; font-weight: 500;
    line-height: 1.35; margin-bottom: 8px; min-height: 2.1em;
}
.kartu .nilai {
    font-size: clamp(1.25rem, 2.1vw, 1.72rem); font-weight: 700; color: %(tinta)s;
    line-height: 1.1; letter-spacing: -0.02em; white-space: nowrap;
}
.kartu .nilai.kecil { font-size: 1.12rem; line-height: 1.25; white-space: normal; }
.kartu .ket { font-size: 0.74rem; color: %(redup)s; margin-top: 7px; line-height: 1.4; }

/* Kotak bacaan singkat */
.bacaan {
    background: %(latar)s; border: 1px solid %(garis)s;
    border-left: 4px solid %(seri1)s; border-radius: 12px;
    padding: 15px 18px; margin: 6px 0 4px 0;
    font-size: 0.89rem; color: %(tinta)s; line-height: 1.65;
}
.bacaan b { color: %(aksen)s; }

/* Bungkus grafik */
[data-testid="stPlotlyChart"] {
    background: %(latar)s; border: 1px solid %(garis)s; border-radius: 14px;
    padding: 0; overflow: hidden;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}

/* Menu samping */
[data-testid="stSidebar"] h3 {
    font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: %(redup)s; font-weight: 700;
}

/* Tabel dan tombol */
[data-testid="stExpander"] {
    background: %(latar)s; border: 1px solid %(garis)s; border-radius: 12px;
}
.stDownloadButton button {
    border-radius: 9px; border: 1px solid %(garis)s; font-weight: 500;
}
.sumber {
    font-size: 0.76rem; color: %(redup)s; margin-top: 26px;
    padding-top: 14px; border-top: 1px solid %(garis)s; line-height: 1.6;
}
/* Ikon menu samping, digambar dengan CSS supaya tidak butuh berkas gambar */
[data-testid="stSidebarNav"] a { border-radius: 10px; padding: 8px 10px; gap: 10px; }
[data-testid="stSidebarNav"] a::before { content: ''; width: 20px; height: 20px; flex: none; background-color: currentColor; -webkit-mask: var(--ikon) center/contain no-repeat; mask: var(--ikon) center/contain no-repeat; }
[data-testid="stSidebarNav"] li:nth-child(1) a { --ikon: url("data:image/svg+xml,%%3Csvg%%20xmlns=%%27http://www.w3.org/2000/svg%%27%%20viewBox=%%270%%200%%2024%%2024%%27%%20fill=%%27none%%27%%20stroke=%%27black%%27%%20stroke-width=%%272%%27%%20stroke-linecap=%%27round%%27%%20stroke-linejoin=%%27round%%27%%3E%%3Cpath%%20d=%%27M3%%2011l9-8%%209%%208%%27/%%3E%%3Cpath%%20d=%%27M5%%2010v10h5v-6h4v6h5V10%%27/%%3E%%3C/svg%%3E"); }
[data-testid="stSidebarNav"] li:nth-child(2) a { --ikon: url("data:image/svg+xml,%%3Csvg%%20xmlns=%%27http://www.w3.org/2000/svg%%27%%20viewBox=%%270%%200%%2024%%2024%%27%%20fill=%%27none%%27%%20stroke=%%27black%%27%%20stroke-width=%%272%%27%%20stroke-linecap=%%27round%%27%%20stroke-linejoin=%%27round%%27%%3E%%3Cpath%%20d=%%27M3%%2017l6-6%%204%%204%%208-9%%27/%%3E%%3Cpath%%20d=%%27M15%%206h6v6%%27/%%3E%%3C/svg%%3E"); }
[data-testid="stSidebarNav"] li:nth-child(3) a { --ikon: url("data:image/svg+xml,%%3Csvg%%20xmlns=%%27http://www.w3.org/2000/svg%%27%%20viewBox=%%270%%200%%2024%%2024%%27%%20fill=%%27none%%27%%20stroke=%%27black%%27%%20stroke-width=%%272%%27%%20stroke-linecap=%%27round%%27%%20stroke-linejoin=%%27round%%27%%3E%%3Cpath%%20d=%%27M3%%205h2l2%%2011h11l2-8H6%%27/%%3E%%3Ccircle%%20cx=%%279%%27%%20cy=%%2720%%27%%20r=%%271.5%%27/%%3E%%3Ccircle%%20cx=%%2717%%27%%20cy=%%2720%%27%%20r=%%271.5%%27/%%3E%%3C/svg%%3E"); }
[data-testid="stSidebarNav"] li:nth-child(4) a { --ikon: url("data:image/svg+xml,%%3Csvg%%20xmlns=%%27http://www.w3.org/2000/svg%%27%%20viewBox=%%270%%200%%2024%%2024%%27%%20fill=%%27none%%27%%20stroke=%%27black%%27%%20stroke-width=%%272%%27%%20stroke-linecap=%%27round%%27%%20stroke-linejoin=%%27round%%27%%3E%%3Cpath%%20d=%%27M3%%203v18h18%%27/%%3E%%3Cpath%%20d=%%27M7%%2015l4-5%%203%%203%%205-6%%27%%20stroke-dasharray=%%272%%203%%27/%%3E%%3C/svg%%3E"); }

/* Menu samping berlatar biru */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #123a6b 0%%, #1d5aa8 100%%); border-right: none; }
[data-testid="stSidebar"] * { color: #fff; }
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.12); }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: #2a78d6; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.25); }
[data-testid="stSidebar"] img { background: #fff; border-radius: 10px; padding: 5px 8px; }

/* Perbaikan kontras di menu samping: tulisan di kotak putih harus gelap */
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"] button * { color: #123a6b !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #fff; }
[data-testid="stSidebar"] [data-baseweb="select"] div, [data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] svg { color: #101828 !important; fill: #101828 !important; }
[data-testid="stSidebar"] [data-baseweb="tag"], [data-testid="stSidebar"] [data-baseweb="tag"] * { color: #fff !important; }

/* Sentuhan tampilan: kartu sedikit terangkat saat disentuh, garis aksen di
   atas kartu, dan judul kepala yang mengecil di layar sempit */
.kartu { border-top: 3px solid %(seri1)s; transition: transform .15s ease, box-shadow .15s ease; }
.kartu:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(16,24,40,0.10); }
.bagian h2 { padding-left: 10px; border-left: 4px solid %(seri2)s; }
@media (max-width: 760px) {
    .kepala { padding: 20px 18px; }
    .kepala h1 { font-size: 1.4rem; }
    .logo-baris img { height: 40px; }
}

/* Kontras menu samping: tulisan di dalam kotak putih harus gelap */
[data-testid="stSidebarCollapseButton"] button { background: rgba(255,255,255,0.16) !important; border: none !important; box-shadow: none !important; }
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"] button * { color: #ffffff !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #fff; }
[data-testid="stSidebar"] [data-baseweb="select"] div, [data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] svg { color: #101828 !important; fill: #101828 !important; }
[data-testid="stSidebar"] [data-baseweb="tag"], [data-testid="stSidebar"] [data-baseweb="tag"] * { color: #fff !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] section { background: rgba(255,255,255,0.10); }
[data-testid="stSidebar"] [data-testid="stFileUploader"] small, [data-testid="stSidebar"] [data-testid="stFileUploader"] span { color: #fff; }

/* Ikon dua menu tambahan */
[data-testid="stSidebarNav"] li:nth-child(5) a { --ikon: url("data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%%3E%%3Cpath d='M9 11l3 3L22 4'/%%3E%%3Cpath d='M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11'/%%3E%%3C/svg%%3E"); }
[data-testid="stSidebarNav"] li:nth-child(6) a { --ikon: url("data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%%3E%%3Cpath d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'/%%3E%%3Cpath d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'/%%3E%%3C/svg%%3E"); }

/* Gerak halus saat halaman dibuka */
@keyframes naik-pelan { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.kartu, .wawasan, .bacaan, .istilah, .bagian { animation: naik-pelan .5s ease both; }

/* Ikon info (i) dengan penjelasan saat disentuh */
.info { display: inline-flex; align-items: center; justify-content: center;
    width: 18px; height: 18px; border-radius: 50%%; background: #e8f0fb;
    color: %(seri1)s; font-size: 11px; font-weight: 700; cursor: help;
    position: relative; margin-left: 8px; vertical-align: middle;
    letter-spacing: 0; text-transform: none; font-style: normal; }
.info::after { content: attr(data-tip); position: absolute; left: 50%%; bottom: 140%%;
    transform: translateX(-50%%); width: 270px; background: #101828; color: #fff;
    padding: 9px 12px; border-radius: 9px; font-size: .76rem; font-weight: 400;
    line-height: 1.5; opacity: 0; pointer-events: none; transition: opacity .15s;
    z-index: 60; text-align: left; box-shadow: 0 6px 18px rgba(16,24,40,.25); }
.info:hover::after, .info:focus::after { opacity: 1; }
.catatan-kaki { font-size: .74rem; color: %(redup)s; margin: 6px 2px 0 2px; line-height: 1.55; }
.pil { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: .74rem; font-weight: 600; }
.pil.hijau { background: #e3f6ec; color: #17784f; }
.pil.biru { background: #e4effc; color: #1d5aa8; }
.pil.merah { background: #fbe7e7; color: #a82a2a; }
.pil.abu { background: #eef0f3; color: #55606e; }
</style>
""" % WARNA


# --------------------------------------------------------------------------
# Logo
# --------------------------------------------------------------------------
# Logo dibaca dari folder aset/ lalu disisipkan langsung ke dalam HTML
# sebagai data base64. Cara ini dipakai supaya berkas gambarnya ikut
# terbawa saat dashboard dinaikkan ke internet, tanpa perlu alamat luar.
JENIS_GAMBAR = {".png": "image/png", ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg", ".svg": "image/svg+xml",
                ".webp": "image/webp"}


def cari_logo(dasar: str):
    """Mencari berkas logo bernama <dasar> dengan perluasan apa pun.

    Mengembalikan Path atau None, sehingga dashboard tetap jalan walau
    logonya belum dipasang.
    """
    for perluasan in JENIS_GAMBAR:
        berkas = ASET / f"{dasar}{perluasan}"
        if berkas.exists():
            return berkas
    return None


@st.cache_data
def berkas_logo(dasar: str):
    """Logo dalam bentuk data base64, siap disisipkan ke dalam HTML."""
    berkas = cari_logo(dasar)
    if berkas is None:
        return None
    jenis = JENIS_GAMBAR[berkas.suffix.lower()]
    sandi = base64.b64encode(berkas.read_bytes()).decode()
    return f"data:{jenis};base64,{sandi}"


def _deret_logo() -> str:
    """Potongan HTML berisi logo yang tersedia, atau string kosong."""
    gambar = [f'<img src="{tautan}" alt="{nama}">'
              for dasar, nama in (("logo_bps", "BPS"), ("logo_upn", "UPN"))
              if (tautan := berkas_logo(dasar))]
    return f'<div class="logo-baris">{"".join(gambar)}</div>' if gambar else ""


def atur_halaman(judul: str) -> None:
    """Pengaturan dasar halaman, dipanggil paling awal di tiap halaman."""
    # initial_sidebar_state="expanded" memaksa menu samping selalu terbuka.
    # Tanpa ini Streamlit menyembunyikannya sendiri pada layar yang dianggap
    # sempit, sehingga pembaca tidak menemukan halaman-halaman lainnya.
    st.set_page_config(page_title=f"{judul} — Dashboard BPS Bojonegoro",
                       page_icon="📊", layout="wide",
                       initial_sidebar_state="expanded")
    st.markdown(_GAYA, unsafe_allow_html=True)

    # Logo kecil di atas menu samping, muncul di semua halaman
    utama = cari_logo("logo_bps")
    if utama is not None:
        st.logo(str(utama), size="large")


def kepala(judul: str, penjelasan: str, lencana: str = "",
           latar: str = "") -> None:
    """Kepala halaman berlatar biru, dengan logo dan gambar latar bila ada.

    `latar` adalah nama berkas di folder aset/ tanpa perluasan, misalnya
    "latar_beranda". Gambar diberi lapisan biru tua di sisi kiri supaya
    tulisan tetap terbaca. Bila berkasnya tidak ada, kepala tampil polos.
    """
    tambahan = f'<div class="lencana">{lencana}</div>' if lencana else ""
    gambar = berkas_logo(latar) if latar else None
    gaya_latar = (
        'style="background-image: linear-gradient(100deg, '
        'rgba(18,58,107,0.80) 0%, rgba(18,58,107,0.52) 42%, '
        f'rgba(29,90,168,0.06) 100%), url(\'{gambar}\'); '
        'background-size: cover; background-position: center;"'
        if gambar else "")
    st.markdown(
        f'<div class="kepala" {gaya_latar}>{_deret_logo()}<h1>{judul}</h1>'
        f'<p>{penjelasan}</p>{tambahan}</div>',
        unsafe_allow_html=True)


def wawasan(judul: str, butir: list) -> None:
    """Kotak berisi beberapa temuan singkat. Setiap butir adalah HTML satu
    kalimat; semuanya dihitung dari data sehingga ikut berubah saat
    penyaring diganti."""
    isi = "".join(f"<li>{b}</li>" for b in butir)
    st.markdown(
        f'<div class="wawasan"><div class="judul">{judul}</div>'
        f'<ul>{isi}</ul></div>', unsafe_allow_html=True)


def istilah(teks: str) -> None:
    """Kotak penjelasan istilah teknis dalam bahasa sehari-hari."""
    st.markdown(f'<div class="istilah">{teks}</div>', unsafe_allow_html=True)


# Daftar halaman, dipakai untuk tautan antarhalaman di badan halaman.
# Jalurnya dihitung dari berkas pintu masuk, yaitu Beranda.py.
HALAMAN = [("Beranda.py", "Beranda"),
           ("pages/1_Inflasi.py", "Inflasi"),
           ("pages/2_Harga_Pangan.py", "Harga Pangan"),
           ("pages/3_Peramalan.py", "Peramalan")]


def navigasi() -> None:
    """Dulu menampilkan deretan tautan halaman di bawah kepala. Sekarang
    dikosongkan karena menu samping sudah memuat tautan yang sama dan
    deretan ini hanya membuat menu tampil dua kali. Fungsinya dibiarkan
    ada supaya semua halaman tetap bisa memanggilnya."""
    return None


def bagian(mata: str, judul: str, penjelasan: str = "") -> None:
    """Judul bagian dengan label kecil di atasnya."""
    p = f"<p>{penjelasan}</p>" if penjelasan else ""
    st.markdown(
        f'<div class="bagian"><div class="mata">{mata}</div>'
        f'<h2>{judul}</h2>{p}</div>', unsafe_allow_html=True)


def bacaan(teks: str) -> None:
    """Kotak satu paragraf berisi kesimpulan dalam bahasa sehari-hari.

    Isinya dihitung dari data, bukan ditulis tetap, supaya ikut berubah
    ketika pengguna mengganti penyaring.
    """
    st.markdown(f'<div class="bacaan">{teks}</div>', unsafe_allow_html=True)


def kartu(kolom, label: str, nilai: str, keterangan: str = "",
          kecil: bool = False) -> None:
    """Kartu angka ringkas.

    Dibuat sendiri, tidak memakai st.metric, karena st.metric memotong
    label yang panjang dan warnanya tidak bisa diatur.
    """
    kelas = "nilai kecil" if kecil else "nilai"
    kolom.markdown(
        f'<div class="kartu"><div class="label">{label}</div>'
        f'<div class="{kelas}">{nilai}</div>'
        f'<div class="ket">{keterangan}</div></div>',
        unsafe_allow_html=True)


# Keterangan status karya. Dipasang di kaki setiap halaman supaya dashboard
# berlogo ini tidak terbaca sebagai terbitan resmi BPS.
PENAFIAN = (
    "Dashboard ini disusun sebagai keluaran kegiatan Magang Mandiri MBKM "
    "Program Studi Sains Data, Universitas Pembangunan Nasional Veteran Jawa "
    "Timur, di BPS Kabupaten Bojonegoro. Bukan publikasi resmi BPS. Angka "
    "resmi inflasi Kabupaten Bojonegoro tetap mengacu pada Berita Resmi "
    "Statistik yang diterbitkan BPS Kabupaten Bojonegoro."
)


def sumber(teks: str) -> None:
    st.markdown(f'<div class="sumber">{teks}<br><br>{PENAFIAN}</div>',
                unsafe_allow_html=True)


def gaya(fig, tinggi: int = 360):
    """Menyeragamkan tampilan semua grafik Plotly.

    Sumbu dibuat samar dan garis bantu tipis, agar yang menonjol datanya.
    """
    fig.update_layout(
        height=tinggi,
        margin=dict(l=12, r=16, t=16, b=10),
        plot_bgcolor=WARNA["latar"],
        paper_bgcolor=WARNA["latar"],
        font=dict(family="Plus Jakarta Sans, system-ui, sans-serif",
                  size=12, color=WARNA["tinta2"]),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12,
                        bordercolor=WARNA["garis"],
                        font_family="Plus Jakarta Sans, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, title=None,
                    font=dict(size=11.5)),
    )
    fig.update_xaxes(showgrid=False, linecolor=WARNA["garis"],
                     tickcolor=WARNA["garis"], color=WARNA["redup"],
                     tickfont=dict(size=11))
    fig.update_yaxes(gridcolor=WARNA["garis"], zeroline=False,
                     linecolor="rgba(0,0,0,0)", color=WARNA["redup"],
                     tickfont=dict(size=11))
    return fig


def gaya_titik(fig, tinggi: int = 360):
    """Sama seperti gaya(), tetapi untuk grafik yang keterangannya muncul
    per titik — batang mendatar, peta panas, diagram pencar."""
    gaya(fig, tinggi)
    fig.update_layout(hovermode="closest")
    return fig


# --------------------------------------------------------------------------
# Komponen tambahan
# --------------------------------------------------------------------------
def info(teks: str) -> str:
    """Ikon (i) kecil. Saat kursor diarahkan, teks penjelasan muncul.
    Dipakai di dalam judul bagian: bagian("...", "Judul" + info("...")).
    """
    return (f'<span class="info" tabindex="0" '
            f'data-tip="{_html.escape(teks, quote=True)}">i</span>')


def pil(teks: str, warna: str = "biru") -> str:
    """Lencana kecil berwarna: hijau, biru, merah, atau abu."""
    return f'<span class="pil {warna}">{teks}</span>'


def catatan_kaki(teks: str) -> None:
    """Catatan kecil di bawah grafik, misalnya sumber acuan."""
    st.markdown(f'<div class="catatan-kaki">{teks}</div>', unsafe_allow_html=True)


def tambah_sasaran(fig):
    """Menambahkan pita sasaran inflasi 1,5%-3,5% dan tiga garis berlabel.

    Cocok untuk grafik inflasi tahunan (y-on-y), karena sasaran PMK
    31/2024 dirumuskan pada inflasi tahunan.
    """
    hijau = "#1f9d6b"
    fig.add_hrect(y0=SASARAN_BAWAH, y1=SASARAN_ATAS, line_width=0,
                  fillcolor="rgba(31,157,107,0.11)", layer="below")
    for y, label, garis, posisi in [
            (SASARAN_ATAS, "Batas atas sasaran (3,5%)", "dot", "top left"),
            (SASARAN_TENGAH, "Sasaran inflasi 2,5% (PMK 31/2024)", "dash", "top left"),
            (SASARAN_BAWAH, "Batas bawah sasaran (1,5%)", "dot", "bottom left")]:
        fig.add_hline(y=y, line_width=1.2, line_dash=garis, line_color=hijau,
                      annotation_text=label, annotation_position=posisi,
                      annotation_font=dict(size=10.5, color=hijau))
    return fig


def status_sasaran(nilai: float):
    """(teks, warna lencana) untuk inflasi tahunan terhadap sasaran."""
    if nilai < SASARAN_BAWAH:
        return "Di bawah sasaran", "biru"
    if nilai > SASARAN_ATAS:
        return "Di atas sasaran", "merah"
    return "Dalam sasaran", "hijau"


_KOMPONEN_DASAR = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Plus Jakarta Sans', system-ui, sans-serif; background: transparent; }
</style>
"""

_ANGKA_GERAK = _KOMPONEN_DASAR + """
<style>
.baris { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.k { background: #fff; border: 1px solid #e6e8ec; border-top: 3px solid #2a78d6; border-radius: 14px;
     padding: 14px 16px; box-shadow: 0 1px 2px rgba(16,24,40,.04); }
.k .l { font-size: 12px; color: #55606e; font-weight: 500; margin-bottom: 6px; line-height: 1.35; }
.k .n { font-size: 30px; font-weight: 800; color: #123a6b; letter-spacing: -0.02em; line-height: 1.1; white-space: nowrap; }
.k .t { font-size: 11.5px; color: #8a94a3; margin-top: 6px; line-height: 1.4; }
</style>
<div class="baris">__ISI__</div>
<script>
const fmt = (v, d) => v.toLocaleString('id-ID', {minimumFractionDigits: d, maximumFractionDigits: d});
document.querySelectorAll('.n').forEach(el => {
  const akhir = parseFloat(el.dataset.nilai), d = parseInt(el.dataset.desimal),
        awal = el.dataset.awalan || '', akh = el.dataset.akhiran || '';
  const mulai = performance.now(), lama = 1400;
  function langkah(t) {
    const p = Math.min((t - mulai) / lama, 1), e = 1 - Math.pow(1 - p, 3);
    el.textContent = awal + fmt(akhir * e, d) + akh;
    if (p < 1) requestAnimationFrame(langkah);
  }
  requestAnimationFrame(langkah);
});
</script>
"""

_PENGUKUR = _KOMPONEN_DASAR + """
<div style="background:#fff;border:1px solid #e6e8ec;border-radius:16px;padding:14px 10px 10px 10px;
     box-shadow:0 1px 2px rgba(16,24,40,.04);text-align:center">
  <div style="font-size:12px;color:#55606e;font-weight:600;letter-spacing:.04em;text-transform:uppercase">__JUDUL__</div>
  <svg id="s" viewBox="0 0 360 215" width="100%" style="max-width:420px"></svg>
  <div id="status" style="margin-top:-4px;font-size:13px;font-weight:700;color:__WARNASTATUS__">__STATUS__</div>
  <div style="font-size:11.5px;color:#8a94a3;margin-top:4px">__KET__</div>
</div>
<script>
const MIN = -1, MAX = 6, NILAI = __NILAI__, W = 360, cx = 180, cy = 175, r = 135, tebal = 24;
const ang = v => Math.PI * (1 - (Math.min(Math.max(v, MIN), MAX) - MIN) / (MAX - MIN));
const pt = (rad, a) => [cx + rad * Math.cos(a), cy - rad * Math.sin(a)];
const busur = (v1, v2, w) => { const [x1, y1] = pt(r, ang(v1)), [x2, y2] = pt(r, ang(v2));
  return `<path d="M${x1} ${y1} A${r} ${r} 0 0 1 ${x2} ${y2}" stroke="${w}" stroke-width="${tebal}" fill="none"/>`; };
let svg = busur(MIN, 1.5, '#2a78d6') + busur(1.5, 3.5, '#1f9d6b') + busur(3.5, MAX, '#d03b3b');
[[0,'0%'],[1.5,'1,5%'],[2.5,'2,5%'],[3.5,'3,5%'],[5,'5%']].forEach(([v, t]) => {
  const [x, y] = pt(r + 22, ang(v)); svg += `<text x="${x}" y="${y}" font-size="10.5" fill="#55606e" text-anchor="middle" dominant-baseline="middle">${t}</text>`; });
svg += '<line id="j" x1="'+cx+'" y1="'+cy+'" x2="'+cx+'" y2="'+(cy-r+12)+'" stroke="#101828" stroke-width="3.5" stroke-linecap="round"/>';
svg += `<circle cx="${cx}" cy="${cy}" r="9" fill="#101828"/>`;
svg += `<text id="v" x="${cx}" y="${cy+36}" font-size="30" font-weight="800" fill="#123a6b" text-anchor="middle">0,00%</text>`;
document.getElementById('s').innerHTML = svg;
const j = document.getElementById('j'), v = document.getElementById('v');
const fmt = x => x.toLocaleString('id-ID', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const mulai = performance.now(), lama = 1800;
function langkah(t) {
  const p = Math.min((t - mulai) / lama, 1), e = 1 - Math.pow(1 - p, 3);
  const nilai = MIN + (NILAI - MIN) * e, a = ang(nilai), [x, y] = pt(r - 12, a);
  j.setAttribute('x2', x); j.setAttribute('y2', y);
  v.textContent = (NILAI >= 0 ? '+' : '') + fmt(NILAI * e) + '%';
  if (p < 1) requestAnimationFrame(langkah);
}
requestAnimationFrame(langkah);
</script>
"""


def angka_gerak(daftar: list, tinggi: int = 135) -> None:
    """Deretan kartu angka yang menghitung naik dari nol saat halaman dibuka.

    Tiap butir berupa kamus: label, nilai, desimal, awalan, akhiran, ket.
    Digambar di dalam komponen HTML karena Streamlit tidak menjalankan
    skrip pada st.markdown.
    """
    isi = ""
    for d in daftar:
        isi += (f'<div class="k"><div class="l">{_html.escape(d["label"])}</div>'
                f'<div class="n" data-nilai="{d["nilai"]}" '
                f'data-desimal="{d.get("desimal", 0)}" '
                f'data-awalan="{_html.escape(d.get("awalan", ""))}" '
                f'data-akhiran="{_html.escape(d.get("akhiran", ""))}">0</div>'
                f'<div class="t">{_html.escape(d.get("ket", ""))}</div></div>')
    komponen.html(_ANGKA_GERAK.replace("__ISI__", isi), height=tinggi)


def pengukur_sasaran(nilai: float, judul: str, ket: str, tinggi: int = 285) -> None:
    """Pengukur setengah lingkaran: jarum bergerak ke nilai inflasi tahunan,
    dengan tiga zona (di bawah, dalam, di atas sasaran)."""
    teks, warna = status_sasaran(nilai)
    kode = {"hijau": "#17784f", "biru": "#1d5aa8", "merah": "#a82a2a"}[warna]
    html = (_PENGUKUR.replace("__NILAI__", repr(float(nilai)))
            .replace("__JUDUL__", _html.escape(judul))
            .replace("__STATUS__", _html.escape(teks))
            .replace("__WARNASTATUS__", kode)
            .replace("__KET__", _html.escape(ket)))
    komponen.html(html, height=tinggi)
