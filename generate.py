# -*- coding: utf-8 -*-
"""
クレカ比較ラボ サイト自動生成エンジン
data/cards.json を読み込み、全HTMLページを自動生成する。
毎日スケジュール実行することで「最終更新日」を更新し続け、SEOの鮮度を保つ。

使い方:
    python generate.py
"""
import json
import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "cards.json")

# 日本語の曜日
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def today_str():
    now = datetime.datetime.now()
    return f"{now.year}年{now.month}月{now.day}日（{WEEKDAYS[now.weekday()]}）"


def year_month():
    now = datetime.datetime.now()
    return f"{now.year}年{now.month}月"


def stars_html(n):
    return "★" * n + "☆" * (5 - n)


def card_by_id(data, cid):
    for c in data["cards"]:
        if c["id"] == cid:
            return c
    return None


def hero_card_svg():
    """ヒーロー用のオリジナル・クレジットカードSVGイラスト（著作権フリー）"""
    return """
<svg class="hero-svg" viewBox="0 0 460 380" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="クレジットカードのイラスト">
  <defs>
    <linearGradient id="cardBack" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#5c6bc0"/><stop offset="1" stop-color="#3949ab"/>
    </linearGradient>
    <linearGradient id="cardFront" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#ff8a3d"/><stop offset="1" stop-color="#f4511e"/>
    </linearGradient>
    <linearGradient id="chip" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#ffe082"/><stop offset="1" stop-color="#ffb300"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".35"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <!-- 後ろのカード -->
  <g transform="rotate(-14 230 190)">
    <rect x="70" y="70" width="300" height="190" rx="22" fill="url(#cardBack)"/>
    <rect x="70" y="70" width="300" height="190" rx="22" fill="url(#shine)"/>
    <rect x="98" y="118" width="46" height="34" rx="6" fill="url(#chip)"/>
    <path d="M98 135 h46 M121 118 v34" stroke="#b8860b" stroke-width="1.2" opacity=".5"/>
    <circle cx="330" cy="105" r="16" fill="#ffffff" opacity=".25"/>
    <circle cx="312" cy="105" r="16" fill="#ffffff" opacity=".18"/>
    <rect x="98" y="180" width="150" height="9" rx="4" fill="#ffffff" opacity=".55"/>
    <rect x="98" y="200" width="90" height="7" rx="3" fill="#ffffff" opacity=".35"/>
  </g>
  <!-- 手前のカード -->
  <g transform="rotate(8 230 210)">
    <rect x="110" y="150" width="300" height="190" rx="22" fill="url(#cardFront)"/>
    <rect x="110" y="150" width="300" height="190" rx="22" fill="url(#shine)"/>
    <rect x="138" y="198" width="48" height="36" rx="6" fill="url(#chip)"/>
    <path d="M138 216 h48 M162 198 v36" stroke="#b8860b" stroke-width="1.3" opacity=".55"/>
    <text x="138" y="290" fill="#ffffff" font-family="monospace" font-size="20" letter-spacing="3" opacity=".95">•••• •••• •••• 8021</text>
    <text x="138" y="320" fill="#ffffff" font-family="sans-serif" font-size="13" opacity=".9" letter-spacing="1">CREDIT CARD LABO</text>
    <circle cx="372" cy="200" r="17" fill="#ffffff" opacity=".85"/>
    <circle cx="352" cy="200" r="17" fill="#ffd54f" opacity=".85"/>
  </g>
  <!-- 浮遊するコイン -->
  <g>
    <circle cx="60" cy="70" r="20" fill="#ffd54f"/><text x="60" y="77" text-anchor="middle" font-size="18" fill="#a15c00" font-weight="bold">¥</text>
    <circle cx="410" cy="320" r="16" fill="#ffd54f"/><text x="410" y="326" text-anchor="middle" font-size="15" fill="#a15c00" font-weight="bold">P</text>
    <circle cx="40" cy="300" r="13" fill="#ffe082"/><text x="40" y="305" text-anchor="middle" font-size="12" fill="#a15c00" font-weight="bold">%</text>
  </g>
</svg>"""


# ---------- 共通パーツ ----------
def head(site, title, description, depth=0):
    prefix = "" if depth == 0 else "../"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{description}">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Zen+Kaku+Gothic+New:wght@500;700;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}style.css">
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-4SP91V4T07"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-4SP91V4T07');
  </script>
