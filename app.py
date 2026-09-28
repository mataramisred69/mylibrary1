import base64
import math
import os
import random
import requests
import streamlit as st
from engine import GutenbergEngine

# Impor pypdf untuk ekstraksi teks PDF
try:
    import pypdf

    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


@st.cache_resource
def get_engine():
    return GutenbergEngine("pg_catalog.csv")


engine = get_engine()

st.set_page_config(
    page_title="Pro Digital Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- KONFIGURASI PEMILIK & GITHUB ---
MY_EMAIL = "sahjihanfarabi@gmail.com"
OWNER_PASSWORD = "f15rahasia"

# Konfigurasi Repositori GitHub Anda
GITHUB_REPO = "mylibrary1"  # Nama repo Anda
GITHUB_USER = "mataramisred69"  # Username GitHub Anda (sesuaikan jika berbeda)


# --- FUNGSI SAVE FILE LANGSUNG KE GITHUB VIA API ---
def push_file_to_github(file_path_in_repo, content_bytes, commit_message):
    token = st.secrets.get("GITHUB_TOKEN", None)
    if not token:
        return False, "GITHUB_TOKEN belum diatur di Streamlit Secrets."

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{file_path_in_repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Cek apakah file sudah ada untuk mendapatkan sha (jika overwrite)
    res_get = requests.get(url, headers=headers)
    sha = None
    if res_get.status_code == 200:
        sha = res_get.json().get("sha")

    b64_content = base64.b64encode(content_bytes).decode("utf-8")

    payload = {"message": commit_message, "content": b64_content}
    if sha:
        payload["sha"] = sha

    res_put = requests.put(url, json=payload, headers=headers)
    if res_put.status_code in [200, 201]:
        return True, "Berhasil tersimpan ke GitHub!"
    else:
        return False, f"Gagal API: {res_put.status_code} - {res_put.text}"


# --- FUNGSI VERIFIKASI PEMILIK ---
def is_owner_verified():
    if st.session_state.get("owner_authenticated", False):
        return True

    try:
        user_email = None
        if hasattr(st, "experimental_user") and hasattr(
            st.experimental_user, "email"
        ):
            user_email = st.experimental_user.email
        elif hasattr(st, "user") and hasattr(st.user, "email"):
            user_email = st.user.email

        if (
            user_email
            and user_email.lower().strip() == MY_EMAIL.lower().strip()
        ):
            return True
    except Exception:
        pass

    return False


# --- FUNGSI AMBIL TEKS OTOMATIS (ANTI 404) ---
@st.cache_data(show_spinner="Memuat isi buku...")
def fetch_book_text(book_id):
    urls = [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
    ]

    for url in urls:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return res.text
        except Exception:
            continue

    return None


# --- FUNGSI BACA BUKU & SAMPUL PRIBADI DARI FOLDER GITHUB ---
def load_github_private_books():
    private_dir = "private_books"
    books = {}

    if os.path.exists(private_dir):
        files = os.listdir(private_dir)
        # Cari file teks / pdf
        for idx, filename in enumerate(files):
            filepath = os.path.join(private_dir, filename)
            ext = os.path.splitext(filename)[1].lower()

            if ext in [".txt", ".pdf"]:
                base_name = os.path.splitext(filename)[0]
                clean_title = base_name.replace("_", " ").title()
                content = ""

                if ext == ".txt":
                    try:
                        with open(
                            filepath, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                    except Exception:
                        content = "Gagal membaca isi file teks."

                elif ext == ".pdf" and HAS_PYPDF:
                    try:
                        reader = pypdf.PdfReader(filepath)
                        pages_text = []
                        total_pages = min(len(reader.pages), 150)
                        for i in range(total_pages):
                            t = reader.pages[i].extract_text()
                            if t:
                                pages_text.append(t)
                        content = "\n\n".join(pages_text)
                    except Exception:
                        content = "Gagal mengekstrak teks dari file PDF."

                # Cari apakah ada sampul pasangan (misal: komet.jpg / komet.png)
                cover_url = f"https://via.placeholder.com/150x200?text={clean_title.replace(' ', '+')}"
                for img_ext in [".jpg", ".jpeg", ".png"]:
                    possible_cover = os.path.join(
                        private_dir, f"{base_name}{img_ext}"
                    )
                    if os.path.exists(possible_cover):
                        try:
                            with open(possible_cover, "rb") as img_f:
                                img_b64 = base64.b64encode(
                                    img_f.read()
                                ).decode()
                                cover_url = f"data:image/{img_ext.replace('.', '')};base64,{img_b64}"
                        except Exception:
                            pass
                        break

                if content:
                    books[f"gh_priv_{idx}"] = {
                        "title": clean_title,
                        "author": "Pribadi",
                        "content": content,
                        "cover": cover_url,
                    }
    return books


# --- STATE MANAGEMENT ---
if "selected_book_id" not in st.session_state:
    st.session_state.selected_book_id = None
if "selected_book_title" not in st.session_state:
    st.session_state.selected_book_title = ""
if "selected_book_author" not in st.session_state:
    st.session_state.selected_book_author = ""
if "is_private_book" not in st.session_state:
    st.session_state.is_private_book = False
if "private_text_content" not in st.session_state:
    st.session_state.private_text_content = ""

if "search_input" not in st.session_state:
    st.session_state.search_input = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

if "saved_books" not in st.session_state:
    st.session_state.saved_books = {}
if "active_view" not in st.session_state:
    st.session_state.active_view = "catalog"
if "owner_authenticated" not in st.session_state:
    st.session_state.owner_authenticated = False

# CSS LIGHT MODE + PAPER-WHITE READER
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    .f15-header {
        font-family: 'serif', 'Georgia', 'Times New Roman';
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .f15-sub {
        font-size: 13px;
        color: #64748b;
        margin-bottom: 16px;
    }
    .book-card-f15 {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    .cover-box-f15 {
        width: 100%;
        height: 160px;
        border-radius: 8px;
        overflow: hidden;
        background-color: #f1f5f9;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 8px;
    }
    .cover-img-f15 {
        max-height: 100%;
        max-width: 100%;
        object-fit: contain;
    }
    .title-f15 {
        font-family: 'serif', 'Georgia', 'Times New Roman';
        font-size: 13px;
        font-weight: 600;
        color: #0f172a;
        height: 36px;
        line-height: 1.3;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 4px;
    }
    .author-f15 {
        font-size: 11px;
        color: #64748b;
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .tag-f15 {
        display: inline-block;
        background-color: #f1f5f9;
        color: #475569;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 12px;
        margin-bottom: 8px;
    }

    /* CONTAINER BACA TERANG & TAJAM */
    .paper-reader {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        height: 680px !important;
        overflow-y: scroll !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
        font-family: 'Georgia', 'Cambria', 'Times New Roman', serif !important;
        font-size: 18px !important;
        line-height: 1.8 !important;
        color: #0f172a !important;
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
    }

    @media (max-width: 640px) {
        [data-testid="column"] {
            width: 50% !important;
            flex: 1 1 50% !important;
            min-width: 45% !important;
            padding: 0 4px !important;
        }
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
        }
        .cover-box-f15 { height: 130px !important; }
        .title-f15 { font-size: 12px !important; height: 32px !important; }
        .paper-reader {
            font-size: 16px !important;
            padding: 14px !important;
            height: 550px !important;
        }
    }
    .stButton>button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stButton>button:hover {
        background-color: #f1f5f9 !important;
        border-color: #3b82f6 !important;
        color: #1d4ed8 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

user_is_owner = is_owner_verified()

# ==========================================
# SIDEBAR: NAVIGASI & KATEGORI LENGKAP
# ==========================================
with st.sidebar:
    st.title("📚 Navigasi Menu")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button("🌐 Jelajah", use_container_width=True):
            st.session_state.active_view = "catalog"
            st.rerun()
    with col_m2:
        saved_count = len(st.session_state.saved_books)
        if st.button(f"🔖 Buku Saya ({saved_count})", use_container_width=True):
            st.session_state.active_view = "my_library"
            st.rerun()

    if st.button("🔒 Panel Buku Pribadi", use_container_width=True):
        st.session_state.active_view = "private_vault"
        st.rerun()

    st.divider()
    st.header("✨ Kategori Lengkap")

    categories = [
        {"label": "🩺 Ilmu Medis & Kesehatan", "query": "Medicine"},
        {"label": "🧠 Pengembangan Diri & Sukses", "query": "Success"},
        {"label": "💡 Filsafat & Psikologi", "query": "Philosophy"},
        {"label": "📈 Bisnis & Ekonomi", "query": "Economics"},
        {"label": "🔍 Petualangan & Detektif", "query": "Holmes"},
        {"label": "🚀 Sains & Fiksi Ilmiah", "query": "Science"},
        {"label": "📜 Sejarah & Biografi", "query": "History"},
        {"label": "🏰 Fantasi & Dongeng", "query": "Wonderland"},
        {"label": "🎭 Romance & Klasik", "query": "Love"},
        {"label": "🏛️ Politik & Hukum", "query": "Politics"},
    ]

    for cat in categories:
        if st.button(cat["label"], use_container_width=True):
            st.session_state.search_input = cat["query"]
            st.session_state.current_page = 1
            st.session_state.active_view = "catalog"
            st.rerun()

    st.divider()

    if st.button("🎲 Pilihkan Buku Acak", use_container_width=True):
        random_queries = [
            "Secret",
            "Health",
            "Mind",
            "Power",
            "Life",
            "Doctor",
            "World",
            "Art",
            "Mystery",
        ]
        st.session_state.search_input = random.choice(random_queries)
        st.session_state.current_page = 1
        st.session_state.active_view = "catalog"
        st.rerun()

    if st.session_state.search_input:
        if st.button("❌ Tampilkan Semua Buku", use_container_width=True):
            st.session_state.search_input = ""
            st.session_state.current_page = 1
            st.rerun()

# ==========================================
# 1. BACA TEKS (PAPER-WHITE READER)
# ==========================================
if st.session_state.selected_book_id is not None:
    b_id = st.session_state.selected_book_id
    b_title = st.session_state.selected_book_title
    b_author = st.session_state.selected_book_author
    is_priv = st.session_state.is_private_book

    col_back, col_save = st.columns([2, 1])
    with col_back:
        if st.button("⬅️ Kembali", use_container_width=True):
            st.session_state.selected_book_id = None
            st.rerun()
    with col_save:
        if not is_priv:
            is_saved = b_id in st.session_state.saved_books
            save_label = (
                "📌 Tersimpan di Buku Saya" if is_saved else "🔖 Simpan Buku"
            )
            if st.button(save_label, use_container_width=True):
                if is_saved:
                    del st.session_state.saved_books[b_id]
                else:
                    st.session_state.saved_books[b_id] = {
                        "title": b_title,
                        "author": b_author,
                        "cover": f"https://www.gutenberg.org/cache/epub/{b_id}/pg{b_id}.cover.medium.jpg",
                    }
                st.rerun()

    st.markdown("---")
    st.markdown(
        f"<div class='f15-header'>{b_title}</div>", unsafe_allow_html=True
    )
    st.caption(
        f"Penulis: {b_author} | {'Buku Pribadi' if is_priv else f'ID Buku: #{b_id}'}"
    )

    st.write("")

    if is_priv:
        book_content = st.session_state.private_text_content
        st.markdown(
            f'<div class="paper-reader">{book_content}</div>',
            unsafe_allow_html=True,
        )
    else:
        book_content = fetch_book_text(b_id)
        if book_content:
            st.markdown(
                f'<div class="paper-reader">{book_content}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.error("Naskah teks tidak dapat diunduh secara langsung.")

# ==========================================
# 2. PANEL BUKU PRIBADI (DENGAN AUTO-SAVE GITHUB)
# ==========================================
elif st.session_state.active_view == "private_vault":
    st.markdown(
        "<div class='f15-header'>🔒 Panel Buku Pribadi</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='f15-sub'>Upload & Simpan Permanen Langsung ke GitHub</div>",
        unsafe_allow_html=True,
    )

    if not user_is_owner:
        st.info("🔒 Konfirmasi identitas Anda sebagai pemilik untuk masuk.")
        input_pass = st.text_input(
            "Masukkan Password Pemilik:",
            type="password",
            placeholder="Ketik password...",
        )
        if st.button("🔓 Masuk Ke Panel"):
            if input_pass == OWNER_PASSWORD:
                st.session_state.owner_authenticated = True
                st.success("Akses Diterima!")
                st.rerun()
            else:
                st.error("Password salah!")
    else:
        st.success("✅ Akses Terverifikasi")
        if st.button("🔒 Keluar / Kunci Kembali"):
            st.session_state.owner_authenticated = False
            st.rerun()

        st.divider()
        st.subheader("➕ Tambah Buku Pribadi Baru ke GitHub")

        new_title = st.text_input(
            "Judul Buku:", placeholder="Masukkan judul..."
        )
        cover_file = st.file_uploader(
            "🖼️ Upload Sampul Buku (JPG/PNG):", type=["jpg", "jpeg", "png"]
        )

        st.markdown("---")
        upload_mode = st.radio(
            "Pilih Metode Naskah:",
            ["📁 Upload File Naskah (TXT)", "✍️ Ketik / Paste Manual"],
        )

        file_bytes_to_push = None
        text_content_to_push = ""

        if upload_mode == "📁 Upload File Naskah (TXT)":
            text_file = st.file_uploader(
                "Upload File Naskah (.txt):", type=["txt"]
            )
            if text_file is not None:
                file_bytes_to_push = text_file.getvalue()
        else:
            text_content_to_push = st.text_area(
                "Isi Naskah Buku (Teks Polos):",
                height=200,
                placeholder="Ketik atau tempel naskah di sini...",
            )

        if st.button("💾 Simpan Otomatis ke GitHub", use_container_width=True):
            if new_title and (file_bytes_to_push or text_content_to_push):
                slug_name = (
                    new_title.lower()
                    .replace(" ", "_")
                    .replace("'", "")
                    .replace('"', "")
                )

                # 1. Save File Teks ke private_books/slug.txt
                txt_filename = f"private_books/{slug_name}.txt"
                if file_bytes_to_push:
                    txt_bytes = file_bytes_to_push
                else:
                    txt_bytes = text_content_to_push.encode("utf-8")

                success_txt, msg_txt = push_file_to_github(
                    txt_filename,
                    txt_bytes,
                    f"Add private book text: {new_title}",
                )

                # 2. Save Sampul jika ada ke private_books/slug.jpg
                if cover_file is not None and success_txt:
                    img_ext = os.path.splitext(cover_file.name)[1].lower()
                    img_filename = f"private_books/{slug_name}{img_ext}"
                    push_file_to_github(
                        img_filename,
                        cover_file.getvalue(),
                        f"Add cover for {new_title}",
                    )

                if success_txt:
                    st.success(
                        f"Buku '{new_title}' dan sampulnya berhasil tersimpan permanen di GitHub!"
                    )
                    st.info(
                        "Streamlit Cloud sedang memperbarui data... Halaman akan dimuat ulang."
                    )
                    st.rerun()
                else:
                    st.error(f"Gagal menyimpan ke GitHub: {msg_txt}")
            else:
                st.warning("Judul dan isi naskah wajib diisi.")

        st.divider()

        # MUAT BUKU PRIBADI DARI FOLDER GITHUB 'private_books'
        github_books = load_github_private_books()

        st.subheader("📚 Koleksi Buku Pribadi Tersimpan")

        if github_books:
            priv_items = list(github_books.items())
            cols_per_row = 4
            for i in range(0, len(priv_items), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(priv_items):
                        p_id, p_info = priv_items[i + j]
                        with cols[j]:
                            st.markdown(
                                f"""
                                <div class="book-card-f15">
                                    <div class="cover-box-f15">
                                        <img src="{p_info['cover']}" class="cover-img-f15" onerror="this.src='https://via.placeholder.com/150x200?text=No+Cover'">
                                    </div>
                                    <div class="title-f15">{p_info['title']}</div>
                                    <div class="author-f15">oleh {p_info['author']}</div>
                                </div>
                            """,
                                unsafe_allow_html=True,
                            )
                            if st.button("📖 Baca", key=f"read_gh_priv_{p_id}"):
                                st.session_state.selected_book_id = p_id
                                st.session_state.selected_book_title = p_info["title"]
                                st.session_state.selected_book_author = p_info["author"]
                                st.session_state.is_private_book = True
                                st.session_state.private_text_content = p_info["content"]
                                st.rerun()
        else:
            st.info("Belum ada file buku di dalam folder `private_books/` di GitHub.")

# ==========================================
# 3. HALAMAN "BUKU SAYA" (BOOKMARK)
# ==========================================
elif st.session_state.active_view == "my_library":
    st.markdown(
        "<div class='f15-header'>📖 Buku Saya</div>", unsafe_allow_html=True
    )
    st.markdown(
        "<div class='f15-sub'>Daftar Koleksi Disimpan</div>",
        unsafe_allow_html=True,
    )

    saved_dict = st.session_state.saved_books

    if saved_dict:
        saved_items = list(saved_dict.items())
        cols_per_row = 4
        for i in range(0, len(saved_items), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(saved_items):
                    s_id, s_info = saved_items[i + j]
                    with cols[j]:
                        st.markdown(
                            f"""
                            <div class="book-card-f15">
                                <div class="cover-box-f15">
                                    <img src="{s_info['cover']}" class="cover-img-f15" onerror="this.src='https://via.placeholder.com/150x200?text=No+Cover'">
                                </div>
                                <div class="title-f15">{s_info['title']}</div>
                                <div class="author-f15">oleh {s_info['author']}</div>
                            </div>
                        """,
                            unsafe_allow_html=True,
                        )
                        if st.button("📖 Baca", key=f"read_saved_{s_id}"):
                            st.session_state.selected_book_id = s_id
                            st.session_state.selected_book_title = s_info[
                                "title"
                            ]
                            st.session_state.selected_book_author = s_info[
                                "author"
                            ]
                            st.session_state.is_private_book = False
                            st.rerun()
    else:
        st.info("Belum ada buku yang disimpan di bookmark.")

# ==========================================
# 4. KATALOG UTAMA
# ==========================================
else:
    st.markdown(
        "<div class='f15-header'>Pro Digital Library</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='f15-sub'>Eksplorasi Ribuan Koleksi Buku Klasik Dunia</div>",
        unsafe_allow_html=True,
    )

    search_query = st.text_input(
        "",
        value=st.session_state.search_input,
        placeholder="🔍 Cari Judul, Penulis, Topik, Medis, Pengembangan Diri...",
        label_visibility="collapsed",
    )

    if search_query != st.session_state.search_input:
        st.session_state.search_input = search_query
        st.session_state.current_page = 1

    query_clean = search_query.strip()

    raw_books = engine.search_books(
        query=query_clean, limit=70000 if query_clean else 70000
    )

    total_books = len(raw_books)

    if total_books > 0:
        ITEMS_PER_PAGE = 24
        total_pages = math.ceil(total_books / ITEMS_PER_PAGE)

        if st.session_state.current_page > total_pages:
            st.session_state.current_page = 1

        start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_books = raw_books[start_idx:end_idx]

        st.markdown("<br>", unsafe_allow_html=True)

        cols_per_row = 4
        for i in range(0, len(page_books), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(page_books):
                    b = page_books[i + j]
                    b_id = b["id"]
                    b_title = b["title"]
                    b_author = b["author"]
                    cover_url = b["cover"]

                    try:
                        read_time = (int(b_id) % 12) + 8
                    except (ValueError, TypeError):
                        read_time = (len(str(b_title)) % 12) + 8

                    with cols[j]:
                        st.markdown(
                            f"""
                            <div class="book-card-f15">
                                <div>
                                    <div class="cover-box-f15">
                                        <img src="{cover_url}" class="cover-img-f15" onerror="this.src='https://via.placeholder.com/150x200?text=No+Cover'">
                                    </div>
                                    <div class="title-f15" title="{b_title}">{b_title}</div>
                                    <div class="author-f15">oleh {b_author}</div>
                                </div>
                                <div>
                                    <span class="tag-f15">⏱️ {read_time} menit baca</span>
                                </div>
                            </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        if st.button(
                            "📖 Baca",
                            key=f"btn_{b_id}_{st.session_state.current_page}_{i}_{j}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_book_id = b_id
                            st.session_state.selected_book_title = b_title
                            st.session_state.selected_book_author = b_author
                            st.session_state.is_private_book = False
                            st.rerun()

                        st.write("")

        # NAVIGASI HALAMAN BAWAH
        st.markdown("---")
        st.caption(
            f"Menampilkan buku {start_idx + 1:,} - {min(end_idx, total_books):,} dari total {total_books:,} koleksi."
        )

        col_p1, col_p2, col_p3 = st.columns([1, 1, 1])

        with col_p1:
            if st.button(
                "⬅️ Sebelumnya",
                key="bot_prev_f15",
                disabled=(st.session_state.current_page == 1),
                use_container_width=True,
            ):
                st.session_state.current_page -= 1
                st.rerun()

        with col_p2:
            selected_page = st.number_input(
                "Halaman",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.current_page,
                step=1,
                label_visibility="collapsed",
            )
            if selected_page != st.session_state.current_page:
                st.session_state.current_page = selected_page
                st.rerun()

        with col_p3:
            if st.button(
                "Selanjutnya ➡️",
                key="bot_next_f15",
                disabled=(st.session_state.current_page >= total_pages),
                use_container_width=True,
            ):
                st.session_state.current_page += 1
                st.rerun()

        st.markdown(
            f"<div style='text-align: center; font-size: 11px; color: #64748b; margin-top: 4px;'>Halaman {st.session_state.current_page} dari {total_pages:,}</div>",
            unsafe_allow_html=True,
        )

    else:
        st.warning(
            f"Buku dengan kata kunci '{query_clean}' tidak ditemukan. Coba gunakan kata kunci lain!"
        )
