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


def fmt_date(iso):
    """ISO日付(2026-06-07)を日本語表記(2026年6月7日)に変換"""
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{y}年{m}月{d}日"


def article_date(a):
    """記事の公開日(ISO)。未設定なら今日"""
    return a.get("published", datetime.date.today().isoformat())


def publish_from_queue(data):
    """記事キューから1日1本だけ自動公開する。公開したらcards.jsonへ書き戻す"""
    queue = data.get("article_queue", [])
    if not queue:
        return
    today = datetime.date.today().isoformat()
    if any(a.get("published") == today for a in data["articles"]):
        return  # 今日はすでに公開済み
    art = queue.pop(0)
    art["published"] = today
    data["articles"].append(art)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"記事キューから自動公開: {art['id']}（残り{len(queue)}本）")


def card_by_id(data, cid):
    for c in data["cards"]:
        if c["id"] == cid:
            return c
    return None


def card_cats(card):
    """比較表の絞り込み用カテゴリタグを返す"""
    cats = []
    blob = card.get("name", "") + card.get("brand_label", "") + card.get("feature", "")
    if "永年無料" in card.get("annual_fee", ""):
        cats.append("free")
    if card.get("reward_highlight"):
        cats.append("highreward")
    if "ゴールド" in blob or "GOLD" in blob or card.get("color") == "amber":
        cats.append("gold")
    if "プラチナ" in blob or "PLATINUM" in blob or card.get("color") == "platinum":
        cats.append("platinum")
    if "マイル" in card.get("reward", "") or "マイル" in card.get("feature", ""):
        cats.append("mile")
    if "即日" in card.get("feature", "") or "即日" in card.get("catch", ""):
        cats.append("instant")
    return " ".join(cats)


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
def head(site, title, description, depth=0, path=""):
    prefix = "" if depth == 0 else "../"
    base = site.get("base_url", "").rstrip("/")
    canonical_url = f"{base}/{path}" if path != "index.html" else f"{base}/"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{description}">
  <title>{title}</title>
  <link rel="canonical" href="{canonical_url}">
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{base}/ogp.png">
  <meta property="og:site_name" content="{site['name']}">
  <meta property="og:locale" content="ja_JP">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{base}/ogp.png">
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
        <a href="{p}simulator.html">シミュレーター</a>
        <a href="{p}securities.html">証券・NISA</a>
        <a href="{p}glossary.html">用語集</a>
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
        <a href="{p}securities.html">ネット証券・NISA</a>
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
    html = head(site, f"{site['name']}｜{year_month()}おすすめクレジットカードランキング", site["description"], path="index.html")
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

    # かんたんカード診断
    diag_map = {"free": "smbc-card", "highreward": "recruit-card", "mile": "jal-card",
                "status": "amex-gold", "docomo": "d-card", "daily": "smbc-card"}
    diag_data = {}
    for k, cid in diag_map.items():
        c = card_by_id(data, cid)
        if c:
            diag_data[k] = {"name": c["name"], "catch": c["catch"],
                            "detail": f"cards/{cid}.html", "url": c["affiliate_url"]}
    html += """
<section class="diagnosis-section">
  <div class="container">
    <h2 class="section-title">かんたんカード診断</h2>
    <p class="section-sub">いちばん重視するポイントを選ぶだけ。あなたにおすすめの1枚を提案します。</p>
    <div class="diag-options">
      <button class="diag-btn" data-key="free">💴 年会費無料</button>
      <button class="diag-btn" data-key="highreward">📈 とにかく高還元</button>
      <button class="diag-btn" data-key="mile">✈️ マイル・旅行</button>
      <button class="diag-btn" data-key="status">✨ ステータス・特典</button>
      <button class="diag-btn" data-key="docomo">📱 ドコモユーザー</button>
      <button class="diag-btn" data-key="daily">🛍️ コンビニ・普段使い</button>
    </div>
    <div class="diag-result" id="diag-result" style="display:none;"></div>
  </div>
  <script>
  var DIAG=""" + json.dumps(diag_data, ensure_ascii=False) + """;
  (function(){
    var btns=document.querySelectorAll('.diag-btn');
    var res=document.getElementById('diag-result');
    btns.forEach(function(b){
      b.addEventListener('click',function(){
        btns.forEach(function(x){x.classList.remove('active');});
        b.classList.add('active');
        var d=DIAG[b.getAttribute('data-key')];
        if(!d){return;}
        res.innerHTML='<div class="diag-card-label">🎯 あなたへのおすすめ</div>'
          +'<h3>'+d.name+'</h3><p class="diag-catch">'+d.catch+'</p>'
          +'<div class="diag-card-actions"><a href="'+d.url+'" target="_blank" rel="nofollow sponsored noopener" class="btn-apply">公式サイトで申し込む（無料）</a>'
          +'<a href="'+d.detail+'" class="btn-detail">詳しく見る</a></div>';
        res.style.display='block';
      });
    });
  })();
  </script>
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
    <p class="section-sub">掲載カードを一覧でまとめて比較。条件で絞り込み、表内をスクロールできます。</p>
    <div class="table-filters">
      <button class="filter-btn active" data-filter="all">すべて</button>
      <button class="filter-btn" data-filter="free">年会費無料</button>
      <button class="filter-btn" data-filter="highreward">高還元</button>
      <button class="filter-btn" data-filter="gold">ゴールド</button>
      <button class="filter-btn" data-filter="platinum">プラチナ</button>
      <button class="filter-btn" data-filter="mile">マイル</button>
      <button class="filter-btn" data-filter="instant">即日発行</button>
    </div>
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
          <tr{cls} data-cat="{card_cats(c)}">
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
    <p class="table-scroll-hint">↕ 表内を上下にスクロールして全""" + str(len(cards)) + """枚を比較できます</p>
  </div>
  <script>
  (function(){
    var btns=document.querySelectorAll('.table-filters .filter-btn');
    var rows=document.querySelectorAll('.comparison-table tbody tr');
    btns.forEach(function(b){
      b.addEventListener('click',function(){
        btns.forEach(function(x){x.classList.remove('active');});
        b.classList.add('active');
        var f=b.getAttribute('data-filter');
        rows.forEach(function(r){
          var cat=' '+(r.getAttribute('data-cat')||'')+' ';
          r.style.display=(f==='all'||cat.indexOf(' '+f+' ')>=0)?'':'none';
        });
      });
    });
  })();
  </script>
</section>"""

    # 証券・NISA誘導（クレカ積立）
    html += """
<section class="securities-teaser">
  <div class="container">
    <div class="teaser-box">
      <div class="teaser-text">
        <h2>💹 クレカ積立でポイントを貯めよう</h2>
        <p>クレジットカードで投資信託を積み立てると、ポイントが貯まってお得。NISA対応の人気ネット証券を比較しました。</p>
      </div>
      <a href="securities.html" class="btn-primary">ネット証券・NISAを見る →</a>
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

    # トップページの記事セクション
    html += """