</head>
<body>"""


def header(site, depth=0):
    p = "" if depth == 0 else "../"
    return f"""
<header class="site-header">
  <div class="container">
    <div class="header-inner">
      <a href="{p}index.html" class="logo">{site['logo']}</a>
      <nav class="global-nav">
        <a href="{p}index.html#ranking">ランキング</a>
        <a href="{p}index.html#purpose">目的別</a>
        <a href="{p}index.html#comparison">比較表</a>
        <a href="{p}articles.html">記事一覧</a>
      </nav>
    </div>
  </div>
</header>"""


def footer(site, depth=0):
    p = "" if depth == 0 else "../"
    return f"""
<section class="disclosure-section">
  <div class="container">
    <div class="disclosure-box">
      <p>⚠️ <strong>広告・アフィリエイト表示について：</strong>本サイトはアフィリエイトプログラムに参加しており、カードお申し込みリンクを経由して成約が発生した場合、当サイトに報酬が支払われることがあります。掲載情報は編集部の調査に基づきますが、最新情報は各カード公式サイトにてご確認ください。</p>
    </div>
  </div>
</section>
<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <div class="footer-brand">
        <a href="{p}index.html" class="logo">{site['logo']}</a>
        <p>{site['tagline']}</p>
      </div>
      <div class="footer-links">
        <h4>カテゴリ</h4>
        <a href="{p}purpose/beginner.html">初心者向け</a>
        <a href="{p}purpose/travel.html">旅行・出張向け</a>
        <a href="{p}purpose/shopping.html">ネットショッピング</a>
        <a href="{p}articles.html">記事一覧</a>
      </div>
      <div class="footer-links">
        <h4>サイト情報</h4>
        <a href="{p}about.html">運営者情報</a>
        <a href="{p}privacy.html">プライバシーポリシー</a>
        <a href="{p}disclaimer.html">免責事項</a>
        <a href="{p}contact.html">お問い合わせ</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>最終更新：{today_str()}　/　© {datetime.datetime.now().year} {site['name']} All Rights Reserved.</p>
    </div>
  </div>
</footer>
</body>
</html>"""


def card_block(card, rank=None, depth=0):
    """ランキング/一覧用のカードブロック"""
    p = "" if depth == 0 else "../"
    rank_class = f"rank-{rank}" if rank else "rank-x"
    badge = f'<div class="rank-badge">{rank}位</div>' if rank else ""
    rh = " highlight" if card.get("reward_highlight") else ""
    merits = "\n".join(
        f'          <p class="merit">✅ {m}</p>' for m in card["merits"]
    )
    detail_href = f"{p}cards/{card['id']}.html"
    return f"""
    <div class="card-item {rank_class}">
      {badge}
      <div class="card-body">
        <div class="card-header-row">
          <div class="card-logo-area">
            <div class="card-logo-placeholder {card['color']}"><span class="cc-num">•••• •••• •••• ••••</span><span class="cc-brand">{card['brand_label']}</span><span class="cc-mark"></span></div>
          </div>
          <div class="card-title-area">
            <h3>{card['name']}</h3>
            <div class="stars">{stars_html(card['stars'])}</div>
            <p class="card-catch">{card['catch']}</p>
          </div>
        </div>
        <div class="card-specs">
          <div class="spec"><span class="spec-label">年会費</span><span class="spec-value highlight">{card['annual_fee']}</span></div>
          <div class="spec"><span class="spec-label">還元率</span><span class="spec-value{rh}">{card['reward']}</span></div>
          <div class="spec"><span class="spec-label">入会特典</span><span class="spec-value">{card['bonus']}</span></div>
          <div class="spec"><span class="spec-label">ブランド</span><span class="spec-value">{card['international']}</span></div>
        </div>
        <div class="card-merits">
{merits}
        </div>
        <div class="card-actions">
          <a href="{card['affiliate_url']}" class="btn-apply" target="_blank" rel="nofollow sponsored noopener">公式サイトで申し込む（無料）</a>
          <a href="{detail_href}" class="btn-detail">詳しく見る</a>
        </div>
      </div>
    </div>"""


# ---------- 各ページ生成 ----------
def build_index(data):
    site = data["site"]
    cards = data["cards"]
    html = head(site, f"{site['name']}｜{year_month()}おすすめクレジットカードランキング", site["description"])
    html += header(site)

    # ヒーロー
    html += f"""
