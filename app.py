import math
import random

from engine import GutenbergEngine
import requests
import streamlit as st


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


# --- FUNGSI AMBIL TEKS OTOMATIS (ANTI 404) ---
@st.cache_data(show_spinner="Memuat isi buku...")
def fetch_book_text(book_id):
    # Daftar variasi URL yang mungkin digunakan oleh Project Gutenberg
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
                # Mengembalikan isi teks jika berhasil ditemukan
                return res.text
        except Exception:
            continue

    return None


# --- STATE MANAGEMENT ---
if "selected_book_id" not in st.session_state:
    st.session_state.selected_book_id = None
if "selected_book_title" not in st.session_state:
    st.session_state.selected_book_title = ""
if "selected_book_author" not in st.session_state:
    st.session_state.selected_book_author = ""
if "search_input" not in st.session_state:
    st.session_state.search_input = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

if "saved_books" not in st.session_state:
    st.session_state.saved_books = {}
if "reading_progress" not in st.session_state:
    st.session_state.reading_progress = {}
if "active_view" not in st.session_state:
    st.session_state.active_view = "catalog"

# CSS LIGHT MODE (CLEAN, ULTRA FAST, RESPONSIVE 2 KOLOM DI HP)
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
# 1. BACA TEKS LANGSUNG DI WEB (NATIVE READER ANTI 404)
# ==========================================
if st.session_state.selected_book_id is not None:
    b_id = st.session_state.selected_book_id
    b_title = st.session_state.selected_book_title
    b_author = st.session_state.selected_book_author
    cover_url = (
        f"https://www.gutenberg.org/cache/epub/{b_id}/pg{b_id}.cover.medium.jpg"
    )

    col_back, col_save = st.columns([2, 1])
    with col_back:
        if st.button("⬅️ Kembali ke Katalog", use_container_width=True):
            st.session_state.selected_book_id = None
            st.rerun()
    with col_save:
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
                    "cover": cover_url,
                }
            st.rerun()

    st.markdown("---")
    st.markdown(
        f"<div class='f15-header'>{b_title}</div>", unsafe_allow_html=True
    )
    st.caption(f"Penulis: {b_author} | ID Buku: #{b_id}")

    # Pengatur Progress Baca
    curr_prog = st.session_state.reading_progress.get(b_id, {}).get(
        "progress_pct", 0
    )
    new_prog = st.slider(
        "📊 Update Progress Membaca Anda (%):", 0, 100, curr_prog
    )
    if new_prog != curr_prog:
        st.session_state.reading_progress[b_id] = {
            "title": b_title,
            "author": b_author,
            "cover": cover_url,
            "progress_pct": new_prog,
        }

    st.write("")

    # AMBIL TEKS BUKU VIA BACKEND
    book_content = fetch_book_text(b_id)

    if book_content:
        # Menampilkan teks langsung di elemen lokal Streamlit
        st.text_area(
            "📖 Naskah Buku:", value=book_content, height=650, disabled=True
        )
    else:
        st.error("Naskah teks tidak dapat diunduh secara langsung.")
        fallback_page = f"https://www.gutenberg.org/ebooks/{b_id}"
        st.info(
            f"Silakan buka naskah melalui halaman resmi Gutenberg: [Buka Buku #{b_id}]({fallback_page})"
        )

# ==========================================
# 2. HALAMAN "BUKU SAYA" (PUSTAKA & PROGRESS)
# ==========================================
elif st.session_state.active_view == "my_library":
    st.markdown(
        "<div class='f15-header'>📖 Buku Saya</div>", unsafe_allow_html=True
    )
    st.markdown(
        "<div class='f15-sub'>Daftar Buku Yang Sedang Dibaca & Koleksi Disimpan</div>",
        unsafe_allow_html=True,
    )

    st.subheader("🔥 Lanjut Baca")
    reading_list = st.session_state.reading_progress

    if reading_list:
        for r_id, r_info in reading_list.items():
            col_img, col_det = st.columns([1, 4])
            with col_img:
                st.image(r_info["cover"], width=100)
            with col_det:
                st.write(f"**{r_info['title']}**")
                st.caption(f"oleh {r_info['author']}")
                st.progress(r_info["progress_pct"] / 100)
                st.write(f"**{r_info['progress_pct']}% selesai**")
                if st.button("📖 Lanjutkan Membaca", key=f"cont_{r_id}"):
                    st.session_state.selected_book_id = r_id
                    st.session_state.selected_book_title = r_info["title"]
                    st.session_state.selected_book_author = r_info["author"]
                    st.rerun()
            st.divider()
    else:
        st.info(
            "Belum ada buku yang sedang dibaca. Buka buku di katalog dan atur progress bacanya!"
        )

    st.subheader("🔖 Buku Yang Disimpan")
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
                            st.rerun()
    else:
        st.info("Belum ada buku yang disimpan di bookmark.")

# ==========================================
# 3. KATALOG UTAMA
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