<section class="home-articles-section">
  <div class="container">
    <h2 class="section-title">お役立ち記事</h2>
    <p class="section-sub">クレジットカード選びに役立つ情報を発信しています。</p>
    <div class="article-grid">"""
    for a in sorted(data["articles"], key=article_date, reverse=True)[:6]:
        html += f"""
      <a href="articles/{a['id']}.html" class="article-card">
        <div class="article-meta"><span class="article-tag">記事</span><span class="article-card-date">📅 {fmt_date(article_date(a))} 公開</span></div>
        <h3>{a['title']}</h3>
        <p>{a['description']}</p>
        <span class="read-more">続きを読む →</span>
      </a>"""
    html += """
    </div>
    <div class="home-articles-more"><a href="articles.html" class="btn-detail">記事をもっと見る →</a></div>
  </div>
</section>"""

    base = site.get("base_url", "").rstrip("/")
    html += f"""
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebSite","name":"{site['name']}","url":"{base}/","description":"{site['description']}","inLanguage":"ja"}}
</script>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Organization","name":"{site['name']}","url":"{base}/","description":"クレジットカードを年会費・還元率・特典で比較・紹介する情報メディア"}}
</script>"""
    faq = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": g["q"],
                           "acceptedAnswer": {"@type": "Answer", "text": g["a"]}} for g in data["guides"]]}
    html += '\n<script type="application/ld+json">\n' + json.dumps(faq, ensure_ascii=False) + '\n</script>'

    html += footer(site)
    write(os.path.join(BASE_DIR, "index.html"), html)


def build_card_pages(data):
    site = data["site"]
    cards = data["cards"]
    os.makedirs(os.path.join(BASE_DIR, "cards"), exist_ok=True)
    for c in cards:
        html = head(site, f"{c['name']}の評判・特典を徹底解説｜{site['name']}",
                    f"{c['name']}の年会費・還元率・特典・メリットデメリットを徹底解説。{c['catch']}", depth=1, path=f"cards/{c['id']}.html")
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
        cbase = site.get("base_url", "").rstrip("/")
        cbc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{cbase}/"},
            {"@type": "ListItem", "position": 2, "name": c["name"], "item": f"{cbase}/cards/{c['id']}.html"}]}
        html += '\n<script type="application/ld+json">\n' + json.dumps(cbc, ensure_ascii=False) + '\n</script>'
        html += footer(site, depth=1)
        write(os.path.join(BASE_DIR, "cards", f"{c['id']}.html"), html)


def build_purpose_pages(data):
    site = data["site"]
    os.makedirs(os.path.join(BASE_DIR, "purpose"), exist_ok=True)
    for pp in data["purposes"]:
        html = head(site, f"{pp['title']}におすすめのクレジットカード｜{site['name']}",
                    f"{pp['title']}におすすめのクレジットカードを厳選して紹介。{pp['desc']}", depth=1, path=f"purpose/{pp['id']}.html")
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
                "クレジットカードの選び方・還元率・年会費などお役立ち情報をまとめた記事一覧です。", path="articles.html")
    html += header(site)
    html += """