<section class="hero">
  <div class="hero-bg"></div>
  <div class="container">
    <div class="hero-grid">
      <div class="hero-text">
        <p class="hero-label">✨ {year_month()} 最新版</p>
        <h1>あなたに最適な<br><span class="hl">クレジットカード</span>を<br>見つけよう</h1>
        <p class="hero-sub">ポイント還元率・年会費・特典を徹底比較。<br>{len(cards)}枚以上のカードから本当におすすめの1枚を紹介します。</p>
        <div class="hero-actions">
          <a href="#ranking" class="btn-primary">ランキングを見る</a>
          <a href="#comparison" class="btn-ghost">比較表を見る</a>
        </div>
        <div class="hero-trust">
          <span>🔒 年会費無料カード多数</span>
          <span>📊 編集部が徹底比較</span>
        </div>
      </div>
      <div class="hero-visual">{hero_card_svg()}</div>
    </div>
  </div>
</section>"""

    # 3つのポイント
    html += """
<section class="points-section">
  <div class="container">
    <h2 class="section-title">クレカ選びの3つのポイント</h2>
    <div class="points-grid">
      <div class="point-card"><div class="point-icon">💰</div><h3>ポイント還元率</h3><p>毎日の買い物でポイントが貯まります。還元率が高いほどお得。1%以上を目安に選びましょう。</p></div>
      <div class="point-card"><div class="point-icon">🎁</div><h3>特典・優待</h3><p>空港ラウンジ・旅行保険・ショッピング保険など、カードによって特典が大きく異なります。</p></div>
      <div class="point-card"><div class="point-icon">📋</div><h3>年会費</h3><p>年会費無料でも高機能なカードが増えています。特典と年会費のバランスで選びましょう。</p></div>
    </div>
  </div>
</section>"""

    # ランキング (上位5枚)
    html += f"""
<section class="ranking-section" id="ranking">
  <div class="container">
    <h2 class="section-title">おすすめクレジットカード ランキング TOP5</h2>
    <p class="section-sub">編集部が実際に調査・比較した{year_month()}最新のおすすめランキングです。</p>"""
    for i, c in enumerate(cards[:5], start=1):
        html += card_block(c, rank=i, depth=0)
    html += """
  </div>
</section>"""

    # ランキング選定基準（E-E-A-T・信頼性）
    html += """
<section class="criteria-section">
  <div class="container">
    <h2 class="section-title">ランキングの選定基準</h2>
    <p class="section-sub">当サイト編集部は、以下の6つの観点を独自に点数化して総合的にランキングを作成しています。</p>
    <div class="criteria-grid">
      <div class="criteria-item"><span class="criteria-num">01</span><h3>年会費</h3><p>永年無料か、年会費に見合う特典があるかを評価します。</p></div>
      <div class="criteria-item"><span class="criteria-num">02</span><h3>ポイント還元率</h3><p>通常還元率と、店舗ごとの上乗せ還元のお得さを評価します。</p></div>
      <div class="criteria-item"><span class="criteria-num">03</span><h3>特典・付帯保険</h3><p>旅行保険・ショッピング保険・優待などの充実度を評価します。</p></div>
      <div class="criteria-item"><span class="criteria-num">04</span><h3>セキュリティ</h3><p>ナンバーレスや不正利用補償など、安心して使えるかを評価します。</p></div>
      <div class="criteria-item"><span class="criteria-num">05</span><h3>入会キャンペーン</h3><p>新規入会で受け取れる特典・ポイントの大きさを評価します。</p></div>
      <div class="criteria-item"><span class="criteria-num">06</span><h3>使いやすさ・評判</h3><p>発行スピードや対応ブランド、利用者の評判を評価します。</p></div>
    </div>
    <p class="criteria-note">※掲載カードは金融庁の登録を受けた発行会社のクレジットカードを対象に、編集部が調査・比較しています。情報は各公式サイトでも必ずご確認ください。</p>
  </div>
</section>"""

    # 目的別
    html += """
<section class="purpose-section" id="purpose">
  <div class="container">
    <h2 class="section-title">目的・特徴から選ぶ</h2>
    <p class="section-sub">あなたの使い方やほしい特典から、ぴったりのクレジットカードを探せます。</p>
    <div class="purpose-grid">"""
    for pp in data["purposes"]:
        html += f"""
      <a href="purpose/{pp['id']}.html" class="purpose-card">
        <div class="purpose-icon">{pp['icon']}</div>
        <h3>{pp['title']}</h3>
        <p>{pp['desc']}</p>
      </a>"""
    html += """
    </div>
  </div>
