import random
from engine import GutenbergEngine
import math
import streamlit as st
import streamlit.components.v1 as components


@st.cache_resource
def get_engine():
    return GutenbergEngine("pg_catalog.csv")


engine = get_engine()

st.set_page_config(
    page_title="Pro Digital Library - Mega Catalog",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

# CSS Light Theme Modern
st.markdown(
    """
    <style>
    .stApp { background-color: #f8fafc !important; color: #0f172a; }
    .book-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    }
    .cover-box {
        width: 100%; height: 170px; border-radius: 8px;
        overflow: hidden; background-color: #f1f5f9;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 8px;
    }
    .cover-img { max-height: 100%; max-width: 100%; object-fit: contain; }
    .book-title {
        font-size: 13px; font-weight: 700; color: #0f172a;
        height: 36px; overflow: hidden; display: -webkit-box;
        -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 4px;
    }
    .book-author {
        font-size: 11px; color: #64748b; margin-bottom: 8px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 1. MODE BACA LAYAR PENUH
# ==========================================
if st.session_state.selected_book_id is not None:
    b_id = st.session_state.selected_book_id
    b_title = st.session_state.selected_book_title
    b_author = st.session_state.selected_book_author

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Kembali ke Katalog", use_container_width=True):
            st.session_state.selected_book_id = None
            st.rerun()

    st.markdown("---")
    st.title(f"📖 {b_title}")
    st.caption(f"Penulis: {b_author} | ID Buku: #{b_id}")

    read_tab1, read_tab2 = st.tabs(
        ["📖 E-Reader Layar Penuh", "📄 Teks Polos (Plain Text)"]
    )

    with read_tab1:
        st.info("💡 Memuat e-reader resmi...")
        reader_url = (
            f"https://www.gutenberg.org/files/{b_id}/{b_id}-h/{b_id}-h.htm"
        )
        fallback_url = f"https://www.gutenberg.org/ebooks/{b_id}.html.images"
        components.iframe(reader_url, height=700, scrolling=True)
        st.caption(
            f"Jika tampilan tidak muncul, [buka buku di tab baru]({fallback_url})"
        )

    with read_tab2:
        txt_url = f"https://www.gutenberg.org/files/{b_id}/{b_id}-0.txt"
        st.markdown(
            f"Buka langsung naskah teks polos: [Unduh/Baca Teks Raw]({txt_url})"
        )

# ==========================================
# 2. KATALOG UTAMA & REKOMENDASI (UNLIMITED BOOKS)
# ==========================================
else:
    # --- SIDEBAR: REKOMENDASI & FILTER ---
    with st.sidebar:
        st.header("✨ Rekomendasi Topik")

        topics = [
            {"label": "🔍 Petualangan & Detektif", "query": "Holmes"},
            {"label": "🚀 Sains & Fiksi Ilmiah", "query": "Science"},
            {"label": "📜 Sejarah & Klasik", "query": "History"},
            {"label": "🏰 Fantasi & Dongeng", "query": "Wonderland"},
            {"label": "🎭 Romance & Drama", "query": "Love"},
        ]

        for t in topics:
            if st.button(t["label"], use_container_width=True):
                st.session_state.search_input = t["query"]
                st.session_state.current_page = 1
                st.rerun()

        st.divider()

        if st.button("🎲 Buku Acak (Random)", use_container_width=True):
            random_queries = [
                "Secret",
                "King",
                "World",
                "Art",
                "Mystery",
                "Island",
                "Story",
                "Man",
                "Life",
                "Dark",
            ]
            st.session_state.search_input = random.choice(random_queries)
            st.session_state.current_page = 1
            st.rerun()

        if st.session_state.search_input:
            if st.button("❌ Tampilkan Semua Koleksi", use_container_width=True):
                st.session_state.search_input = ""
                st.session_state.current_page = 1
                st.rerun()

    # --- TAMPILAN UTAMA ---
    st.title("📚 Pro Digital Library")
    st.caption("Akses Lebih dari 10.000+ Buku Klasik Dunia Tanpa Lag")

    # Kolom Search Utama
    search_query = st.text_input(
        "🔎 Cari Judul, Penulis, atau Topik Buku:",
        value=st.session_state.search_input,
        placeholder="Ketik judul/penulis atau biarkan kosong untuk melihat ribuan koleksi...",
    )

    # Sinkronisasi pencarian manual
    if search_query != st.session_state.search_input:
        st.session_state.search_input = search_query
        st.session_state.current_page = 1

    query_clean = search_query.strip()

    # MENGAMBIL HINGGA 70.000 BUKU DARI CSV ENGINE (TANPA LIMIT KETAT)
    raw_books = engine.search_books(
        query=query_clean, limit=70000 if query_clean else 70000
    )

    total_books = len(raw_books)

    if total_books > 0:
        ITEMS_PER_PAGE = 24
        total_pages = math.ceil(total_books / ITEMS_PER_PAGE)

        # Validasi halaman
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = 1

        # BAR NAVIGASI ATAS
        col_info, col_jump = st.columns([3, 2])
        with col_info:
            if query_clean:
                st.success(
                    f"🎯 Ditemukan **{total_books:,} Buku** untuk keyword: *\"{query_clean}\"*"
                )
            else:
                st.info(
                    f"📂 Total **{total_books:,} Buku Tersedia** | Halaman **{st.session_state.current_page}** dari **{total_pages}**"
                )

        with col_jump:
            # Fitur Input Langsung Nomor Halaman
            selected_page = st.number_input(
                f"Lompat ke Halaman (1-{total_pages}):",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.current_page,
                step=1,
            )
            if selected_page != st.session_state.current_page:
                st.session_state.current_page = selected_page
                st.rerun()

        st.divider()

        # POTONG DATA UNTUK HALAMAN AKTIF
        start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_books = raw_books[start_idx:end_idx]

        # Render Buku dalam Grid 4 Kolom
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

                    with cols[j]:
                        st.markdown(
                            f"""
                            <div class="book-card">
                                <div class="cover-box">
                                    <img src="{cover_url}" class="cover-img" onerror="this.src='https://via.placeholder.com/150x200?text=No+Cover'">
                                </div>
                                <div class="book-title" title="{b_title}">{b_title}</div>
                                <div class="book-author">oleh {b_author}</div>
                            </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        if st.button(
                            "📖 Baca Buku",
                            key=f"btn_{b_id}_{st.session_state.current_page}_{i}_{j}",
                            use_container_width=True,
                            type="primary",
                        ):
                            st.session_state.selected_book_id = b_id
                            st.session_state.selected_book_title = b_title
                            st.session_state.selected_book_author = b_author
                            st.rerun()

                        st.write("")

        # BAR NAVIGASI BAWAH
        st.divider()
        col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
        with col_b1:
            st.caption(
                f"Menampilkan buku ke-{start_idx + 1:,} sampai {min(end_idx, total_books):,} dari total {total_books:,} buku."
            )
        with col_b2:
            if st.button(
                "⬅️ Halaman Sebelumnya",
                key="bot_prev",
                disabled=(st.session_state.current_page == 1),
                use_container_width=True,
            ):
                st.session_state.current_page -= 1
                st.rerun()
        with col_b3:
            if st.button(
                "Halaman Selanjutnya ➡️",
                key="bot_next",
                disabled=(st.session_state.current_page >= total_pages),
                use_container_width=True,
            ):
                st.session_state.current_page += 1
                st.rerun()

    else:
        st.warning(
            f"Buku dengan pencarian '{query_clean}' tidak ditemukan. Coba gunakan kata kunci lain!"
        )