<section class="article-list-section">
  <div class="container">
    <h1 class="section-title">お役立ち記事一覧</h1>
    <p class="section-sub">クレジットカード選びに役立つ情報をお届けします。</p>
    <div class="article-grid">"""
    for a in sorted(data["articles"], key=article_date, reverse=True):
        html += f"""
      <a href="articles/{a['id']}.html" class="article-card">
        <div class="article-meta"><span class="article-tag">記事</span><span class="article-card-date">📅 {fmt_date(article_date(a))} 公開</span></div>
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
        h = head(site, f"{a['title']}｜{site['name']}", a["description"], depth=1, path=f"articles/{a['id']}.html")
        h += header(site, depth=1)
        h += f"""
<article class="detail-page">
  <div class="container container-narrow">
    <nav class="breadcrumb"><a href="../index.html">ホーム</a> ＞ <a href="../articles.html">記事一覧</a> ＞ <span>{a['title']}</span></nav>
    <h1 class="article-title">{a['title']}</h1>
    <p class="article-date">📅 {fmt_date(article_date(a))} 公開</p>
    <p class="article-lead">{a['lead']}</p>"""
        for s in a["sections"]:
            h += f"""
    <h2>{s['h']}</h2>
    <p class="review-text">{s['p']}</p>"""
        # 関連記事(リスト上の前後3本・内部リンク強化)
        arts = data["articles"]
        idx = arts.index(a)
        related = [arts[(idx + k) % len(arts)] for k in (1, 2, 3)]
        h += """
    <div class="related-articles">
      <h2>関連記事</h2>"""
        for r in related:
            h += f"""
      <a href="{r['id']}.html" class="related-link">📄 {r['title']}</a>"""
        h += """
    </div>"""
        # 記事末尾にランキング誘導
        h += """
    <div class="article-cta">
      <h3>おすすめカードはこちら</h3>
      <p>編集部おすすめのクレジットカードランキングもぜひチェックしてください。</p>
      <a href="../index.html#ranking" class="btn-primary">ランキングを見る</a>
    </div>
  </div>
</article>"""
        base = site.get("base_url", "").rstrip("/")
        iso = article_date(a)
        h += f"""
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{a['title']}","description":"{a['description']}","datePublished":"{iso}","dateModified":"{iso}","inLanguage":"ja","author":{{"@type":"Organization","name":"{site['name']}編集部"}},"publisher":{{"@type":"Organization","name":"{site['name']}"}},"mainEntityOfPage":"{base}/articles/{a['id']}.html"}}
</script>"""
        bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{base}/"},
            {"@type": "ListItem", "position": 2, "name": "記事一覧", "item": f"{base}/articles.html"},
            {"@type": "ListItem", "position": 3, "name": a["title"], "item": f"{base}/articles/{a['id']}.html"}]}
        h += '\n<script type="application/ld+json">\n' + json.dumps(bc, ensure_ascii=False) + '\n</script>'
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
    <h2>アクセス解析ツールについて</h2><p class="review-text">当サイトでは、Googleによるアクセス解析ツール「Googleアナリティクス（GA4）」を利用しています。Googleアナリティクスはトラフィックデータの収集のためにCookieを使用します。このデータは匿名で収集されており、個人を特定するものではありません。この機能はCookieを無効にすることで収集を拒否できますので、お使いのブラウザの設定をご確認ください。Googleによるデータの取り扱いの詳細は「<a href="https://policies.google.com/technologies/partner-sites?hl=ja" target="_blank" rel="noopener">Googleのサービスを使用するサイトやアプリから収集した情報のGoogleによる使用</a>」および「<a href="https://marketingplatform.google.com/about/analytics/terms/jp/" target="_blank" rel="noopener">Googleアナリティクス利用規約</a>」をご覧ください。また、Googleアナリティクスによる計測を無効にしたい場合は「<a href="https://tools.google.com/dlpage/gaoptout?hl=ja" target="_blank" rel="noopener">Googleアナリティクス オプトアウト アドオン</a>」をご利用いただけます。</p>
    <h2>広告・アフィリエイトプログラムについて</h2><p class="review-text">当サイトは、アフィリエイトプログラム（A8.net、afb等のアフィリエイト・サービス・プロバイダ）に参加しています。当サイトのリンクを経由して商品・サービスの申し込みが行われた場合、提携する広告主から当サイトに報酬が支払われることがあります。アフィリエイトプログラムでは、成果の計測のためにCookieが使用されます。Cookieにより収集される情報に、個人を特定する情報は含まれません。</p>
    <h2>免責</h2><p class="review-text">本ポリシーの内容は、法令の変更やサービスの変更に応じて、予告なく改定されることがあります。重要な変更がある場合は本ページにてお知らせします。</p>"""),
        "disclaimer.html": ("免責事項", """
    <h2>掲載情報について</h2><p class="review-text">当サイトに掲載している情報の正確性には万全を期しておりますが、内容を保証するものではありません。クレジットカードの年会費・還元率・特典・キャンペーン等は変更される場合があります。お申し込みの際は必ず各カード公式サイトで最新情報をご確認ください。</p>
    <h2>アフィリエイトについて</h2><p class="review-text">当サイトはアフィリエイトプログラムに参加しており、掲載リンクを経由してカードが発行された場合、当サイトに成果報酬が支払われることがあります。ただし掲載順位や評価は報酬額のみで決定するものではなく、編集部の調査に基づいています。</p>
    <h2>損害の責任について</h2><p class="review-text">当サイトの情報を利用して生じたいかなる損害についても、当サイトは一切の責任を負いかねます。最終的なお申し込みの判断はご自身の責任で行ってください。</p>"""),
        "contact.html": ("お問い合わせ", """
    <h2>お問い合わせについて</h2><p class="review-text">当サイトへのご質問・掲載情報の誤りのご指摘・取材や提携のご依頼などは、下記メールアドレスまでご連絡ください。</p>
    <p class="review-text">📧 crecalabo.info@gmail.com</p>
    <p class="review-text">内容を確認のうえ、順次対応させていただきます。返信までお時間をいただく場合がございますのでご了承ください。</p>"""),
    }
    for fname, (title, body) in pages.items():
        html = head(site, f"{title}｜{site['name']}", f"{site['name']}の{title}ページです。", path=fname)
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


def broker_block(b, rank=None, depth=0):
    p = "" if depth == 0 else "../"
    badge = f'<div class="rank-badge">{rank}位</div>' if rank else ""
    rank_class = f"rank-{rank}" if rank else "rank-x"
    merits = "\n".join(f'          <p class="merit">✅ {m}</p>' for m in b["merits"])
    return f"""
    <div class="card-item {rank_class}">
      {badge}
      <div class="card-body">
        <div class="card-header-row">
          <div class="card-logo-area"><div class="broker-logo {b['color']}">{b['brand_label']}</div></div>
          <div class="card-title-area">
            <h3>{b['name']}</h3>
            <div class="stars">{stars_html(b['stars'])}</div>
            <p class="card-catch">{b['catch']}</p>
          </div>
        </div>
        <div class="card-specs">
          <div class="spec"><span class="spec-label">手数料</span><span class="spec-value highlight">{b['fee']}</span></div>
          <div class="spec"><span class="spec-label">NISA</span><span class="spec-value">{b['nisa']}</span></div>
          <div class="spec"><span class="spec-label">クレカ積立</span><span class="spec-value">{b['credit']}</span></div>
          <div class="spec"><span class="spec-label">取扱商品</span><span class="spec-value">{b['products']}</span></div>
        </div>
        <div class="card-merits">
{merits}
        </div>
        <div class="card-actions">
          <a href="{b['affiliate_url']}" class="btn-apply" target="_blank" rel="nofollow sponsored noopener">公式サイトで口座開設（無料）</a>
          <a href="{p}securities/{b['id']}.html" class="btn-detail">詳しく見る</a>
        </div>
      </div>
    </div>"""


def build_securities(data):
    site = data["site"]
    brokers = data.get("brokers", [])
    if not brokers:
        return
    os.makedirs(os.path.join(BASE_DIR, "securities"), exist_ok=True)
    # 一覧ページ
    html = head(site, f"ネット証券・NISA口座おすすめ比較｜{site['name']}",
                "クレカ積立に対応したネット証券・NISA口座を手数料・ポイント還元で比較。おすすめの証券会社を紹介します。", path="securities.html")
    html += header(site)
    html += """
