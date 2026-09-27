from engine import GutenbergEngine
import streamlit as st

st.set_page_config(
    page_title="Pro Library - CSV Catalog",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_engine():
    return GutenbergEngine("pg_catalog.csv")


engine = get_engine()

# State Management
if "selected_book_id" not in st.session_state:
    st.session_state.selected_book_id = None
if "selected_book_title" not in st.session_state:
    st.session_state.selected_book_title = ""
if "selected_book_author" not in st.session_state:
    st.session_state.selected_book_author = ""

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


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_text_stream(book_id):
    return engine.get_quick_text(book_id)


# ==========================================
# 1. MODE BACA FULL SCREEN
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

    c1, c2 = st.columns([2, 3])
    with c1:
        font_size = st.slider("🔍 Ukuran Teks (px):", 14, 30, 18)
    with c2:
        theme = st.radio(
            "🎨 Mode Tampilan:",
            ["Light Mode ☀️", "Sepia 📜", "Dark Mode 🌙"],
            horizontal=True,
        )

    if theme == "Dark Mode 🌙":
        bg, text, border = "#1e293b", "#f8fafc", "#334155"
    elif theme == "Sepia 📜":
        bg, text, border = "#fef3c7", "#78350f", "#fde68a"
    else:
        bg, text, border = "#ffffff", "#0f172a", "#cbd5e1"

    st.markdown(
        f"""
        <style>
        .stTextArea textarea {{
            background-color: {bg} !important;
            color: {text} !important;
            font-size: {font_size}px !important;
            line-height: 1.8 !important;
            border: 1px solid {border} !important;
            border-radius: 12px !important;
            font-family: 'Georgia', serif !important;
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.title(f"📖 {b_title}")
    st.caption(f"Penulis: {b_author} | ID Buku: #{b_id}")

    with st.spinner("⚡ Mengunduh naskah cerita dari Gutenberg..."):
        text_content = fetch_text_stream(b_id)

    st.text_area("Isi Naskah Buku:", value=text_content, height=600)

# ==========================================
# 2. KATALOG UTAMA
# ==========================================
else:
    st.title("📚 Pro Digital Library")
    st.caption("Katalog CSV Engine - Memuat 5.000+ Buku Instan")

    with st.sidebar:
        st.header("⚙️ Kontrol Katalog")
        target_count = st.select_slider(
            "Tampilkan Jumlah Buku:",
            options=[1000, 2000, 3000, 5000],
            value=3000,
        )

    search_query = st.text_input(
        "🔎 Cari Judul / Penulis / Kata Kunci:",
        placeholder="Ketik misalnya: Declaration, Lincoln, Bible, Alice...",
    )

    raw_books = engine.search_books(
        query=search_query.strip(), limit=target_count
    )

    if raw_books:
        st.success(
            f"🎯 Berhasil Memuat **{len(raw_books):,} Buku** dari File CSV!"
        )
        st.divider()

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
            "Tidak ada buku yang cocok atau file 'pg_catalog.csv' belum dibaca dengan benar."
        )