import requests
from bs4 import BeautifulSoup
import sqlite3
import os
import time

# ユーザーのFilmarksページURL
BASE_URL = "https://filmarks.com"
USER_PAGE = "/users/sarustar?page=1"

# ヘッダーを偽装
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# SQLiteデータベースのパス（Docker内）
DB_PATH = os.path.join(os.getcwd(), "app/data/reviews.db")

# SQLite にデータを保存する関数
def save_to_sqlite(reviews):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # テーブル作成（存在しない場合のみ）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            review TEXT,
            rating REAL,
            url TEXT
        )
    """)

    # 既存データをクリア（毎回上書き）
    cursor.execute("DELETE FROM reviews")

    # データ挿入
    for item in reviews:
        # スコアを float 型に変換（"N/A" なら NULL）
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

# 収集したレビューを保存するリスト
all_reviews = []
page_url = f"{BASE_URL}{USER_PAGE}"

while page_url:
    print(f"取得中: {page_url}")
    response = requests.get(page_url, headers=HEADERS)

    if response.status_code != 200:
        print("ページ取得に失敗:", response.status_code)
        break

    soup = BeautifulSoup(response.text, "html.parser")

    # レビューが格納されているカードを取得
    review_cards = soup.find_all("div", class_="c-content-card")

    if not review_cards:
        print("レビューが見つかりませんでした。終了します。")
        break

    for card in review_cards:
        # 映画タイトル
        title_tag = card.find("h3", class_="c-content-card__title")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        # スコア
        score_tag = card.find("div", class_="c-rating__score")
        score = score_tag.get_text(strip=True) if score_tag else "N/A"

        # レビュー本文
        review_tag = card.find("p", class_="c-content-card__review")
        review = review_tag.get_text(" ", strip=True) if review_tag else "N/A"

        # 映画の詳細ページURL
        movie_link_tag = title_tag.find("a") if title_tag else None
        movie_link = f"https://filmarks.com{movie_link_tag['href']}" if movie_link_tag else "N/A"

        all_reviews.append({
            "title": title,
            "score": score,
            "review": review,
            "url": movie_link
        })

    # 次のページのリンクを取得
    next_page_tag = soup.select_one("a.c2-pagination__next")

    if next_page_tag and "href" in next_page_tag.attrs:
        page_url = BASE_URL + next_page_tag["href"]
    else:
        print("次のページがありません。終了します。")
        break

    time.sleep(2)  # サーバー負荷対策で2秒待機

# 取得したデータを SQLite に保存
save_to_sqlite(all_reviews)

print(f"レビュー取得完了！ {len(all_reviews)}件のレビューを SQLite に保存しました。")
print(f"データベース: {DB_PATH}")