<section class="securities-section">
  <div class="container">
    <h1 class="section-title">ネット証券・NISA口座 おすすめ比較</h1>
    <p class="section-sub">クレジットカードで投資信託を積み立てる「クレカ積立」に対応したネット証券を比較。手数料無料・ポイント還元・NISA対応で選べる人気5社を紹介します。</p>"""
    for i, b in enumerate(brokers, start=1):
        html += broker_block(b, rank=i, depth=0)
    html += """
    <h2 class="section-title" style="margin-top:54px;">ネット証券 比較表</h2>
    <div class="table-wrapper">
      <table class="comparison-table">
        <thead><tr><th>証券会社</th><th>手数料</th><th>NISA</th><th>クレカ積立</th><th>取扱商品</th><th>口座開設</th></tr></thead>
        <tbody>"""
    for idx, b in enumerate(brokers):
        cls = ' class="table-highlight"' if idx == 0 else ""
        html += f"""
          <tr{cls}>
            <td><a href="securities/{b['id']}.html"><strong>{b['name']}</strong></a></td>
            <td>{b['fee']}</td>
            <td>{b['nisa']}</td>
            <td>{b['credit']}</td>
            <td>{b['products']}</td>
            <td><a href="{b['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener" class="table-btn">開設</a></td>
          </tr>"""
    html += """
        </tbody>
      </table>
    </div>
    <p class="table-scroll-hint">※クレカ積立は、当サイト掲載のクレジットカードと組み合わせるとポイントが貯まります。</p>

    <div class="securities-guide">
      <h2 class="section-title" style="margin-top:54px;">ネット証券の選び方 3つのポイント</h2>
      <div class="criteria-grid">
        <div class="criteria-item"><h3>① 手数料の安さ</h3><p class="review-text">国内株式の売買手数料が無料の証券会社が増えています。コストは長期投資のリターンに直結するため、手数料体系は必ず確認しましょう。投資信託は購入時手数料無料(ノーロード)のものを選ぶのが基本です。</p></div>
        <div class="criteria-item"><h3>② クレカ積立の還元率</h3><p class="review-text">投資信託の積立をクレジットカードで支払うと、0.5〜1%程度のポイントが貯まります。自分が使っているカード・ポイント経済圏に合った証券会社を選ぶと、効率よくポイントが貯まります。</p></div>
        <div class="criteria-item"><h3>③ 取扱商品とNISA対応</h3><p class="review-text">投資信託の本数、米国株・外国株の取扱い、新NISA・iDeCoへの対応状況をチェック。初心者は、低コストのインデックスファンドが揃っているかを基準にすると失敗しにくくなります。</p></div>
      </div>

      <h2 class="section-title" style="margin-top:48px;">用語ミニ解説</h2>
      <div class="term-box">
        <p class="review-text"><strong>新NISA</strong>…投資の利益が非課税になる制度。年間最大360万円、生涯1,800万円まで非課税で投資できます。</p>
        <p class="review-text"><strong>クレカ積立</strong>…投資信託の積立をクレジットカードで決済し、ポイントを貯めながら投資する方法。月10万円まで対応。</p>
        <p class="review-text"><strong>iDeCo</strong>…私的年金制度。掛金が全額所得控除になり節税できますが、原則60歳まで引き出せません。</p>
        <p class="review-text"><strong>インデックスファンド</strong>…日経平均やS&P500などの指数に連動する投資信託。低コストで分散投資でき、初心者の定番です。</p>
      </div>

      <h2 class="section-title" style="margin-top:48px;">よくある質問（FAQ）</h2>
      <div class="faq-list">
