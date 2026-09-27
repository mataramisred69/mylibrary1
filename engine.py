import re
import pandas as pd
import requests


class GutenbergEngine:

    def __init__(self, csv_path="pg_catalog.csv"):
        self.csv_path = csv_path
        self.df = None
        self.load_catalog()

    def load_catalog(self):
        try:
            self.df = pd.read_csv(self.csv_path, low_memory=False)
            self.df.columns = [
                re.sub(r"\W+", "", str(c)).lower() for c in self.df.columns
            ]
        except Exception as e:
            print(f"Gagal memuat file CSV: {e}")
            self.df = pd.DataFrame()

    def search_books(self, query="", limit=3000):
        if self.df is None or self.df.empty:
            return []

        df_filtered = self.df.copy()

        col_id = next(
            (
                c
                for c in df_filtered.columns
                if "text" in c or "num" in c or "id" in c
            ),
            df_filtered.columns[0],
        )
        col_title = next(
            (c for c in df_filtered.columns if "title" in c),
            df_filtered.columns[1] if len(df_filtered.columns) > 1 else col_id,
        )
        col_author = next(
            (
                c
                for c in df_filtered.columns
                if "author" in c or "creator" in c
            ),
            None,
        )

        if query:
            q = query.lower()
            cond = df_filtered[col_title].astype(str).str.lower().str.contains(
                q, na=False
            )
            if col_author:
                cond |= (
                    df_filtered[col_author]
                    .astype(str)
                    .str.lower()
                    .str.contains(q, na=False)
                )
            df_filtered = df_filtered[cond]

        df_result = df_filtered.head(limit)

        books = []
        for _, row in df_result.iterrows():
            raw_id = str(row[col_id])
            id_match = re.search(r"\d+", raw_id)
            if not id_match:
                continue
            book_id = id_match.group(0)

            title = (
                str(row[col_title])
                if pd.notna(row[col_title])
                else "Judul Tidak Diketahui"
            )
            author = (
                str(row[col_author])
                if col_author and pd.notna(row[col_author])
                else "Penulis Anonim"
            )

            cover_url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.cover.medium.jpg"

            books.append({
                "id": book_id,
                "title": title,
                "author": author,
                "cover": cover_url,
            })

        return books

    def get_quick_text(self, book_id):
        """Mencoba 4 jalur mirror Gutenberg dengan timeout ketat 2 detik per jalur"""
        possible_urls = [
            f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
            f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8",
        ]

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        }

        for url in possible_urls:
            try:
                res = requests.get(url, timeout=2.5, headers=headers, stream=True)
                if res.status_code == 200:
                    content_bytes = bytearray()
                    for chunk in res.iter_content(chunk_size=2048):
                        content_bytes.extend(chunk)
                        if len(content_bytes) > 100000:  # Batas sampel ~100 KB
                            break

                    text = content_bytes.decode("utf-8", errors="ignore")

                    # Pembersihan awal lisensi
                    clean_start = re.search(
                        r"\*\*\* START OF TH(IS|E) GUTENBERG EBOOK .*\*\*\*",
                        text,
                        re.IGNORECASE,
                    )
                    if clean_start:
                        text = text[clean_start.end() :]

                    if len(text.strip()) > 50:
                        return text.strip()
            except Exception:
                continue

        return f"⚠️ Naskah untuk Buku ID #{book_id} tidak dapat diunduh langsung dari server Gutenberg.\n\nAnda dapat mengunduh/membaca langsung di link resmi berikut:\nhttps://www.gutenberg.org/ebooks/{book_id}"