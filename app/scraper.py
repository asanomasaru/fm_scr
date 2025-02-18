import requests
from bs4 import BeautifulSoup
import sqlite3
import os
import time

# 環境変数から GITHUB_WORKSPACE を取得（なければカレントディレクトリ）
WORKSPACE = os.getenv("GITHUB_WORKSPACE", os.getcwd())
DB_PATH = os.path.join(WORKSPACE, "data/reviews.db")

# デバッグログ
print(f"✅ [INFO] GITHUB_WORKSPACE: {WORKSPACE}")
print(f"✅ [INFO] DB_PATH: {DB_PATH}")

# データディレクトリを作成
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def save_to_sqlite(reviews):
    print(f"✅ [INFO] Saving {len(reviews)} reviews to SQLite database...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # テーブル作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                review TEXT,
                rating REAL,
                url TEXT
            )
        """)

        # データ削除（毎回上書き）
        cursor.execute("DELETE FROM reviews")

        # データ挿入
        for item in reviews:
            try:
                rating = float(item["score"]) if item["score"] != "N/A" else None
            except ValueError:
                rating = None

            cursor.execute(
                "INSERT INTO reviews (title, review, rating, url) VALUES (?, ?, ?, ?)",
                (item["title"], item["review"], rating, item["url"])
            )

        conn.commit()
        conn.close()
        print(f"✅ [INFO] SQLite database saved successfully!")

    except sqlite3.Error as e:
        print(f"❌ [ERROR] SQLite Error: {e}")
        exit(1)

# ここからスクレイピング処理（変更なし）

print(f"✅ [INFO] Database exists: {os.path.exists(DB_PATH)}")