SEC_FAQ_PLACEHOLDER
      </div>
      <p class="review-text" style="margin-top:24px;">▶ <a href="articles/shin-nisa-hajimekata.html">新NISAの始め方完全ガイド</a>／<a href="articles/kureka-tsumitate.html">クレカ積立とは?</a> もあわせてご覧ください。</p>
    </div>
  </div>
</section>"""
    sec_faqs = [
        ("ネット証券はどこも同じですか?", "手数料・取扱商品・クレカ積立の還元率・ポイントの種類が会社ごとに異なります。普段貯めているポイント(楽天・Vポイントなど)や使っているクレジットカードに合わせて選ぶと、効率よくポイントが貯まります。"),
        ("証券口座の開設にお金はかかりますか?", "口座開設・口座維持は無料の証券会社がほとんどです。本人確認書類とマイナンバーがあれば、スマホから10分程度で申し込めます。"),
        ("新NISA口座は複数の証券会社で持てますか?", "NISA口座は1人1口座のみです。年単位で金融機関を変更できますが手続きに手間がかかるため、長く使う前提で最初の1社を選ぶことが大切です。"),
        ("クレカ積立は本当にお得ですか?", "現金での積立ではポイントは付きませんが、クレカ積立なら決済額の0.5〜1%程度のポイントが貯まります。同じ金額を投資してもポイント分だけお得になるため、対応カードを持っているなら活用をおすすめします。"),
        ("投資初心者は何から始めればいいですか?", "まずはネット証券で口座を開き、新NISAのつみたて投資枠で低コストのインデックスファンドを少額から積み立てるのが定番です。不安な方はポイント投資から試すのもよいでしょう。"),
    ]
    faq_html = "\n".join(
        f'        <div class="faq-item"><p class="faq-q">Q. {q}</p><p class="faq-a">A. {a}</p></div>'
        for q, a in sec_faqs)
    html = html.replace("SEC_FAQ_PLACEHOLDER", faq_html)
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in sec_faqs]}
    html += '\n<script type="application/ld+json">\n' + json.dumps(faq_ld, ensure_ascii=False) + '\n</script>'
    html += footer(site)
    write(os.path.join(BASE_DIR, "securities.html"), html)

    # 各証券の詳細ページ
    base = site.get("base_url", "").rstrip("/")
    for b in brokers:
        merits = "\n".join(f'        <li>✅ {m}</li>' for m in b["merits"])
        demerits = "\n".join(f'        <li>⚠️ {m}</li>' for m in b.get("demerits", []))
        h = head(site, f"{b['name']}の特徴・評判・クレカ積立｜{site['name']}",
                 f"{b['name']}の手数料・取扱商品・NISA・クレカ積立を解説。{b['catch']}", depth=1, path=f"securities/{b['id']}.html")
        h += header(site, depth=1)
        h += f"""
