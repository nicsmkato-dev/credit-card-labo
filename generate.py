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
import re
import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except Exception:
    _PIL_OK = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "cards.json")
# アフィリエイトリンク上書き表（ASP承認後のリンクをここに入れると affiliate_url を差し替える）
#   形式: 1行 = "<id>  <url>"  （# 始まりと空行は無視）
#   未記載のカード/証券は cards.json の affiliate_url（公式URL等）にフォールバック。
#   a8_sync.py がA8の承認済みリンクを自動でこのファイルへ追記する。
LINKS_FILE = os.path.join(BASE_DIR, "data", "affiliate_links.txt")

# 日本語の曜日
WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]


def load_affiliate_overrides():
    """data/affiliate_links.txt を読み、{id: url} を返す。無ければ空dict。"""
    overrides = {}
    if not os.path.exists(LINKS_FILE):
        return overrides
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()  # URLは空白を含まない→先頭=id, 2番目=url, 以降は行末コメント
            if len(parts) < 2:
                continue
            cid, url = parts[0].strip(), parts[1].strip()
            if cid and url:
                overrides[cid] = url
    return overrides


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    overrides = load_affiliate_overrides()
    if overrides:
        for key in ("cards", "brokers"):
            for item in data.get(key, []) or []:
                if isinstance(item, dict) and item.get("id") in overrides:
                    item["affiliate_url"] = overrides[item["id"]]
    return data


def today_str():
    now = datetime.datetime.now()
    return f"{now.year}年{now.month}月{now.day}日（{WEEKDAYS[now.weekday()]}）"


def year_month():
    now = datetime.datetime.now()
    return f"{now.year}年{now.month}月"


def stars_html(n):
    return "★" * n + "☆" * (5 - n)


_CARD_LINK_CACHE = {}

# 本文で正式名以外の表記でも詳細ページへリンクするための別名（表記ゆれ）
CARD_ALIASES = {
    "jcb-card-w": ["JCB CARD W", "JCBカード W", "JCB CARD W plus L"],
    "jcb-gold": ["JCB GOLD"],
    "smbc-card": ["三井住友カード(NL)", "三井住友NL"],
    "dcard-gold": ["dカードGOLD"],
    "epos-gold": ["エポスゴールド"],
    "paypay-gold": ["PayPayゴールド", "PayPayカードゴールド"],
    "aupay-card": ["au PAYカード", "auPAYカード"],
    "aupay-gold": ["au PAYゴールド", "auPAYゴールド"],
    "saison-gold-premium": ["セゾンゴールドプレミアム", "セゾンゴールド・プレミアム"],
}


def _card_link_regex(cards):
    """マッチ文字列→id と正規表現を構築（正式名＋別名、長い表記優先でキャッシュ）"""
    key = id(cards)
    if key not in _CARD_LINK_CACHE:
        pairs = [(c["name"], c["id"]) for c in cards]
        for cid, aliases in CARD_ALIASES.items():
            for a in aliases:
                pairs.append((a, cid))
        pairs.sort(key=lambda x: len(x[0]), reverse=True)
        text_to_id = {t: i for t, i in pairs}
        pat = "|".join(re.escape(t) for t, _ in pairs)
        _CARD_LINK_CACHE[key] = (re.compile(pat), text_to_id)
    return _CARD_LINK_CACHE[key]


def link_cards(text, cards, depth=1, linked_ids=None, skip_id=None):
    """本文中のカード名（別名含む）を、そのカードの詳細ページへのリンクに置換する。
    linked_ids（リスト）を渡すと同一ページで各カード初出の1回だけリンク（過剰リンク防止）。
    skip_id を渡すとそのカード自身（自ページ）はリンクしない。"""
    if not text:
        return text
    rx, text_to_id = _card_link_regex(cards)
    p = "" if depth == 0 else "../"

    def repl(m):
        matched = m.group(0)
        cid = text_to_id[matched]
        if cid == skip_id:
            return matched
        if linked_ids is not None:
            if cid in linked_ids:
                return matched
            linked_ids.append(cid)
        return (f'<a href="{p}cards/{cid}.html" '
                f'class="card-inline-link">{matched}</a>')

    return rx.sub(repl, text)


# 記事の関連度判定用キーワード（タイトル・説明・リードに含まれる語の共有数で関連記事を選ぶ）
RELATED_VOCAB = [
    "還元率", "ポイント", "年会費", "審査", "信用情報", "限度額", "延滞", "多重申込",
    "NISA", "積立", "つみたて", "投資", "iDeCo", "証券", "ポイ活", "経済圏", "ポイントサイト",
    "旅行", "マイル", "空港", "ラウンジ", "海外", "保険", "ふるさと納税",
    "学生", "主婦", "女性", "シニア", "20代", "30代", "社会人",
    "ナンバーレス", "セキュリティ", "不正利用", "3Dセキュア",
    "公共料金", "税金", "家賃", "携帯", "スマホ", "サブスク", "コンビニ", "スーパー", "ガソリン", "ETC",
    "国際ブランド", "VISA", "Mastercard", "JCB", "アメックス", "ダイナース",
    "解約", "再発行", "家族カード", "デビット", "ゴールド", "プラチナ", "即日発行",
    "Amazon", "コストコ", "タッチ決済", "Apple Pay", "Google Pay", "リボ払い",
]
_ARTICLE_KW_CACHE = {}


def article_keywords(a):
    """記事のタイトル＋説明＋リードから関連語の集合を返す（キャッシュ）。"""
    cid = a.get("id")
    if cid in _ARTICLE_KW_CACHE:
        return _ARTICLE_KW_CACHE[cid]
    text = (a.get("title", "") + " " + a.get("description", "") + " " + a.get("lead", "")).lower()
    kw = set(k for k in RELATED_VOCAB if k.lower() in text)
    _ARTICLE_KW_CACHE[cid] = kw
    return kw


def related_articles(a, arts, n=3):
    """共有キーワード数が多い順に関連記事を返す。足りなければ新着で補完。"""
    ak = article_keywords(a)
    scored = []
    for other in arts:
        if other.get("id") == a.get("id"):
            continue
        score = len(ak & article_keywords(other))
        scored.append((score, article_date(other), other))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top = [o for s, d, o in scored if s > 0][:n]
    if len(top) < n:  # 関連が足りなければ新着記事で穴埋め
        for s, d, o in scored:
            if o not in top:
                top.append(o)
            if len(top) >= n:
                break
    return top[:n]


CARD_IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif")


def card_image_path(cid):
    """images/cards/<id>.<ext> が存在すればそのファイル名を返す。無ければ None"""
    for ext in CARD_IMG_EXTS:
        rel = os.path.join("images", "cards", cid + ext)
        if os.path.exists(os.path.join(BASE_DIR, rel)):
            return rel.replace("\\", "/")
    return None


def card_visual(card, depth=0, big=False):
    """実画像があれば<img>、無ければ従来のCSS券面を返す"""
    p = "" if depth == 0 else "../"
    big_cls = " big" if big else ""
    img = card_image_path(card["id"])
    if img:
        return (f'<div class="card-photo{big_cls}">'
                f'<img src="{p}{img}" alt="{card["name"]}" loading="lazy" '
                f'width="320" height="202"></div>')
    return (f'<div class="card-logo-placeholder {card["color"]}{big_cls}">'
            f'<span class="cc-num">•••• •••• •••• ••••</span>'
            f'<span class="cc-brand">{card["brand_label"]}</span>'
            f'<span class="cc-mark"></span></div>')


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


