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

import pandas as pd
import streamlit as st

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
.stApp { background: %(halaman)s; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

[data-testid="stMainBlockContainer"] {
    padding-top: 2.2rem; padding-bottom: 4rem;
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
    font-size: 1.72rem; font-weight: 700; color: %(tinta)s;
    line-height: 1.1; letter-spacing: -0.02em;
}
.kartu .nilai.kecil { font-size: 1.12rem; line-height: 1.25; }
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
    padding: 10px 8px 4px 8px;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04);
}

/* Menu samping */
[data-testid="stSidebar"] { background: %(latar)s; border-right: 1px solid %(garis)s; }
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


def kepala(judul: str, penjelasan: str, lencana: str = "") -> None:
    """Kepala halaman berlatar biru, dengan logo bila tersedia."""
    tambahan = f'<div class="lencana">{lencana}</div>' if lencana else ""
    st.markdown(
        f'<div class="kepala">{_deret_logo()}<h1>{judul}</h1>'
        f'<p>{penjelasan}</p>{tambahan}</div>',
        unsafe_allow_html=True)


# Daftar halaman, dipakai untuk tautan antarhalaman di badan halaman.
# Jalurnya dihitung dari berkas pintu masuk, yaitu Beranda.py.
HALAMAN = [("Beranda.py", "Beranda"),
           ("pages/1_Inflasi.py", "Inflasi"),
           ("pages/2_Harga_Pangan.py", "Harga Pangan"),
           ("pages/3_Peramalan.py", "Peramalan")]


def navigasi() -> None:
    """Deretan tautan antarhalaman, dipasang di bawah kepala tiap halaman.

    Menu samping Streamlit menyembunyikan dirinya sendiri pada layar yang
    dianggap sempit, dan pembaca yang baru pertama membuka dashboard belum
    tentu menemukannya. Tautan di badan halaman membuat seluruh halaman
    selalu terjangkau, apa pun ukuran layarnya.
    """
    for kolom, (berkas, label) in zip(st.columns(len(HALAMAN)), HALAMAN):
        kolom.page_link(berkas, label=label, use_container_width=True)


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
        margin=dict(l=8, r=12, t=8, b=8),
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