<article class="detail-page">
  <div class="container container-narrow">
    <nav class="breadcrumb"><a href="../index.html">ホーム</a> ＞ <a href="../securities.html">ネット証券・NISA</a> ＞ <span>{b['name']}</span></nav>
    <div class="detail-hero {b['color']}">
      <div class="broker-logo {b['color']} big">{b['brand_label']}</div>
      <div>
        <h1>{b['name']}</h1>
        <div class="stars">{stars_html(b['stars'])}</div>
        <p>{b['catch']}</p>
      </div>
    </div>
    <div class="card-specs detail-specs">
      <div class="spec"><span class="spec-label">手数料</span><span class="spec-value highlight">{b['fee']}</span></div>
      <div class="spec"><span class="spec-label">NISA</span><span class="spec-value">{b['nisa']}</span></div>
      <div class="spec"><span class="spec-label">クレカ積立</span><span class="spec-value">{b['credit']}</span></div>
      <div class="spec"><span class="spec-label">取扱商品</span><span class="spec-value">{b['products']}</span></div>
    </div>
    <div class="apply-cta">
      <a href="{b['affiliate_url']}" class="btn-apply" target="_blank" rel="nofollow sponsored noopener">{b['name']}で口座開設（無料）</a>
    </div>
    <h2>{b['name']}の総合評価</h2>
    <p class="review-text">{b['review']}</p>
    <h2>メリット</h2>
    <ul class="merit-list">
{merits}
    </ul>
    <h2>デメリット・注意点</h2>
    <ul class="demerit-list">
{demerits}
    </ul>
    <h2>こんな人におすすめ</h2>
    <p class="review-text">👤 {b['target']}</p>
    <div class="apply-cta">
      <a href="{b['affiliate_url']}" class="btn-apply" target="_blank" rel="nofollow sponsored noopener">公式サイトで口座開設（無料）</a>
      <a href="../securities.html" class="btn-detail">他の証券会社と比較する</a>
    </div>
  </div>
</article>"""
        bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{base}/"},
            {"@type": "ListItem", "position": 2, "name": "ネット証券・NISA", "item": f"{base}/securities.html"},
            {"@type": "ListItem", "position": 3, "name": b["name"], "item": f"{base}/securities/{b['id']}.html"}]}
        h += '\n<script type="application/ld+json">\n' + json.dumps(bc, ensure_ascii=False) + '\n</script>'
        h += footer(site, depth=1)
        write(os.path.join(BASE_DIR, "securities", f"{b['id']}.html"), h)


def build_simulator(data):
    """ポイント還元シミュレーター（毎月の利用額から年間獲得ポイントを概算）"""
    site = data["site"]
    cards = [c for c in data["cards"] if c.get("sim_rate")]
    if not cards:
        return
    # JSに渡すカードデータ
    sim_data = [{"id": c["id"], "name": c["name"], "color": c.get("color", "gray"),
                 "rate": c["sim_rate"], "grade": c.get("grade", "一般"),
                 "fee": c.get("annual_fee", ""), "url": c.get("affiliate_url", "#")} for c in cards]
    sim_json = json.dumps(sim_data, ensure_ascii=False)
    html = head(site, f"クレジットカード ポイント還元シミュレーター｜{site['name']}",
                "毎月のカード利用額を入力するだけで、各クレジットカードで年間どれだけポイントが貯まるかを概算できる無料シミュレーターです。",
                path="simulator.html")
    html += header(site)
    html += """
<section class="simulator-section">
  <div class="container container-narrow">
    <h1 class="section-title">ポイント還元シミュレーター</h1>
    <p class="section-sub">毎月のカード利用額を入力すると、主要カードで年間どれくらいポイントが貯まるかを概算します。</p>
    <div class="sim-box">
      <label class="sim-label" for="sim-spend">毎月のカード利用額（円）</label>
      <input type="number" id="sim-spend" class="sim-input" value="50000" min="0" step="1000" inputmode="numeric">
      <div class="sim-presets">
        <button type="button" class="sim-preset" data-v="30000">3万円</button>
        <button type="button" class="sim-preset" data-v="50000">5万円</button>
        <button type="button" class="sim-preset" data-v="80000">8万円</button>
        <button type="button" class="sim-preset" data-v="120000">12万円</button>
      </div>
      <div class="sim-grade-label">カードの種類</div>
      <div class="sim-grades">
        <button type="button" class="sim-grade active" data-g="すべて">すべて</button>
        <button type="button" class="sim-grade" data-g="一般">一般</button>
        <button type="button" class="sim-grade" data-g="ゴールド">ゴールド</button>
        <button type="button" class="sim-grade" data-g="プラチナ">プラチナ</button>
      </div>
      <button type="button" id="sim-run" class="btn-primary sim-run">年間ポイントを計算する</button>
    </div>
    <div id="sim-result" class="sim-result"></div>
    <p class="sim-note">※基本還元率での概算です。対象店舗でのボーナス還元・キャンペーンは含みません。<strong>ゴールド・プラチナは年会費がかかります</strong>（各行に表示）。年会費を上回る還元・特典があるかで判断しましょう。最新の還元率は各カード公式サイトでご確認ください。</p>
  </div>