</section>"""

    # 比較表 (全カード)
    html += """
<section class="comparison-section" id="comparison">
  <div class="container">
    <h2 class="section-title">クレジットカード 一覧比較表</h2>
    <div class="table-wrapper">
      <table class="comparison-table">
        <thead>
          <tr><th>カード名</th><th>年会費</th><th>還元率</th><th>入会特典</th><th>ブランド</th><th>特徴</th><th>申込</th></tr>
        </thead>
        <tbody>"""
    for idx, c in enumerate(cards):
        cls = ' class="table-highlight"' if idx == 0 else ""
        rstr = f"<strong>{c['reward']}</strong>" if c.get("reward_highlight") else c["reward"]
        html += f"""
          <tr{cls}>
            <td><a href="cards/{c['id']}.html"><strong>{c['name']}</strong></a></td>
            <td>{c['annual_fee'].replace('永年','')}</td>
            <td>{rstr}</td>
            <td>{c['bonus']}</td>
            <td>{c['international'].replace(' / ','/')}</td>
            <td>{c['feature']}</td>
            <td><a href="{c['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener" class="table-btn">申込む</a></td>
          </tr>"""
    html += """
        </tbody>
      </table>
    </div>
  </div>
</section>"""

    # 初心者ガイド
    html += """
<section class="guide-section" id="beginner">
  <div class="container">
    <h2 class="section-title">クレジットカード初心者ガイド</h2>
    <div class="guide-grid">"""
    for g in data["guides"]:
        html += f"""
      <div class="guide-card"><h3>📌 {g['q']}</h3><p>{g['a']}</p></div>"""
    html += """
    </div>
  </div>
</section>"""

    html += footer(site)
    write(os.path.join(BASE_DIR, "index.html"), html)


def build_card_pages(data):
    site = data["site"]
    cards = data["cards"]
    os.makedirs(os.path.join(BASE_DIR, "cards"), exist_ok=True)
    for c in cards:
        html = head(site, f"{c['name']}の評判・特典を徹底解説｜{site['name']}",
                    f"{c['name']}の年会費・還元率・特典・メリットデメリットを徹底解説。{c['catch']}", depth=1)
        html += header(site, depth=1)
        rh = " highlight" if c.get("reward_highlight") else ""
        merits = "\n".join(f'        <li>✅ {m}</li>' for m in c["merits"])
        demerits = "\n".join(f'        <li>⚠️ {m}</li>' for m in c.get("demerits", []))
        html += f"""
<article class="detail-page">
  <div class="container container-narrow">
    <nav class="breadcrumb"><a href="../index.html">ホーム</a> ＞ <span>{c['name']}</span></nav>
    <div class="detail-hero {c['color']}">
      <div class="card-logo-placeholder {c['color']} big"><span class="cc-num">•••• •••• •••• ••••</span><span class="cc-brand">{c['brand_label']}</span><span class="cc-mark"></span></div>
      <div>
        <h1>{c['name']}</h1>
        <div class="stars">{stars_html(c['stars'])}</div>
        <p>{c['catch']}</p>
      </div>
    </div>

    <div class="card-specs detail-specs">
      <div class="spec"><span class="spec-label">年会費</span><span class="spec-value highlight">{c['annual_fee']}</span></div>
      <div class="spec"><span class="spec-label">還元率</span><span class="spec-value{rh}">{c['reward']}</span></div>
      <div class="spec"><span class="spec-label">入会特典</span><span class="spec-value">{c['bonus']}</span></div>
      <div class="spec"><span class="spec-label">ブランド</span><span class="spec-value">{c['international']}</span></div>
    </div>

    <div class="apply-cta">
      <a href="{c['affiliate_url']}" class="btn-apply" target="_blank" rel="nofollow sponsored noopener">{c['name']}を公式サイトで申し込む（無料）</a>
    </div>

    <h2>{c['name']}の総合評価</h2>
    <p class="review-text">{c['review']}</p>

    <h2>メリット</h2>
    <ul class="merit-list">
{merits}
    </ul>

    <h2>デメリット・注意点</h2>
    <ul class="demerit-list">
{demerits}
    </ul>

    <h2>こんな人におすすめ</h2>
    <p class="review-text">👤 {c['target']}</p>

    <div class="apply-cta">
      <a href="{c['affiliate_url']}" class="btn-apply" target="_blank" rel="nofollow sponsored noopener">公式サイトで申し込む（無料）</a>
      <a href="../index.html#ranking" class="btn-detail">他のカードと比較する</a>
    </div>
  </div>
