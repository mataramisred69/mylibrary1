import random
from engine import GutenbergEngine
import streamlit as st
import streamlit.components.v1 as components


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

# State Management
if "selected_book_id" not in st.session_state:
    st.session_state.selected_book_id = None
if "selected_book_title" not in st.session_state:
    st.session_state.selected_book_title = ""
if "selected_book_author" not in st.session_state:
    st.session_state.selected_book_author = ""
if "search_input" not in st.session_state:
    st.session_state.search_input = ""

# CSS UI Light Theme Modern
st.markdown(
    """
    <style>
    .stApp { background-color: #f8fafc !important; color: #0f172a; }
    .book-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    .cover-box {
        width: 100%; height: 180px; border-radius: 8px;
        overflow: hidden; background-color: #f1f5f9;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 10px;
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
# 1. MODE BACA LAYAR PENUH (EMBED READER)
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
        st.info("💡 Memuat e-reader resmi langsung di dalam aplikasi...")
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
# 2. KATALOG UTAMA & REKOMENDASI HARI INI
# ==========================================
else:
    # --- SIDEBAR: REKOMENDASI HARI INI ---
    with st.sidebar:
        st.header("✨ Rekomendasi Hari Ini")
        st.caption("Pilih topik menarik untuk eksplorasi kilat:")

        # Daftar topik rekomendasi
        topics = [
            {"label": "🔍 Petualangan & Detektif", "query": "Holmes"},
            {"label": "🚀 Sains & Fiksi Ilmiah", "query": "Science"},
            {"label": "📜 Sejarah & Deklarasi", "query": "History"},
            {"label": "🏰 Fantasi & Dongeng", "query": "Wonderland"},
            {"label": "🎭 Novel Klasik Dunia", "query": "Love"},
        ]

        for t in topics:
            if st.button(t["label"], use_container_width=True):
                st.session_state.search_input = t["query"]
                st.rerun()

        st.divider()

        # Fitur Acak Buku (Random Pick)
        if st.button("🎲 Kejutan! Pilihkan Buku Acak", use_container_width=True):
            random_queries = [
                "Secret",
                "King",
                "World",
                "Art",
                "Mystery",
                "Island",
            ]
            st.session_state.search_input = random.choice(random_queries)
            st.rerun()

    # --- TAMPILAN UTAMA ---
    st.title("📚 Pro Digital Library")
    st.caption("Akses Puluhan Ribu Buku Klasik Dunia Secara Instan")

    # Kolom Search Utama
    search_query = st.text_input(
        "🔎 Cari Judul, Penulis, atau Topik Buku:",
        value=st.session_state.search_input,
        placeholder="Ketik misalnya: Sherlock, Austen, Time Machine, War...",
    )

    # Ambil hasil pencarian dari CSV Engine
    query_clean = search_query.strip()
    raw_books = engine.search_books(
        query=query_clean, limit=100 if query_clean else 24
    )

    if raw_books:
        if query_clean:
            st.success(
                f"🎯 Menampilkan **{len(raw_books)} Hasil** untuk pencarian: *\"{query_clean}\"*"
            )
        else:
            st.subheader("🔥 Koleksi Populer Hari Ini")

        st.divider()

        # Grid Tampilan Buku (4 Kolom)
        cols_per_row = 4
        for i in range(0, len(raw_books), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(raw_books):
                    b = raw_books[i + j]
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
                            key=f"btn_{b_id}_{i}_{j}",
                            use_container_width=True,
                            type="primary",
                        ):
                            st.session_state.selected_book_id = b_id
                            st.session_state.selected_book_title = b_title
                            st.session_state.selected_book_author = b_author
                            st.rerun()

                        st.write("")
    else:
        st.warning(
            f"Buku dengan kata kunci '{query_clean}' tidak ditemukan. Coba gunakan kata kunci lain!"
        )