</section>
<script>
const SIM_CARDS = SIM_DATA_PLACEHOLDER;
let SIM_GRADE = 'すべて';
const yen = n => n.toLocaleString('ja-JP');
function runSim(){
  const spend = Math.max(0, parseInt(document.getElementById('sim-spend').value||'0',10));
  const annual = spend * 12;
  const pool = SIM_CARDS.filter(c => SIM_GRADE === 'すべて' || c.grade === SIM_GRADE);
  const rows = pool.map(c => ({...c, pts: Math.round(annual * c.rate / 100)}))
    .sort((a,b)=> b.pts - a.pts);
  const el = document.getElementById('sim-result');
  if(!spend){ el.innerHTML = '<p class="sim-empty">金額を入力して計算してください。</p>'; return; }
  if(!rows.length){ el.innerHTML = '<p class="sim-empty">該当するカードがありません。</p>'; return; }
  let h = '<h2 class="sim-result-title">年間 '+yen(annual)+'円 の利用での獲得ポイント概算</h2>';
  h += '<div class="sim-rows">';
  rows.forEach((c,i)=>{
    const feeTag = (c.grade !== '一般' && c.fee) ? '<span class="sim-fee">年会費 '+c.fee+'</span>' : '';
    h += '<div class="sim-row">'
      + '<span class="sim-rank">'+(i+1)+'</span>'
      + '<span class="sim-logo '+c.color+'">'+c.name.slice(0,2)+'</span>'
      + '<span class="sim-name">'+c.name+'<small>還元率 '+c.rate+'%'+(c.grade!=='一般'?'・'+c.grade:'')+'</small>'+feeTag+'</span>'
      + '<span class="sim-pts">約'+yen(c.pts)+'<small>円分/年</small></span>'
      + '<a class="sim-apply" href="'+c.url+'" target="_blank" rel="nofollow sponsored noopener">公式</a>'
      + '</div>';
  });
  h += '</div>';
  el.innerHTML = h;
}
document.getElementById('sim-run').addEventListener('click', runSim);
document.querySelectorAll('.sim-preset').forEach(b=> b.addEventListener('click', ()=>{
  document.getElementById('sim-spend').value = b.dataset.v; runSim();
}));
document.querySelectorAll('.sim-grade').forEach(b=> b.addEventListener('click', ()=>{
  document.querySelectorAll('.sim-grade').forEach(x=> x.classList.remove('active'));
  b.classList.add('active'); SIM_GRADE = b.dataset.g; runSim();
}));
runSim();
</script>"""
    html = html.replace("SIM_DATA_PLACEHOLDER", sim_json)
    html += footer(site)
    write(os.path.join(BASE_DIR, "simulator.html"), html)


KANA_ROWS = [
    ("あ", "あいうえおぁぃぅぇぉ"),
    ("か", "かきくけこがぎぐげご"),
    ("さ", "さしすせそざじずぜぞ"),
    ("た", "たちつてとだぢづでどっ"),
    ("な", "なにぬねの"),
    ("は", "はひふへほばびぶべぼぱぴぷぺぽ"),
    ("ま", "まみむめも"),
    ("や", "やゆよゃゅょ"),
    ("ら", "らりるれろ"),
    ("わ", "わをんゐゑ"),
]


def kana_row(reading):
    """読み仮名の先頭文字から五十音の行（あ/か/…）を返す"""
    if not reading:
        return "他"
    c = reading[0]
    # カタカナ→ひらがな正規化
    if "ァ" <= c <= "ヶ":
        c = chr(ord(c) - 0x60)
    for row, chars in KANA_ROWS:
        if c in chars:
            return row
    return "他"


def build_glossary(data):
    """クレジットカード用語集"""
    site = data["site"]
    terms = data.get("glossary", [])
    if not terms:
        return
    html = head(site, f"クレジットカード用語集｜{site['name']}",
                "クレジットカードの基本用語（還元率・リボ払い・国際ブランド・クレカ積立など）を初心者向けにわかりやすく解説した用語集です。",
                path="glossary.html")
    html += header(site)
    # 五十音順に並べ、存在する行だけ絞り込みボタンを出す
    terms_sorted = sorted(terms, key=lambda t: (
        [r for r, _ in KANA_ROWS].index(kana_row(t.get("reading", ""))) if kana_row(t.get("reading", "")) in [r for r, _ in KANA_ROWS] else 99,
        t.get("reading", "")))
    present_rows = [r for r, _ in KANA_ROWS if any(kana_row(t.get("reading", "")) == r for t in terms_sorted)]
    row_btns = '<button type="button" class="glossary-row-btn active" data-row="すべて">すべて</button>'
    row_btns += "".join(f'<button type="button" class="glossary-row-btn" data-row="{r}">{r}行</button>' for r in present_rows)
    html += f"""