</article>"""
        html += footer(site, depth=1)
        write(os.path.join(BASE_DIR, "cards", f"{c['id']}.html"), html)


def build_purpose_pages(data):
    site = data["site"]
    os.makedirs(os.path.join(BASE_DIR, "purpose"), exist_ok=True)
    for pp in data["purposes"]:
        html = head(site, f"{pp['title']}におすすめのクレジットカード｜{site['name']}",
                    f"{pp['title']}におすすめのクレジットカードを厳選して紹介。{pp['desc']}", depth=1)
        html += header(site, depth=1)
        html += f"""
<section class="purpose-detail">
  <div class="container">
    <nav class="breadcrumb"><a href="../index.html">ホーム</a> ＞ <span>{pp['title']}</span></nav>
    <h1 class="section-title">{pp['icon']} {pp['title']}におすすめのクレジットカード</h1>
    <p class="section-sub">{pp['intro']}</p>"""
        for i, cid in enumerate(pp["card_ids"], start=1):
            c = card_by_id(data, cid)
            if c:
                html += card_block(c, rank=i, depth=1)
        html += """
  </div>
</section>"""
        html += footer(site, depth=1)
        write(os.path.join(BASE_DIR, "purpose", f"{pp['id']}.html"), html)


def build_article_pages(data):
    site = data["site"]
    os.makedirs(os.path.join(BASE_DIR, "articles"), exist_ok=True)
    # 記事一覧
    html = head(site, f"クレジットカード お役立ち記事一覧｜{site['name']}",
                "クレジットカードの選び方・還元率・年会費などお役立ち情報をまとめた記事一覧です。")
    html += header(site)
    html += """
<section class="article-list-section">
  <div class="container">
    <h1 class="section-title">お役立ち記事一覧</h1>
    <p class="section-sub">クレジットカード選びに役立つ情報をお届けします。</p>
    <div class="article-grid">"""
    for a in data["articles"]:
        html += f"""
      <a href="articles/{a['id']}.html" class="article-card">
        <div class="article-tag">記事</div>
        <h3>{a['title']}</h3>
        <p>{a['description']}</p>
        <span class="read-more">続きを読む →</span>
      </a>"""
    html += """
    </div>
  </div>
</section>"""
    html += footer(site)
    write(os.path.join(BASE_DIR, "articles.html"), html)

    # 各記事
    for a in data["articles"]:
        h = head(site, f"{a['title']}｜{site['name']}", a["description"], depth=1)
        h += header(site, depth=1)
        h += f"""
<article class="detail-page">
  <div class="container container-narrow">
    <nav class="breadcrumb"><a href="../index.html">ホーム</a> ＞ <a href="../articles.html">記事一覧</a> ＞ <span>{a['title']}</span></nav>
    <h1 class="article-title">{a['title']}</h1>
    <p class="article-date">📅 {today_str()} 更新</p>
    <p class="article-lead">{a['lead']}</p>"""
        for s in a["sections"]:
            h += f"""
    <h2>{s['h']}</h2>
    <p class="review-text">{s['p']}</p>"""
        # 記事末尾にランキング誘導
        h += """
    <div class="article-cta">
      <h3>おすすめカードはこちら</h3>
      <p>編集部おすすめのクレジットカードランキングもぜひチェックしてください。</p>
      <a href="../index.html#ranking" class="btn-primary">ランキングを見る</a>
    </div>
  </div>