# ポイント経済圏（「楽天経済圏 クレカ」等の検索意図に対応。比較表フィルタ＋経済圏別ページを生成）
KEIZAIKEN = [
    {"id": "rakuten", "name": "楽天", "icon": "🛒", "point": "楽天ポイント",
     "intro": "楽天市場・楽天ペイ・楽天モバイルなど楽天サービスをよく使う方向け。楽天ポイントが貯まりやすいカードをまとめました。",
     "card_ids": ["rakuten-card"]},
    {"id": "vpoint", "name": "Vポイント（三井住友）", "icon": "💳", "point": "Vポイント",
     "intro": "三井住友カード・Oliveを中心としたVポイント経済圏。対象のコンビニ・飲食店で高還元を狙える主力カードです。",
     "card_ids": ["smbc-card", "olive-card", "smbc-gold-nl", "smbc-platinum", "smbc-business"]},
    {"id": "dpoint", "name": "dポイント（ドコモ）", "icon": "📱", "point": "dポイント",
     "intro": "ドコモ・dカードを中心としたdポイント経済圏。携帯料金や日常の買い物でdポイントが貯まり、ドコモユーザーに最適です。",
     "card_ids": ["d-card", "dcard-gold"]},
    {"id": "paypay", "name": "PayPay", "icon": "📲", "point": "PayPayポイント",
     "intro": "PayPay・ソフトバンク・Yahoo!をよく使う方向け。PayPayポイントが効率よく貯まるカードを紹介します。",
     "card_ids": ["paypay-card", "paypay-gold"]},
    {"id": "ponta", "name": "Ponta（au・リクルート）", "icon": "🅿️", "point": "Pontaポイント",
     "intro": "au・じゃらん・ホットペッパーなどPontaが貯まる・使えるサービス向け。au PAYカードやリクルートカードが中心です。",
     "card_ids": ["aupay-card", "aupay-gold", "recruit-card"]},
]
_KEIZAIKEN_OF = {cid: k["id"] for k in KEIZAIKEN for cid in k["card_ids"]}


def card_keizaiken(card):
    """カードが属するポイント経済圏id（rakuten/vpoint/dpoint/paypay/ponta）。無ければ空文字。"""
    return _KEIZAIKEN_OF.get(card.get("id"), "")


def card_cats(card):
    """比較表の絞り込み用カテゴリタグを返す（経済圏タグも含む）"""
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
    kz = card_keizaiken(card)
    if kz:
        cats.append(kz)
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
def head(site, title, description, depth=0, path="", og_image=None):
    prefix = "" if depth == 0 else "../"
    base = site.get("base_url", "").rstrip("/")
    canonical_url = f"{base}/{path}" if path != "index.html" else f"{base}/"
    og_img_url = f"{base}/{og_image}" if og_image else f"{base}/ogp.png"
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
  <meta property="og:image" content="{og_img_url}">
  <meta property="og:site_name" content="{site['name']}">
  <meta property="og:locale" content="ja_JP">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_img_url}">
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
      <button class="nav-toggle" aria-label="メニューを開く" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
      <nav class="global-nav">
        <a href="{p}index.html#ranking">ランキング</a>
        <a href="{p}index.html#purpose">目的別</a>
        <a href="{p}index.html#keizaiken">経済圏</a>
        <a href="{p}campaign.html">キャンペーン</a>
        <a href="{p}simulator.html">ツール</a>
        <a href="{p}securities.html">証券・NISA</a>
        <a href="{p}articles.html">記事一覧</a>
      </nav>
    </div>
  </div>
</header>
<script>
(function(){{
  var h=document.querySelector('.site-header');
  if(!h) return;
  var btn=h.querySelector('.nav-toggle'), nav=h.querySelector('.global-nav');
  btn.addEventListener('click',function(){{
    var open=h.classList.toggle('nav-open');
    btn.setAttribute('aria-expanded',open);
    btn.setAttribute('aria-label',open?'メニューを閉じる':'メニューを開く');
  }});
  nav.addEventListener('click',function(e){{
    if(e.target.tagName==='A'){{ h.classList.remove('nav-open'); btn.setAttribute('aria-expanded','false'); }}
  }});
}})();
</script>"""


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
        <a href="https://x.com/cleca_labo" target="_blank" rel="noopener" class="footer-sns" aria-label="Xでフォロー">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
          <span>@cleca_labo をフォロー</span>
        </a>
      </div>
      <div class="footer-links">
        <h4>ガイド・ツール</h4>
        <a href="{p}campaign.html">入会キャンペーンまとめ</a>
        <a href="{p}credit-card-guide.html">クレジットカード完全ガイド</a>
        <a href="{p}simulator.html">還元シミュレーター</a>
        <a href="{p}annualfee-simulator.html">年会費ペイ計算機</a>
        <a href="{p}tsumitate-simulator.html">クレカ積立シミュレーター</a>
        <a href="{p}glossary.html">用語集</a>
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
            {card_visual(card, depth)}
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

    # 編集部の総合No.1（ファーストビュー直下に申込CTAを置き、回遊の起点にする）
    top = cards[0]
    html += f"""
<section class="featured-pick" id="featured">
  <div class="container">
    <h2 class="section-title">👑 {year_month()} 編集部の総合No.1</h2>
    <p class="section-sub">どれにするか迷ったら、まずこの1枚。{top['catch']}</p>
    {card_block(top, rank=1)}
    <p class="featured-more">ほかの上位カードも比べるなら <a href="#ranking">ランキングTOP5</a> ／ <a href="#comparison">一覧比較表</a> ／ <a href="#purpose">目的別で探す</a></p>
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

    # 新着・お役立ち記事（記事中心構成：上位に配置）
    n_articles = len(data["articles"])
    html += """
<section class="home-articles-section home-articles-top">
  <div class="container">
    <h2 class="section-title">新着・お役立ち記事</h2>
    <p class="section-sub">クレジットカード・ポイ活・新NISAの「知って得する」情報を毎日更新中📈</p>
    <div class="article-topics">
      <a href="articles.html">記事一覧</a>
      <a href="simulator.html">還元シミュレーター</a>
      <a href="glossary.html">用語集</a>
      <a href="credit-card-guide.html">完全ガイド</a>
      <a href="index.html#purpose">目的別で探す</a>
    </div>
    <div class="article-grid">"""
    for a in sorted(data["articles"], key=article_date, reverse=True)[:12]:
        html += f"""
      <a href="articles/{a['id']}.html" class="article-card">
        <div class="article-meta"><span class="article-tag">記事</span><span class="article-card-date">📅 {fmt_date(article_date(a))} 公開</span></div>
        <h3>{a['title']}</h3>
        <p>{a['description']}</p>
        <span class="read-more">続きを読む →</span>
      </a>"""
    html += f"""
    </div>
    <div class="home-articles-more"><a href="articles.html" class="btn-primary">記事をすべて見る（{n_articles}本）→</a></div>
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

    # ポイント経済圏から選ぶ
    html += """
<section class="keizaiken-section" id="keizaiken">
  <div class="container">
    <h2 class="section-title">ポイント経済圏から選ぶ</h2>
    <p class="section-sub">よく使うサービスの「経済圏」に合わせて選ぶと、ポイントが集中して貯まりやすくなります。</p>
    <div class="purpose-grid">"""
    for kz in KEIZAIKEN:
        html += f"""
      <a href="keizaiken/{kz['id']}.html" class="purpose-card">
        <div class="purpose-icon">{kz['icon']}</div>
        <h3>{kz['name']}経済圏</h3>
        <p>{kz['point']}が貯まる・使えるおすすめカード</p>
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
    <div class="table-filters table-filters-kei">
      <span class="filter-group-label">経済圏</span>
      <button class="filter-btn" data-filter="rakuten">楽天</button>
      <button class="filter-btn" data-filter="vpoint">Vポイント</button>
      <button class="filter-btn" data-filter="dpoint">dポイント</button>
      <button class="filter-btn" data-filter="paypay">PayPay</button>
      <button class="filter-btn" data-filter="ponta">au・Ponta</button>
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
      {card_visual(c, 1, big=True)}
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