<section class="glossary-section">
  <div class="container container-narrow">
    <h1 class="section-title">クレジットカード用語集</h1>
    <p class="section-sub">カード選びでよく出てくる用語を、初心者にもわかりやすく解説します。行で絞り込めます。</p>
    <input type="text" id="glossary-search" class="glossary-search" placeholder="用語を検索（例：還元率、リボ）">
    <div class="glossary-rows">{row_btns}</div>
    <div class="glossary-list">"""
    for t in terms_sorted:
        reading = f'<span class="glossary-reading">{t["reading"]}</span>' if t.get("reading") else ""
        row = kana_row(t.get("reading", ""))
        html += f"""
      <div class="glossary-item" data-row="{row}" data-term="{t['term']}{t.get('reading','')}">
        <h2 class="glossary-term">{t['term']}{reading}</h2>
        <p class="glossary-def">{t['def']}</p>
      </div>"""
    html += """
    </div>
    <p class="glossary-empty" id="glossary-empty" style="display:none;">該当する用語が見つかりませんでした。</p>
  </div>
</section>
<script>
(function(){
  let row = 'すべて';
  const items = [...document.querySelectorAll('.glossary-item')];
  const search = document.getElementById('glossary-search');
  const empty = document.getElementById('glossary-empty');
  function apply(){
    const q = (search.value||'').trim();
    let shown = 0;
    items.forEach(it=>{
      const okRow = (row === 'すべて') || (it.dataset.row === row);
      const okQ = !q || it.dataset.term.indexOf(q) !== -1 || it.textContent.indexOf(q) !== -1;
      const show = okRow && okQ;
      it.style.display = show ? '' : 'none';
      if(show) shown++;
    });
    empty.style.display = shown ? 'none' : '';
  }
  document.querySelectorAll('.glossary-row-btn').forEach(b=> b.addEventListener('click', ()=>{
    document.querySelectorAll('.glossary-row-btn').forEach(x=> x.classList.remove('active'));
    b.classList.add('active'); row = b.dataset.row; apply();
  }));
  search.addEventListener('input', apply);
})();
</script>"""
    # DefinedTermSet 構造化データ
    base = site.get("base_url", "").rstrip("/")
    dts = {"@context": "https://schema.org", "@type": "DefinedTermSet",
           "name": f"クレジットカード用語集｜{site['name']}",
           "url": f"{base}/glossary.html",
           "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t["term"], "description": t["def"]} for t in terms]}
    html += '\n<script type="application/ld+json">\n' + json.dumps(dts, ensure_ascii=False) + '\n</script>'
    html += footer(site)
    write(os.path.join(BASE_DIR, "glossary.html"), html)


def build_404(data):
    site = data["site"]
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex">
  <meta name="description" content="お探しのページは見つかりませんでした。">
  <title>ページが見つかりません｜{site['name']}</title>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Zen+Kaku+Gothic+New:wght@500;700;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="site-header"><div class="container"><div class="header-inner">
  <a href="/" class="logo">{site['logo']}</a>
  <nav class="global-nav"><a href="/index.html#ranking">ランキング</a><a href="/index.html#purpose">目的別</a><a href="/articles.html">記事一覧</a></nav>
</div></div></header>
<section class="detail-page">
  <div class="container container-narrow" style="text-align:center;">
    <p style="font-size:5rem;font-weight:900;background:linear-gradient(120deg,#283593,#ff6f00);-webkit-background-clip:text;background-clip:text;color:transparent;margin-bottom:6px;">404</p>
    <h1 class="article-title">ページが見つかりません</h1>
    <p class="review-text">お探しのページは移動または削除された可能性があります。<br>下記から目的のページをお探しください。</p>
    <div class="apply-cta">
      <a href="/index.html" class="btn-primary">トップページへ戻る</a>
      <a href="/articles.html" class="btn-detail">記事一覧を見る</a>
    </div>
  </div>
</section>
</body>
</html>"""
    write(os.path.join(BASE_DIR, "404.html"), html)


def build_sitemap(data):
    site = data["site"]
    base = site.get("base_url", "").rstrip("/")
    today = datetime.date.today().isoformat()
    urls = [(u, today) for u in ["", "articles.html", "securities.html", "simulator.html", "glossary.html", "about.html", "privacy.html", "disclaimer.html", "contact.html"]]
    urls += [(f"cards/{c['id']}.html", today) for c in data["cards"]]
    urls += [(f"purpose/{p['id']}.html", today) for p in data["purposes"]]
    urls += [(f"articles/{a['id']}.html", article_date(a)) for a in data["articles"]]
    urls += [(f"securities/{b['id']}.html", today) for b in data.get("brokers", [])]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, lastmod in urls:
        loc = f"{base}/{u}" if base else u
        xml += f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>\n"
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
    publish_from_queue(data)
    build_index(data)
    build_card_pages(data)
    build_purpose_pages(data)
    build_article_pages(data)
    build_securities(data)
    build_simulator(data)
    build_glossary(data)
    build_legal_pages(data)
    build_404(data)
    build_sitemap(data)
    n = 6 + len(data["cards"]) + len(data["purposes"]) + len(data["articles"])
    print(f"=== 完了: 約{n}ページを生成しました ===")


if __name__ == "__main__":
    main()