</article>"""
        h += footer(site, depth=1)
        write(os.path.join(BASE_DIR, "articles", f"{a['id']}.html"), h)


def build_legal_pages(data):
    site = data["site"]
    pages = {
        "about.html": ("運営者情報", f"""
    <h2>サイト名</h2><p class="review-text">{site['name']}</p>
    <h2>運営方針</h2><p class="review-text">{site['name']}は、クレジットカードを検討している方が自分に合った1枚を見つけられるよう、年会費・ポイント還元率・特典などを公平に比較・紹介する情報メディアです。掲載情報は各カード発行会社の公式サイト等を元に編集部が調査しています。</p>
    <h2>収益について</h2><p class="review-text">本サイトはアフィリエイトプログラムによる広告収入で運営されています。詳しくは免責事項をご覧ください。</p>"""),
        "privacy.html": ("プライバシーポリシー", """
    <h2>個人情報の取り扱い</h2><p class="review-text">当サイトでは、お問い合わせの際にお名前やメールアドレスなどの個人情報をご提供いただく場合があります。取得した個人情報はお問い合わせへの対応以外の目的では利用しません。</p>
    <h2>アクセス解析ツールについて</h2><p class="review-text">当サイトでは、Googleアナリティクス等のアクセス解析ツールを利用する場合があります。これらはトラフィックデータ収集のためにCookieを使用します。このデータは匿名で収集され、個人を特定するものではありません。</p>
    <h2>広告について</h2><p class="review-text">当サイトでは第三者配信の広告サービスを利用する場合があります。広告配信事業者はユーザーの興味に応じた広告を表示するためCookieを使用することがあります。</p>"""),
        "disclaimer.html": ("免責事項", """
    <h2>掲載情報について</h2><p class="review-text">当サイトに掲載している情報の正確性には万全を期しておりますが、内容を保証するものではありません。クレジットカードの年会費・還元率・特典・キャンペーン等は変更される場合があります。お申し込みの際は必ず各カード公式サイトで最新情報をご確認ください。</p>
    <h2>アフィリエイトについて</h2><p class="review-text">当サイトはアフィリエイトプログラムに参加しており、掲載リンクを経由してカードが発行された場合、当サイトに成果報酬が支払われることがあります。ただし掲載順位や評価は報酬額のみで決定するものではなく、編集部の調査に基づいています。</p>
    <h2>損害の責任について</h2><p class="review-text">当サイトの情報を利用して生じたいかなる損害についても、当サイトは一切の責任を負いかねます。最終的なお申し込みの判断はご自身の責任で行ってください。</p>"""),
        "contact.html": ("お問い合わせ", """
    <h2>お問い合わせについて</h2><p class="review-text">当サイトへのご質問・掲載情報の誤りのご指摘・取材や提携のご依頼などは、下記メールアドレスまでご連絡ください。</p>
    <p class="review-text">📧 example@example.com<br>（公開時にあなたの連絡先に差し替えてください）</p>
    <p class="review-text">内容を確認のうえ、順次対応させていただきます。返信までお時間をいただく場合がございますのでご了承ください。</p>"""),
    }
    for fname, (title, body) in pages.items():
        html = head(site, f"{title}｜{site['name']}", f"{site['name']}の{title}ページです。")
        html += header(site)
        html += f"""
<article class="detail-page">
  <div class="container container-narrow">
    <nav class="breadcrumb"><a href="index.html">ホーム</a> ＞ <span>{title}</span></nav>
    <h1 class="article-title">{title}</h1>
    {body}
  </div>
</article>"""
        html += footer(site)
        write(os.path.join(BASE_DIR, fname), html)


def build_sitemap(data):
    site = data["site"]
    base = site.get("base_url", "").rstrip("/")
    urls = ["index.html", "articles.html", "about.html", "privacy.html", "disclaimer.html", "contact.html"]
    urls += [f"cards/{c['id']}.html" for c in data["cards"]]
    urls += [f"purpose/{p['id']}.html" for p in data["purposes"]]
    urls += [f"articles/{a['id']}.html" for a in data["articles"]]
    today = datetime.date.today().isoformat()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        loc = f"{base}/{u}" if base else u
        xml += f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>\n"
    xml += "</urlset>\n"
    write(os.path.join(BASE_DIR, "sitemap.xml"), xml)

    robots = "User-agent: *\nAllow: /\n"
    if base:
        robots += f"Sitemap: {base}/sitemap.xml\n"
    write(os.path.join(BASE_DIR, "robots.txt"), robots)


def write(path, content):
    """BOMなしUTF-8で書き出す"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  生成: {os.path.relpath(path, BASE_DIR)}")


def main():
    print(f"=== サイト自動生成開始 {today_str()} ===")
    data = load_data()
    build_index(data)
    build_card_pages(data)
    build_purpose_pages(data)
    build_article_pages(data)
    build_legal_pages(data)
    build_sitemap(data)
    n = 6 + len(data["cards"]) + len(data["purposes"]) + len(data["articles"])
    print(f"=== 完了: 約{n}ページを生成しました ===")


if __name__ == "__main__":
    main()
