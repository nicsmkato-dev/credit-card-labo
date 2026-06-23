# -*- coding: utf-8 -*-
"""
クレカ比較Labo 用 X 自動投稿スクリプト

- 既存の共通モジュール C:\\Users\\user\\x_poster\\x_poster.py を利用
- このサイト専用プロファイル(x_profile_creca)を使い、他アカウントと混ざらないようにする
- その日に新しく公開された記事を1本だけツイートする

使い方:
  python post_x.py login        # 最初に1回だけ。クレカ比較LaboのXアカウントに手動ログイン
  python post_x.py post-today   # 今日公開された記事をツイート（毎日タスク用）
  python post_x.py post <記事id> # 指定記事をツイート（手動テスト用）
"""
import os
import io
import sys
import json
import datetime

# 共通モジュールを読み込む
X_POSTER_DIR = r"C:\Users\user\x_poster"
sys.path.insert(0, X_POSTER_DIR)
import x_poster  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "cards.json")
LOG_FILE = os.path.join(BASE_DIR, "post_x.log")
# このサイト専用のXログインプロファイル（共通のx_profileとは別にする）
CRECA_PROFILE = os.path.join(X_POSTER_DIR, "x_profile_creca")

HASHTAGS = "#クレジットカード #クレカ #ポイ活"


def log(msg):
    """実行ログを post_x.log に追記（毎回の成否・理由を残す）"""
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    try:
        print(line)
    except Exception:
        pass
    try:
        with io.open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load():
    with io.open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def site_base(data):
    return data["site"].get("base_url", "https://creca-labo.pages.dev").rstrip("/")


def find_article(data, aid):
    for a in data["articles"]:
        if a["id"] == aid:
            return a
    return None


def today_article(data):
    today = datetime.date.today().isoformat()
    todays = [a for a in data["articles"] if a.get("published") == today]
    return todays[-1] if todays else None


def compose(article, base):
    """280字(全角換算)に収まる投稿文を作る。"""
    url = f"{base}/articles/{article['id']}.html"
    title = article["title"]
    # リード文を短く（最初の1文・約45字）
    lead = article.get("lead", "").replace("\n", "")
    hook = lead.split("。")[0]
    if len(hook) > 45:
        hook = hook[:44] + "…"
    elif hook:
        hook += "。"
    text = f"【新着記事】{title}\n\n{hook}\n\n▼くわしくはこちら\n{url}\n\n{HASHTAGS}"
    return text


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "login":
        ok = x_poster.login(profile_dir=CRECA_PROFILE)
        log(f"[login] result={ok}")
        return
    data = load()
    base = site_base(data)
    if cmd == "post-today":
        art = today_article(data)
        if not art:
            log("[post-today] 本日公開の新記事なし → スキップ")
            return
    elif cmd == "post":
        aid = sys.argv[2] if len(sys.argv) > 2 else ""
        art = find_article(data, aid)
        if not art:
            log(f"[post] 記事が見つかりません: {aid}")
            return
    else:
        print(__doc__)
        return
    text = compose(art, base)
    log(f"[{cmd}] 投稿開始 article={art['id']} title={art['title']}")
    try:
        ok = x_poster.post_to_x(text, profile_dir=CRECA_PROFILE)
    except Exception as e:
        log(f"[{cmd}] 例外: {e}")
        ok = False
    if ok:
        log(f"[{cmd}] 投稿成功 article={art['id']}")
    else:
        log(f"[{cmd}] 投稿失敗 article={art['id']}（未ログイン/重複/Xの制限等の可能性）")


if __name__ == "__main__":
    main()
