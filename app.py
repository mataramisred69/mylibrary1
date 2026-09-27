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
    page_title="F15 Digital Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
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

# CSS CUSTOM: F15 LIBRARY DARK MODE + RESPONSIVE MOBILE GRID (2 KOLOM)
st.markdown(
    """
    <style>
    /* Dark Theme F15 Library Background */
    .stApp {
        background-color: #0d0e12 !important;
        color: #f1f5f9 !important;
    }
    
    /* Header Styling */
    .f15-header {
        font-family: 'serif', 'Georgia', 'Times New Roman';
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2px;
    }
    .f15-sub {
        font-size: 13px;
        color: #94a3b8;
        margin-bottom: 16px;
    }

    /* Card Buku ala F15 Library */
    .book-card-f15 {
        background-color: #16181e;
        border: 1px solid #262932;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
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
        background-color: #111216;
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
        color: #ffffff;
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
        color: #94a3b8;
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .tag-f15 {
        display: inline-block;
        background-color: #222530;
        color: #cbd5e1;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 12px;
        margin-bottom: 8px;
    }

    /* Target Grid Streamlit agar di HP tampil 2 Kolom Sejajar */
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
    
    /* Tombol Style Dark Custom */
    .stButton>button {
        background-color: #1f232d !important;
        color: #f1f5f9 !important;
        border: 1px solid #333846 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stButton>button:hover {
        background-color: #2a2f3d !important;
        border-color: #6366f1 !important;
        color: #ffffff !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 1. MODE BACA LAYAR PENUH (FULLSCREEN E-READER)
# ==========================================
if st.session_state.selected_book_id is not None:
    b_id = st.session_state.selected_book_id
    b_title = st.session_state.selected_book_title
    b_author = st.session_state.selected_book_author

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ Kembali ke Katalog", use_container_width=True):
            st.session_state.selected_book_id = None
            st.rerun()

    st.markdown("---")
    st.markdown(f"<div class='f15-header'>{b_title}</div>", unsafe_allow_html=True)
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
        components.iframe(reader_url, height=750, scrolling=True)
        st.caption(
            f"Jika tampilan tidak muncul, [buka buku di tab baru]({fallback_url})"
        )

    with read_tab2:
        txt_url = f"https://www.gutenberg.org/files/{b_id}/{b_id}-0.txt"
        st.markdown(
            f"Buka langsung naskah teks polos: [Unduh/Baca Teks Raw]({txt_url})"
        )

# ==========================================
# 2. KATALOG UTAMA (STYLE F15 LIBRARY)
# ==========================================
else:
    # --- SIDEBAR (REKOMENDASI TOPIK) ---
    with st.sidebar:
        st.header("✨ Kategori Pilihan")

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

        if st.button("🎲 Pilihkan Buku Acak", use_container_width=True):
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
            ]
            st.session_state.search_input = random.choice(random_queries)
            st.session_state.current_page = 1
            st.rerun()

        if st.session_state.search_input:
            if st.button("❌ Tampilkan Semua Buku", use_container_width=True):
                st.session_state.search_input = ""
                st.session_state.current_page = 1
                st.rerun()

    # --- HEADER F15 STYLE ---
    st.markdown(
        "<div class='f15-header'>F15 Digital Library</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='f15-sub'>Eksplorasi Ribuan Koleksi Buku Klasik Dunia</div>",
        unsafe_allow_html=True,
    )

    # Kolom Pencarian Utama
    search_query = st.text_input(
        "",
        value=st.session_state.search_input,
        placeholder="🔍 Cari Judul, Penulis, atau Topik Buku...",
        label_visibility="collapsed",
    )

    if search_query != st.session_state.search_input:
        st.session_state.search_input = search_query
        st.session_state.current_page = 1

    query_clean = search_query.strip()

    # AMBIL DATA SAMPAI 70.000 BUKU
    raw_books = engine.search_books(
        query=query_clean, limit=70000 if query_clean else 70000
    )

    total_books = len(raw_books)

    if total_books > 0:
        ITEMS_PER_PAGE = 24
        total_pages = math.ceil(total_books / ITEMS_PER_PAGE)

        if st.session_state.current_page > total_pages:
            st.session_state.current_page = 1

        # MENGHITUNG INDEKS BUKU UNTUK HALAMAN AKTIF
        start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_books = raw_books[start_idx:end_idx]

        st.markdown("<br>", unsafe_allow_html=True)

        # RENDER GRID BUKU (2 KOLOM DI HP, 4 KOLOM DI LAPTOP)
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

                    # Hitung estimasi durasi baca dengan aman
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

        # ==========================================
        # 3. NAVIGASI HALAMAN PROFESIONAL DI PALING BAWAH
        # ==========================================
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