EYECATCH_DIR = os.path.join(BASE_DIR, "images", "ogp")
_FONT_BOLD = r"C:\Windows\Fonts\meiryob.ttc"


def _wrap_jp(text, n):
    lines, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= n:
            lines.append(cur)
            cur = ""
    if cur:
        lines.append(cur)
    return lines


def build_eyecatch(article, site):
    """記事ごとのアイキャッチ(OGP)画像を生成。既存ならスキップ(キャッシュ)。相対パスを返す。"""
    rel = f"images/ogp/{article['id']}.png"
    out = os.path.join(EYECATCH_DIR, f"{article['id']}.png")
    if os.path.exists(out):
        return rel
    if not _PIL_OK or not os.path.exists(_FONT_BOLD):
        return None
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (26, 36, 86))
    d = ImageDraw.Draw(img)
    d.polygon([(0, H), (W, H), (W, H - 90)], fill=(40, 53, 147))
    d.rectangle([0, 0, W, 12], fill=(255, 111, 0))
    # ロゴマーク（カード型を図形で描画。絵文字はPILで豆腐化するため使わない）
    d.rounded_rectangle([60, 54, 150, 118], radius=10, fill=(255, 111, 0))
    d.rectangle([74, 74, 112, 84], fill=(255, 255, 255))
    brand = ImageFont.truetype(_FONT_BOLD, 38)
    d.text((168, 64), "クレカ比較Labo", font=brand, fill=(255, 255, 255))
    title = article["title"].split("｜")[0]
    fsize = 64 if len(title) <= 22 else 54
    tf = ImageFont.truetype(_FONT_BOLD, fsize)
    lines = _wrap_jp(title, 15 if fsize == 64 else 18)[:4]
    lh = fsize + 18
    y = (H - lh * len(lines)) // 2 + 20
    last_y = y
    for ln in lines:
        w = d.textlength(ln, font=tf)
        d.text(((W - w) // 2, y), ln, font=tf, fill=(255, 255, 255))
        last_y = y + fsize
        y += lh
    d.rectangle([(W - 220) // 2, last_y + 14, (W + 220) // 2, last_y + 22], fill=(255, 111, 0))
    sf = ImageFont.truetype(_FONT_BOLD, 30)
    d.text((60, H - 70), site.get("base_url", "").replace("https://", ""), font=sf, fill=(200, 206, 235))
    os.makedirs(EYECATCH_DIR, exist_ok=True)
    img.save(out, "PNG")
    return rel


# ------------------------- 記事内の図解（オリジナルSVG・著作権セーフ） -------------------------

def _svg_frame(inner, vb="0 0 560 260", label=""):
    return (f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{label}"><rect width="100%" height="100%" rx="14" fill="#fafbff"/>{inner}</svg>')


def diagram_reward_diff(data=None):
    rows = [("0.5%", 5000, "#9aa3c7"), ("1.0%", 10000, "#3949ab"), ("2.0%", 20000, "#ff6f00")]
    inner = ('<text x="280" y="40" text-anchor="middle" font-size="20" font-weight="700" fill="#283593">還元率の差＝1年でこれだけ変わる</text>'
             '<text x="280" y="66" text-anchor="middle" font-size="14" fill="#8a90a8">年100万円を使った場合の年間ポイント</text>'
             '<line x1="100" y1="215" x2="500" y2="215" stroke="#d5d9ec" stroke-width="2"/>')
    x = 130
    for label, v, color in rows:
        h = int(v / 20000 * 120)
        y = 215 - h
        inner += f'<rect x="{x}" y="{y}" width="80" height="{h}" rx="6" fill="{color}"/>'
        inner += f'<text x="{x+40}" y="{y-10}" text-anchor="middle" font-size="19" font-weight="700" fill="#283593">{v:,}円</text>'
        inner += f'<text x="{x+40}" y="241" text-anchor="middle" font-size="17" fill="#3a3f5a">還元率{label}</text>'
        x += 140
    return _svg_frame(inner, label="還元率別の年間ポイント比較")


def diagram_keizaiken(data=None):
    zs = [("楽天", "#bf0000"), ("Vポイント", "#1f6fd0"), ("dポイント", "#cc0033"),
          ("PayPay", "#ea4335"), ("Ponta", "#0b6cb0")]
    inner = ('<text x="280" y="40" text-anchor="middle" font-size="20" font-weight="700" fill="#283593">ポイントは「1つの経済圏に集中」が正解</text>'
             '<text x="280" y="66" text-anchor="middle" font-size="14" fill="#8a90a8">よく使うサービスに合わせてカードも揃える</text>')
    x = 28
    for name, color in zs:
        inner += f'<rect x="{x}" y="105" width="98" height="62" rx="10" fill="#fff" stroke="{color}" stroke-width="2"/>'
        inner += f'<text x="{x+49}" y="142" text-anchor="middle" font-size="15" font-weight="700" fill="{color}">{name}</text>'
        x += 102
    inner += '<text x="280" y="210" text-anchor="middle" font-size="15" fill="#3a3f5a">バラバラに貯めるより、還元がぐっと伸びます</text>'
    return _svg_frame(inner, label="主要なポイント経済圏")


def diagram_rivo(data=None):
    rows = [("一括払い", 0, "0円", "#3949ab"), ("リボ払い", 15000, "約15,000円", "#d84315")]
    inner = ('<text x="280" y="40" text-anchor="middle" font-size="20" font-weight="700" fill="#283593">リボ払いの手数料イメージ</text>'
             '<text x="280" y="66" text-anchor="middle" font-size="14" fill="#8a90a8">10万円を年率15%・1年で支払った場合の概算</text>'
             '<line x1="100" y1="215" x2="500" y2="215" stroke="#d5d9ec" stroke-width="2"/>')
    x = 170
    for label, v, vt, color in rows:
        h = max(6, int(v / 15000 * 120))
        y = 215 - h
        inner += f'<rect x="{x}" y="{y}" width="90" height="{h}" rx="6" fill="{color}"/>'
        inner += f'<text x="{x+45}" y="{y-10}" text-anchor="middle" font-size="19" font-weight="700" fill="#283593">{vt}</text>'
        inner += f'<text x="{x+45}" y="241" text-anchor="middle" font-size="17" fill="#3a3f5a">{label}</text>'
        x += 160
    return _svg_frame(inner, label="一括払いとリボ払いの手数料比較")


def diagram_tsumitate(data=None):
    rows = [("1年", 6000), ("5年", 30000), ("10年", 60000)]
    inner = ('<text x="280" y="40" text-anchor="middle" font-size="20" font-weight="700" fill="#283593">クレカ積立でもらえるポイント</text>'
             '<text x="280" y="66" text-anchor="middle" font-size="14" fill="#8a90a8">月5万円を還元率1%でクレカ積立した場合</text>'
             '<line x1="100" y1="215" x2="500" y2="215" stroke="#d5d9ec" stroke-width="2"/>')
    x = 130
    for label, v in rows:
        h = int(v / 60000 * 120)
        y = 215 - h
        inner += f'<rect x="{x}" y="{y}" width="80" height="{h}" rx="6" fill="#3949ab"/>'
        inner += f'<text x="{x+40}" y="{y-10}" text-anchor="middle" font-size="18" font-weight="700" fill="#283593">{v:,}円分</text>'
        inner += f'<text x="{x+40}" y="241" text-anchor="middle" font-size="17" fill="#3a3f5a">{label}</text>'
        x += 140
    return _svg_frame(inner, label="クレカ積立で貯まるポイントの推移")


def diagram_cardgrade(data=None):
    tiers = [("一般", "年会費無料・基本の還元", "#3949ab"),
             ("ゴールド", "空港ラウンジ・旅行保険・優待", "#c8a23a"),
             ("プラチナ", "コンシェルジュ・高水準の特典", "#6b7280")]
    inner = '<text x="280" y="40" text-anchor="middle" font-size="20" font-weight="700" fill="#283593">カードランクと特典のちがい</text>'
    y = 70
    for name, desc, color in tiers:
        inner += f'<rect x="80" y="{y}" width="400" height="48" rx="10" fill="{color}"/>'
        inner += f'<text x="104" y="{y+30}" font-size="18" font-weight="700" fill="#fff">{name}</text>'
        inner += f'<text x="200" y="{y+30}" font-size="14" fill="#fff">{desc}</text>'
        y += 60
    return _svg_frame(inner, vb="0 0 560 260", label="一般・ゴールド・プラチナの違い")


def _reward_float(s):
    """還元率文字列から基本還元率の数値を取得（例: '1.0%〜3.0%' → 1.0）"""
    m = re.search(r"(\d+\.?\d*)\s*%", s or "")
    return float(m.group(1)) if m else 0.5


# カードブランドカラー（generate.py内CSS変数に合わせた代表色）
_BRAND_COLOR = {
    "smbc-card": "#1f6fd0", "olive-card": "#2e7d32", "rakuten-card": "#bf0000",
    "epos-card": "#b71c1c", "recruit-card": "#1565c0", "jcb-card-w": "#1a237e",
    "aeon-card": "#00695c", "d-card": "#c62828", "smbc-gold-nl": "#b8860b",
    "jcb-gold": "#4a148c", "paypay-card": "#ea4335", "saison-int": "#0277bd",
    "uc-card": "#37474f", "life-card": "#e65100",
}


def diagram_card_vs(data, c1_id, c2_id):
    c1 = card_by_id(data, c1_id) if data else None
    c2 = card_by_id(data, c2_id) if data else None
    if not c1 or not c2:
        return ""
    col1 = _BRAND_COLOR.get(c1_id, "#3949ab")
    col2 = _BRAND_COLOR.get(c2_id, "#c8a23a")
    r1 = _reward_float(c1.get("reward", ""))
    r2 = _reward_float(c2.get("reward", ""))
    fee1 = c1.get("annual_fee", "永年無料")
    fee2 = c2.get("annual_fee", "永年無料")
    maxr = max(r1, r2, 1.0)
    bw, bh, by = 100, 80, 170
    b1h = max(8, int(r1 / maxr * bh))
    b2h = max(8, int(r2 / maxr * bh))
    inner = (
        # 背景パネル左
        f'<rect x="10" y="10" width="240" height="240" rx="12" fill="{col1}" opacity="0.08"/>'
        # 背景パネル右
        f'<rect x="310" y="10" width="240" height="240" rx="12" fill="{col2}" opacity="0.08"/>'
        # VS バッジ
        f'<circle cx="280" cy="130" r="28" fill="#fff" stroke="#d5d9ec" stroke-width="2"/>'
        f'<text x="280" y="137" text-anchor="middle" font-size="18" font-weight="700" fill="#3a3f5a">VS</text>'
        # カード名
        f'<text x="130" y="42" text-anchor="middle" font-size="16" font-weight="700" fill="{col1}">{c1["name"]}</text>'
        f'<text x="430" y="42" text-anchor="middle" font-size="16" font-weight="700" fill="{col2}">{c2["name"]}</text>'
        # 年会費ラベル
        f'<text x="130" y="70" text-anchor="middle" font-size="12" fill="#8a90a8">年会費</text>'
        f'<text x="430" y="70" text-anchor="middle" font-size="12" fill="#8a90a8">年会費</text>'
        f'<text x="130" y="90" text-anchor="middle" font-size="14" font-weight="700" fill="#283593">{fee1}</text>'
        f'<text x="430" y="90" text-anchor="middle" font-size="14" font-weight="700" fill="#283593">{fee2}</text>'
        # 還元率ラベル
        f'<text x="130" y="118" text-anchor="middle" font-size="12" fill="#8a90a8">基本還元率</text>'
        f'<text x="430" y="118" text-anchor="middle" font-size="12" fill="#8a90a8">基本還元率</text>'
        # 棒グラフ（ベースライン y=250）
        f'<line x1="30" y1="250" x2="240" y2="250" stroke="#d5d9ec" stroke-width="1"/>'
        f'<line x1="320" y1="250" x2="530" y2="250" stroke="#d5d9ec" stroke-width="1"/>'
        f'<rect x="{130 - bw//2}" y="{250 - b1h}" width="{bw}" height="{b1h}" rx="6" fill="{col1}"/>'
        f'<rect x="{430 - bw//2}" y="{250 - b2h}" width="{bw}" height="{b2h}" rx="6" fill="{col2}"/>'
        f'<text x="130" y="{250 - b1h - 8}" text-anchor="middle" font-size="20" font-weight="700" fill="{col1}">{r1:.1f}%</text>'
        f'<text x="430" y="{250 - b2h - 8}" text-anchor="middle" font-size="20" font-weight="700" fill="{col2}">{r2:.1f}%</text>'
    )
    return _svg_frame(inner, vb="0 0 560 270", label=f"{c1['name']}と{c2['name']}の比較")


def _vs(c1, c2):
    return lambda data: diagram_card_vs(data, c1, c2)


DIAGRAMS = {
    "point-reward-ranking": (diagram_reward_diff, "還元率0.5%と1%・2%では、年間でこれだけポイントが変わります。"),
    "high-reward-howto": (diagram_reward_diff, "還元率を上げるだけで、年間のポイントは大きく変わります。"),
    "annual-fee-worth": (diagram_reward_diff, "還元率の差は、年会費を上回ることもあります。"),
    "point-keizaiken": (diagram_keizaiken, "主要なポイント経済圏。よく使う1つに寄せるのが効率的です。"),
    "revolving": (diagram_rivo, "リボ払いは手数料が大きい。支払いは一括が基本です。"),
    "kureka-tsumitate": (diagram_tsumitate, "クレカ積立なら、投資しながらポイントも貯まります。"),
    "point-investment": (diagram_tsumitate, "ポイント投資・クレカ積立で貯まるポイントの目安です。"),
    "card-grade": (diagram_cardgrade, "カードのランクごとに、特典の手厚さが変わります。"),
    # 比較記事（公開済み）
    "vs-rakuten-smbc":   (_vs("rakuten-card", "smbc-card"),   "楽天カードと三井住友カード(NL)の基本還元率比較。"),
    "vs-rakuten-jcbw":   (_vs("rakuten-card", "jcb-card-w"),  "楽天カードとJCB CARD Wの基本還元率比較。"),
    "vs-smbc-epos":      (_vs("smbc-card", "epos-card"),      "三井住友カード(NL)とエポスカードの基本還元率比較。"),
    "vs-recruit-rakuten":(_vs("recruit-card", "rakuten-card"),"リクルートカードと楽天カードの基本還元率比較。"),
    "vs-jcbw-recruit":   (_vs("jcb-card-w", "recruit-card"),  "JCB CARD Wとリクルートカードの基本還元率比較。"),
    "vs-aeon-rakuten":   (_vs("aeon-card", "rakuten-card"),   "イオンカードと楽天カードの基本還元率比較。"),
    # 比較記事（キュー）
    "vs-smbcgold-jcbgold":(_vs("smbc-gold-nl", "jcb-gold"),  "三井住友ゴールド(NL)とJCBゴールドの基本還元率比較。"),
    "vs-epos-jcbw":      (_vs("epos-card", "jcb-card-w"),     "エポスカードとJCB CARD Wの基本還元率比較。"),
    "vs-dcard-rakuten":  (_vs("d-card", "rakuten-card"),      "dカードと楽天カードの基本還元率比較。"),
    "vs-smbc-recruit":   (_vs("smbc-card", "recruit-card"),   "三井住友カード(NL)とリクルートカードの基本還元率比較。"),
}


def build_keizaiken_pages(data):
    """ポイント経済圏別おすすめページ（楽天/Vポイント/dポイント/PayPay/Ponta）。"""
    site = data["site"]
    os.makedirs(os.path.join(BASE_DIR, "keizaiken"), exist_ok=True)
    for kz in KEIZAIKEN:
        cards = [card_by_id(data, cid) for cid in kz["card_ids"]]
        cards = [c for c in cards if c]
        if not cards:
            continue
        title = f"{kz['name']}経済圏におすすめのクレジットカード"
        desc = f"{kz['name']}経済圏で{kz['point']}を効率よく貯めるおすすめクレジットカードを比較。{kz['intro']}"
        html = head(site, f"{title}｜{site['name']}", desc, depth=1, path=f"keizaiken/{kz['id']}.html")
        html += header(site, depth=1)
        html += f"""
<section class="purpose-detail">
  <div class="container">
    <nav class="breadcrumb"><a href="../index.html">ホーム</a> ＞ <a href="../index.html#keizaiken">経済圏から選ぶ</a> ＞ <span>{kz['name']}経済圏</span></nav>
    <h1 class="section-title">{kz['icon']} {title}</h1>
    <p class="section-sub">{kz['intro']}</p>"""
        for i, c in enumerate(cards, start=1):
            html += card_block(c, rank=i, depth=1)
        # 他の経済圏への内部リンク
        html += """
    <div class="related-articles">
      <h2>他のポイント経済圏から選ぶ</h2>"""
        for other in KEIZAIKEN:
            if other["id"] != kz["id"]:
                html += f"""
      <a href="{other['id']}.html" class="related-link">{other['icon']} {other['name']}経済圏のおすすめカード</a>"""
        html += """
    </div>
  </div>
</section>"""
        # Breadcrumb JSON-LD
        base = site.get("base_url", "").rstrip("/")
        bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{base}/"},
            {"@type": "ListItem", "position": 2, "name": f"{kz['name']}経済圏", "item": f"{base}/keizaiken/{kz['id']}.html"}]}
        html += '\n<script type="application/ld+json">\n' + json.dumps(bc, ensure_ascii=False) + '\n</script>'
        html += footer(site, depth=1)
        write(os.path.join(BASE_DIR, "keizaiken", f"{kz['id']}.html"), html)


def build_campaign(data):
    """今月の入会キャンペーンまとめ（入会特典のあるカードをデータ駆動で一覧・毎日再生成で鮮度維持）。"""
    site = data["site"]
    cards = [c for c in data["cards"] if c.get("bonus") and c["bonus"] not in ("入会特典あり", "—", "")]
    html = head(site, f"クレジットカード 入会キャンペーンまとめ｜{year_month()}最新｜{site['name']}",
                f"{year_month()}最新のクレジットカード入会キャンペーン・新規入会特典をまとめて比較。お得に作れるカードを毎日更新でチェックできます。",
                path="campaign.html")
    html += header(site)
    html += f"""
<section class="comparison-section">
  <div class="container">
    <nav class="breadcrumb"><a href="index.html">ホーム</a> ＞ <span>入会キャンペーンまとめ</span></nav>
    <h1 class="section-title">🎁 {year_month()} クレジットカード入会キャンペーンまとめ</h1>
    <p class="section-sub">新規入会・利用で受け取れる特典が大きいカードを一覧にまとめました。特典内容は変更されることがあるため、最新情報は各公式サイトでご確認ください。</p>
    <div class="table-wrapper">
      <table class="comparison-table">
        <thead>
          <tr><th>カード名</th><th>入会特典</th><th>年会費</th><th>還元率</th><th>申込</th></tr>
        </thead>
        <tbody>"""
    for c in cards:
        rstr = f"<strong>{c['reward']}</strong>" if c.get("reward_highlight") else c["reward"]
        html += f"""
          <tr>
            <td><a href="cards/{c['id']}.html"><strong>{c['name']}</strong></a></td>
            <td><strong class="campaign-bonus">{c['bonus']}</strong></td>
            <td>{c['annual_fee'].replace('永年', '')}</td>
            <td>{rstr}</td>
            <td><a href="{c['affiliate_url']}" target="_blank" rel="nofollow sponsored noopener" class="table-btn">申込む</a></td>
          </tr>"""
    html += """
        </tbody>
      </table>
    </div>
    <p class="table-scroll-hint">※入会特典は時期・条件により変動します。獲得条件（利用金額・期間等）は各公式サイトで必ずご確認ください。</p>
    <div class="article-cta">
      <h3>まずは自分に合う1枚から</h3>
      <p>特典の大きさだけでなく、年会費・還元率・使う場所との相性で選ぶのがおすすめです。</p>
      <a href="index.html#ranking" class="btn-primary">おすすめランキングを見る</a>
    </div>
  </div>
</section>"""
    html += footer(site)
    write(os.path.join(BASE_DIR, "campaign.html"), html)


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
        eyecatch = build_eyecatch(a, site)
        h = head(site, f"{a['title']}｜{site['name']}", a["description"], depth=1,
                 path=f"articles/{a['id']}.html", og_image=eyecatch)
        h += header(site, depth=1)
        linked = []  # 記事内で言及・リンクしたカードid（初出順）
        h += f"""
<article class="detail-page">
  <div class="container container-narrow">
    <nav class="breadcrumb"><a href="../index.html">ホーム</a> ＞ <a href="../articles.html">記事一覧</a> ＞ <span>{a['title']}</span></nav>
    <h1 class="article-title">{a['title']}</h1>
    <p class="article-date">📅 {fmt_date(article_date(a))} 公開</p>
    <p class="article-byline">✍️ 監修・執筆：<a href="../about.html">{site['name']}編集部</a>（金融業界歴20年以上・元クレジットカード会社実務）</p>
    <p class="article-lead">{link_cards(a['lead'], data['cards'], 1, linked)}</p>"""
        # 記事内の図解（対象記事のみ・オリジナルSVG）
        if a["id"] in DIAGRAMS:
            dfunc, caption = DIAGRAMS[a["id"]]
            svg = dfunc(data)
            if svg:
                h += f"""
    <figure class="article-figure">
      {svg}
      <figcaption>{caption}</figcaption>
    </figure>"""
        secs = a["sections"]
        # 目次（見出し3つ以上のときだけ・アンカー内部リンクで構造化＆回遊性UP）
        if len(secs) >= 3:
            h += """
    <nav class="article-toc" aria-label="目次">
      <p class="toc-title">📑 目次</p>
      <ol>"""
            for i, s in enumerate(secs):
                h += f"""
        <li><a href="#sec-{i}">{s['h']}</a></li>"""
            h += """
      </ol>
    </nav>"""
        for i, s in enumerate(secs):
            h += f"""
    <h2 id="sec-{i}">{s['h']}</h2>
    <p class="review-text">{link_cards(s['p'], data['cards'], 1, linked)}</p>"""
        # 記事で紹介したカードの詳細リンク（本文で言及されたカードを末尾にまとめる）
        if linked:
            h += """
    <div class="article-card-links">
      <h2>この記事で紹介したカード</h2>
      <ul>"""
            for cid in linked:
                c = card_by_id(data, cid)
                if c:
                    h += f"""
        <li><a href="../cards/{cid}.html">{c['name']} の詳細を見る →</a></li>"""
            h += """
      </ul>
    </div>"""
        # 関連記事（トピック関連度＝共有キーワード数で選定・内部リンク最適化）
        related = related_articles(a, data["articles"], n=3)
        h += """
    <div class="related-articles">
      <h2>関連記事</h2>"""
        for r in related:
            h += f"""
      <a href="{r['id']}.html" class="related-link">📄 {r['title']}</a>"""
        h += """
    </div>"""
        # 記事末尾にランキング誘導＋便利ツール導線
        h += """
    <div class="article-cta">
      <h3>おすすめカードはこちら</h3>
      <p>編集部おすすめのクレジットカードランキングもぜひチェックしてください。</p>
      <a href="../index.html#ranking" class="btn-primary">ランキングを見る</a>
    </div>
    <div class="tool-links">
      <p class="tool-links-title">🛠 無料ツールで比べてみる</p>
      <div class="tool-links-row">
        <a href="../simulator.html" class="tool-link">📊 ポイント還元シミュレーター<small>毎月の利用額で年間ポイントを計算</small></a>
        <a href="../glossary.html" class="tool-link">📖 クレジットカード用語集<small>わからない用語をすぐ解説</small></a>
      </div>
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
        "about.html": ("運営者情報・編集方針", f"""
    <h2>サイト名</h2><p class="review-text">{site['name']}（{site.get('base_url','').replace('https://','')}）</p>
    <h2>運営者・編集責任者について</h2>
    <div class="author-profile">
      <p class="review-text">当サイトは、<strong>金融業界で20年以上の実務経験を持つ編集者</strong>が責任者として運営しています。キャリアの出発点は<strong>クレジットカード会社での実務（2004年〜2006年）</strong>。カードの発行・審査・ポイントプログラムに加え、<strong>加盟店開拓（お店がカード決済を導入する側の営業）</strong>まで、カードビジネスを事業者側の立場で幅広く経験してきました。その後も一貫して金融分野に携わり、家計・資産形成の相談対応にも取り組んでいます。</p>
      <p class="review-text">「カードは発行する側の理屈も、使う側のお得も、両方わかっている」——この視点を強みに、クレジットカード・ポイ活・新NISAといった“お金まわり”のテーマを、生活者の目線でわかりやすく解説することを目指しています。編集責任者自身も複数枚のカードを保有・使い分け、ポイント還元やクレカ積立を日常的に活用しています。</p>
      <ul class="policy-list">
        <li><strong>専門分野</strong>：クレジットカード（発行・審査・ポイント設計・加盟店開拓の実務経験）／ポイント経済圏／新NISA・つみたて投資／家計の見直し</li>
        <li><strong>経歴</strong>：2004年〜2006年 クレジットカード会社にて実務／2006年〜現在 金融分野に従事（実務経験20年以上）</li>
        <li><strong>運営スタンス</strong>：特定の発行会社に偏らず、読者にとっての実利を基準に比較・評価</li>
      </ul>
      <p class="review-text" style="font-size:0.9em;color:#8a90a8;">※プライバシー保護および中立性の観点から、編集責任者の氏名は非公開としています。取材・監修・提携等のご依頼は<a href="contact.html">お問い合わせ</a>より承ります。</p>
    </div>
    <h2>運営方針</h2><p class="review-text">{site['name']}は、クレジットカードを検討している方が自分に合った1枚を見つけられるよう、年会費・ポイント還元率・特典などを公平に比較・紹介する情報メディアです。「広告だから上位」ではなく、読者にとっての使いやすさ・お得さを基準に編集することを大切にしています。</p>
    <h2>カードの選定・評価基準</h2>
    <p class="review-text">当サイトのランキング・おすすめは、以下の6つの観点を編集部で総合的に評価して作成しています。</p>
    <ol class="policy-list">
      <li><strong>年会費</strong>：永年無料か、年会費に見合う特典があるか</li>
      <li><strong>ポイント還元率</strong>：通常還元率と、店舗ごとの上乗せ還元のお得さ</li>
      <li><strong>特典・付帯保険</strong>：旅行保険・ショッピング保険・優待などの充実度</li>
      <li><strong>セキュリティ</strong>：ナンバーレスや不正利用補償など安心して使えるか</li>
      <li><strong>入会キャンペーン</strong>：新規入会で受け取れる特典・ポイントの大きさ</li>
      <li><strong>使いやすさ・評判</strong>：発行スピード・対応ブランド・利用者の評判</li>
    </ol>
    <h2>情報の正確性への取り組み</h2><p class="review-text">掲載している年会費・還元率・特典・キャンペーン等の情報は、各カード発行会社の公式サイトをはじめとする一次情報をもとに編集部が確認しています。サービス内容は変更されることがあるため、サイトは継続的に見直し・更新を行っていますが、お申し込みの際は必ず各カード公式サイトで最新情報をご確認ください。誤りを見つけられた場合は<a href="contact.html">お問い合わせ</a>からご指摘いただけると幸いです。</p>
    <h2>広告・アフィリエイトの開示</h2><p class="review-text">本サイトはアフィリエイトプログラム（A8.net、afb、バリューコマース等）に参加しており、掲載リンクを経由してカードが発行された場合に、提携先から当サイトへ成果報酬が支払われることがあります。ただし、掲載順位や評価は報酬額のみで決定するものではなく、上記の選定基準に基づく編集部の判断で行っています。詳しくは<a href="disclaimer.html">免責事項</a>・<a href="privacy.html">プライバシーポリシー</a>をご覧ください。</p>
    <h2>監修・口コミについて（透明性のための注記）</h2><p class="review-text">当サイトは、実在しない監修者名や、根拠のない口コミ・体験談を掲載しないことを編集方針としています。掲載しているのは、公式情報をもとにした編集部独自の比較・解説です。</p>
    <h2>お問い合わせ</h2><p class="review-text">ご質問・掲載情報の誤りのご指摘・取材や提携のご依頼などは <a href="contact.html">お問い合わせページ</a>（📧 crecalabo.info@gmail.com）までご連絡ください。</p>"""),
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
""" + tools_nav("simulator.html") + """
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


def tools_nav(active, depth=0):
    """3つのシミュレーターを相互リンクするツールバー"""
    p = "" if depth == 0 else "../"
    tools = [("simulator.html", "💳 還元シミュレーター"),
             ("annualfee-simulator.html", "💰 年会費ペイ計算"),
             ("rivo-simulator.html", "⚠️ リボ手数料計算"),
             ("tsumitate-simulator.html", "📈 クレカ積立シミュ")]
    btns = "".join(
        f'<a href="{p}{u}" class="tool-tab{" active" if u == active else ""}">{label}</a>'
        for u, label in tools)
    return f'<div class="tool-tabs">{btns}</div>'


def build_annualfee_simulator(data):
    """年会費ペイ計算機（年会費ありカードが年間利用でペイできるか判定）。"""
    site = data["site"]
    html = head(site, f"年会費ペイ計算機｜ゴールドカードの元は取れる？｜{site['name']}",
                "年会費・年間利用額・上乗せ還元率・特典価値を入力するだけで、年会費ありカード（ゴールド等）の元が取れるかを瞬時に判定できる無料計算機です。",
                path="annualfee-simulator.html")
    html += header(site)
    html += """
<section class="simulator-section">
  <div class="container container-narrow">
    <h1 class="section-title">年会費ペイ計算機</h1>
    <p class="section-sub">ゴールドカードなど年会費がかかるカードでも、年間の利用額しだいで「元が取れる」ことがあります。あなたの場合はどうか計算してみましょう。</p>
""" + tools_nav("annualfee-simulator.html") + """
    <div class="sim-box">
      <label class="sim-label" for="af-fee">カードの年会費（円）</label>
      <input type="number" id="af-fee" class="sim-input" value="5500" min="0" step="100" inputmode="numeric">
      <label class="sim-label" for="af-spend">年間のカード利用額（円）</label>
      <input type="number" id="af-spend" class="sim-input" value="1200000" min="0" step="10000" inputmode="numeric">
      <div class="sim-presets">
        <button type="button" class="sim-preset" data-af="600000">年60万</button>
        <button type="button" class="sim-preset" data-af="1200000">年120万</button>
        <button type="button" class="sim-preset" data-af="2400000">年240万</button>
      </div>
      <label class="sim-label" for="af-rate">無料カードより上乗せされる還元率（％）</label>
      <input type="number" id="af-rate" class="sim-input" value="0.5" min="0" step="0.1" inputmode="decimal">
      <label class="sim-label" for="af-perk">特典の年間価値（円）<small>空港ラウンジ・旅行保険・優待などの価値</small></label>
      <input type="number" id="af-perk" class="sim-input" value="0" min="0" step="1000" inputmode="numeric">
      <button type="button" id="af-run" class="btn-primary sim-run">元が取れるか計算する</button>
    </div>
    <div id="af-result" class="sim-result"></div>
    <p class="sim-note">※「上乗せ還元率」は、年会費無料カード（通常0.5〜1.0%）と比べてそのカードが追加で得られる還元率の目安です。特典価値は人によって異なります。あくまで概算で、最終判断は各公式サイトの最新情報でご確認ください。</p>
  </div>
</section>
<script>
const yen = n => Math.round(n).toLocaleString('ja-JP');
function runAF(){
  const fee = Math.max(0, parseFloat(document.getElementById('af-fee').value||'0'));
  const spend = Math.max(0, parseFloat(document.getElementById('af-spend').value||'0'));
  const rate = Math.max(0, parseFloat(document.getElementById('af-rate').value||'0'));
  const perk = Math.max(0, parseFloat(document.getElementById('af-perk').value||'0'));
  const rewardMerit = spend * rate / 100;
  const totalMerit = rewardMerit + perk;
  const net = totalMerit - fee;
  const box = document.getElementById('af-result');
  let head, cls;
  if(net >= 0){ head = '✅ 元が取れます（年間 +' + yen(net) + '円のお得）'; cls = 'af-ok'; }
  else { head = '⚠️ 現状ではペイしません（年間 ' + yen(net) + '円）'; cls = 'af-ng'; }
  let breakeven = '';
  if(rate > 0){
    const need = Math.max(0, (fee - perk)) / (rate/100);
    breakeven = '<p class="af-line">年会費を還元だけでペイするのに必要な年間利用額：<strong>' + yen(need) + '円</strong>（月 ' + yen(need/12) + '円）</p>';
  }
  box.innerHTML = '<div class="af-card ' + cls + '">'
    + '<p class="af-head">' + head + '</p>'
    + '<p class="af-line">年間の上乗せ還元：<strong>' + yen(rewardMerit) + '円</strong></p>'
    + '<p class="af-line">特典の年間価値：<strong>' + yen(perk) + '円</strong></p>'
    + '<p class="af-line">メリット合計 − 年会費：<strong>' + yen(totalMerit) + '円 − ' + yen(fee) + '円 = ' + yen(net) + '円</strong></p>'
    + breakeven + '</div>';
  box.style.display = 'block';
}
document.getElementById('af-run').addEventListener('click', runAF);
document.querySelectorAll('.sim-preset').forEach(b => b.addEventListener('click', () => {
  document.getElementById('af-spend').value = b.getAttribute('data-af'); runAF();
}));
runAF();
</script>"""
    html += footer(site)
    write(os.path.join(BASE_DIR, "annualfee-simulator.html"), html)


def build_rivo_simulator(data):
    """リボ払い手数料シミュレーター"""
    site = data["site"]
    html = head(site, f"リボ払い手数料シミュレーター｜完済までの期間と手数料を計算｜{site['name']}",
                "リボ払いの残高・毎月の返済額・手数料率を入力すると、完済までの期間と支払う手数料の総額を計算します。リボ払いの怖さが数字でわかります。",
                path="rivo-simulator.html")
    html += header(site)
    html += """
<section class="simulator-section">
  <div class="container container-narrow">
    <h1 class="section-title">リボ払い手数料シミュレーター</h1>
    <p class="section-sub">リボ払いの残高・毎月の返済額・手数料率を入れると、完済までの期間と手数料の総額を計算します。</p>
""" + tools_nav("rivo-simulator.html") + """
    <div class="sim-box">
      <label class="sim-label" for="rb-bal">リボ残高（円）</label>
      <input type="number" id="rb-bal" class="sim-input" value="200000" min="0" step="10000" inputmode="numeric">
      <label class="sim-label" for="rb-pay">毎月の返済額（円）</label>
      <input type="number" id="rb-pay" class="sim-input" value="10000" min="0" step="1000" inputmode="numeric">
      <label class="sim-label" for="rb-rate">手数料率（実質年率 %）</label>
      <input type="number" id="rb-rate" class="sim-input" value="15.0" min="0" max="20" step="0.1" inputmode="decimal">
      <button type="button" id="rb-run" class="btn-primary sim-run">計算する</button>
    </div>
    <div id="rb-result" class="sim-result"></div>
    <p class="sim-note">※元金定額方式での概算です。実際の計算方式・手数料率はカード会社により異なります。あくまで目安としてご利用ください。</p>
  </div>
</section>
<script>
const yen = n => Math.round(n).toLocaleString('ja-JP');
function rbRun(){
  let bal = Math.max(0, parseFloat(document.getElementById('rb-bal').value||'0'));
  const pay = Math.max(0, parseFloat(document.getElementById('rb-pay').value||'0'));
  const rate = Math.max(0, parseFloat(document.getElementById('rb-rate').value||'0'))/100/12;
  const el = document.getElementById('rb-result');
  if(!bal || !pay){ el.innerHTML='<p class="sim-empty">残高と返済額を入力してください。</p>'; return; }
  const principal0 = bal;
  let months=0, interestTotal=0;
  const firstInterest = bal*rate;
  if(pay <= firstInterest){
    el.innerHTML = '<div class="rb-warn"><strong>⚠️ このままでは完済できません。</strong>毎月の返済額が手数料（初月 約'+yen(firstInterest)+'円）以下のため、残高がほとんど減りません。返済額を増やすか、一括返済を検討してください。</div>';
    return;
  }
  while(bal > 0 && months < 1200){
    const interest = bal*rate;
    interestTotal += interest;
    let principal = pay - interest;
    if(principal > bal) principal = bal;
    bal -= principal;
    months++;
  }
  const total = principal0 + interestTotal;
  const y = Math.floor(months/12), m = months%12;
  el.innerHTML =
    '<div class="rb-cards">'
    + '<div class="rb-stat"><span class="rb-k">完済までの期間</span><span class="rb-v">'+(y?y+'年':'')+(m?m+'ヶ月':(y?'':months+'ヶ月'))+'</span></div>'
    + '<div class="rb-stat warn"><span class="rb-k">手数料の総額</span><span class="rb-v">約'+yen(interestTotal)+'円</span></div>'
    + '<div class="rb-stat"><span class="rb-k">総支払額</span><span class="rb-v">約'+yen(total)+'円</span></div>'
    + '</div>'
    + '<p class="rb-msg">一括払いなら手数料は<strong>0円</strong>。リボ払いを続けると <strong>'+yen(interestTotal)+'円</strong> 多く支払う計算です。可能な範囲で返済額を上げる・繰上返済するのが得策です。</p>';
}
document.getElementById('rb-run').addEventListener('click', rbRun);
rbRun();
</script>"""
    html += footer(site)
    write(os.path.join(BASE_DIR, "rivo-simulator.html"), html)


def build_tsumitate_simulator(data):
    """クレカ積立シミュレーター"""
    site = data["site"]
    html = head(site, f"クレカ積立シミュレーター｜貯まるポイントと将来資産を概算｜{site['name']}",
                "毎月の積立額・還元率・想定利回り・年数を入力すると、クレカ積立で貯まるポイントと、将来の資産額・運用益を概算します。新NISAと組み合わせて活用しましょう。",
                path="tsumitate-simulator.html")
    html += header(site)
    html += """
<section class="simulator-section">
  <div class="container container-narrow">
    <h1 class="section-title">クレカ積立シミュレーター</h1>
    <p class="section-sub">毎月の積立額と条件を入れると、貯まるポイントと将来の資産額を概算します。新NISAのつみたて投資枠と相性抜群です。</p>
""" + tools_nav("tsumitate-simulator.html") + """
    <div class="sim-box">
      <label class="sim-label" for="ts-amt">毎月の積立額（円）</label>
      <input type="number" id="ts-amt" class="sim-input" value="30000" min="0" max="100000" step="1000" inputmode="numeric">
      <label class="sim-label" for="ts-pt">クレカ積立の還元率（%）</label>
      <input type="number" id="ts-pt" class="sim-input" value="0.5" min="0" max="5" step="0.1" inputmode="decimal">
      <label class="sim-label" for="ts-ret">想定の年利回り（%）</label>
      <input type="number" id="ts-ret" class="sim-input" value="5" min="0" max="15" step="0.5" inputmode="decimal">
      <label class="sim-label" for="ts-yr">積立年数（年）</label>
      <input type="number" id="ts-yr" class="sim-input" value="20" min="1" max="40" step="1" inputmode="numeric">
      <button type="button" id="ts-run" class="btn-primary sim-run">計算する</button>
    </div>
    <div id="ts-result" class="sim-result"></div>
    <p class="sim-note">※想定利回りは保証された数値ではなく、運用成果は変動します。複利・毎月積立で概算しています。クレカ積立の上限は月10万円です。投資判断はご自身の責任で行ってください。</p>
  </div>
</section>
<script>
const yen2 = n => Math.round(n).toLocaleString('ja-JP');
function tsRun(){
  const amt = Math.max(0, parseFloat(document.getElementById('ts-amt').value||'0'));
  const pt = Math.max(0, parseFloat(document.getElementById('ts-pt').value||'0'))/100;
  const r = Math.max(0, parseFloat(document.getElementById('ts-ret').value||'0'))/100/12;
  const yrs = Math.max(0, parseInt(document.getElementById('ts-yr').value||'0',10));
  const n = yrs*12;
  const el = document.getElementById('ts-result');
  if(!amt || !n){ el.innerHTML='<p class="sim-empty">積立額と年数を入力してください。</p>'; return; }
  const principal = amt*n;
  const fv = r>0 ? amt*((Math.pow(1+r,n)-1)/r) : principal;
  const gain = fv - principal;
  const points = amt*n*pt;
  el.innerHTML =
    '<div class="rb-cards">'
    + '<div class="rb-stat"><span class="rb-k">積立元本</span><span class="rb-v">'+yen2(principal)+'円</span></div>'
    + '<div class="rb-stat good"><span class="rb-k">将来の資産額（概算）</span><span class="rb-v">約'+yen2(fv)+'円</span></div>'
    + '<div class="rb-stat"><span class="rb-k">うち運用益</span><span class="rb-v">約'+yen2(gain)+'円</span></div>'
    + '<div class="rb-stat good"><span class="rb-k">貯まるポイント総額</span><span class="rb-v">約'+yen2(points)+'円分</span></div>'
    + '</div>'
    + '<p class="rb-msg">現金で積み立てるとポイントは付きませんが、クレカ積立なら <strong>約'+yen2(points)+'円分</strong> のポイントが上乗せされます。新NISAなら運用益も非課税です。</p>'
    + '<div class="apply-cta"><a href="securities.html" class="btn-primary">ネット証券・NISAを比較する</a></div>';
}
document.getElementById('ts-run').addEventListener('click', tsRun);
tsRun();
</script>"""
    html += footer(site)
    write(os.path.join(BASE_DIR, "tsumitate-simulator.html"), html)


def build_pillars(data):
    """完全ガイド（ピラーページ）"""
    site = data["site"]
    pillars = data.get("pillars", [])
    if not pillars:
        return
    art_title = {a["id"]: a["title"] for a in data["articles"]}
    base = site.get("base_url", "").rstrip("/")
    for pl in pillars:
        html = head(site, f"{pl['title']}｜{site['name']}", pl["description"], path=f"{pl['id']}.html")
        html += header(site)
        html += f"""
<article class="pillar-page">
  <div class="container container-narrow">
    <nav class="breadcrumb"><a href="index.html">ホーム</a> ＞ <span>{pl['title']}</span></nav>
    <h1 class="article-title">{pl['title']}</h1>
    <p class="article-lead">{pl['lead']}</p>"""
        # 目次
        html += '\n    <div class="pillar-toc"><h2>目次</h2><ol>'
        for i, s in enumerate(pl["sections"], 1):
            html += f'<li><a href="#sec-{i}">{s["h"]}</a></li>'
        html += '</ol></div>'
        # 各セクション
        for i, s in enumerate(pl["sections"], 1):
            html += f"""
    <section class="pillar-sec" id="sec-{i}">
      <h2>{s['h']}</h2>
      <p class="review-text">{s['p']}</p>
      <div class="pillar-links">"""
            for aid in s["ids"]:
                if aid in art_title:
                    html += f'\n        <a href="articles/{aid}.html" class="pillar-link">📄 {art_title[aid]}</a>'
            html += """
      </div>
    </section>"""
        # CTA
        if pl.get("cta") == "securities":
            html += """
    <div class="article-cta">
      <h3>ネット証券・NISAを比較する</h3>
      <p>クレカ積立に対応したネット証券を、手数料・ポイント還元で比較できます。</p>
      <a href="securities.html" class="btn-primary">証券・NISA比較を見る</a>
    </div>"""
        else:
            html += """
    <div class="article-cta">
      <h3>おすすめカードをチェック</h3>
      <p>編集部おすすめのクレジットカードランキングもぜひご覧ください。</p>
      <a href="index.html#ranking" class="btn-primary">ランキングを見る</a>
    </div>"""
        html += """
  </div>
</article>"""
        bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": f"{base}/"},
            {"@type": "ListItem", "position": 2, "name": pl["title"], "item": f"{base}/{pl['id']}.html"}]}
        html += '\n<script type="application/ld+json">\n' + json.dumps(bc, ensure_ascii=False) + '\n</script>'
        html += footer(site)
        write(os.path.join(BASE_DIR, f"{pl['id']}.html"), html)


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
    urls = [(u, today) for u in ["", "articles.html", "campaign.html", "securities.html", "simulator.html", "annualfee-simulator.html", "rivo-simulator.html", "tsumitate-simulator.html", "glossary.html", "about.html", "privacy.html", "disclaimer.html", "contact.html"]]
    urls += [(f"{p['id']}.html", today) for p in data.get("pillars", [])]
    urls += [(f"cards/{c['id']}.html", today) for c in data["cards"]]
    urls += [(f"purpose/{p['id']}.html", today) for p in data["purposes"]]
    urls += [(f"keizaiken/{kz['id']}.html", today) for kz in KEIZAIKEN]
    urls += [(f"articles/{a['id']}.html", article_date(a)) for a in data["articles"]]
    urls += [(f"securities/{b['id']}.html", today) for b in data.get("brokers", [])]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, lastmod in urls:
        loc = f"{base}/{u}" if base else u
        xml += f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>\n"
    xml += "</urlset>\n"
    write(os.path.join(BASE_DIR, "sitemap.xml"), xml)
    # Search Consoleの「取得できませんでした」張り付き対策として別名でも同内容を出力
    write(os.path.join(BASE_DIR, "sitemap_v2.xml"), xml)

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
    build_keizaiken_pages(data)
    build_campaign(data)
    build_article_pages(data)
    build_securities(data)
    build_simulator(data)
    build_annualfee_simulator(data)
    build_rivo_simulator(data)
    build_tsumitate_simulator(data)
    build_glossary(data)
    build_pillars(data)
    build_legal_pages(data)
    build_404(data)
    build_sitemap(data)
    n = 6 + len(data["cards"]) + len(data["purposes"]) + len(data["articles"])
    print(f"=== 完了: 約{n}ページを生成しました ===")


if __name__ == "__main__":
    main()
