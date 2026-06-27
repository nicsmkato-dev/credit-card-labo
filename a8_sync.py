# -*- coding: utf-8 -*-
"""
a8_sync.py — A8.net の「承認済み（提携中）」プログラムのアフィリエイトリンクを
自動取得して creca-labo の data/affiliate_links.txt を更新するスクリプト。

方式A（採用）: 専用Chromeプロファイル(a8_profile)に【横浜アカウント】で初回だけ手動ログイン
  →セッションを保存。以降は手動不要で自動再利用（x_poster/note と同じ運用）。
  ※A8の提携作業はもともと実Chrome操作で行っていた経緯あり。会員名義は「横浜」。

全体の流れ:
  1) 専用プロファイルでA8にログイン（初回のみ横浜アカウントで手動／以降セッション再利用）
  2) 参加プログラム一覧から「提携中」のプログラム名＋px.a8.netリンクを収集
  3) data/a8_program_map.json でカードID(creca-labo)に突合
  4) data/affiliate_links.txt を再生成（承認済みカードのリンクを反映）
  5) auto_deploy=true なら deploy.ps1 を実行（generate.py → commit → push）

設計メモ:
  - ログイン / 突合 / ファイル更新 / deploy のプラミングは完成形。
  - A8会員ページのDOM（URL・行セレクタ）は環境依存のため、定数 CALIBRATE 節に集約。
    初回だけ  `python a8_sync.py inspect`  でログイン後のページHTML/スクショを
    scratchpad的にカレントへ保存し、実DOMを見て JOINED_PROGRAMS_URL / セレクタを確定する。
  - リンク抽出は px.a8.net の href を正規表現で拾う方式なので、ページ構造変更にも比較的頑健。

前提インストール（初回のみ・x_posterと共通）:
  pip install undetected-chromedriver "setuptools<81"

使い方:
  python a8_sync.py inspect   # 初回較正：ログイン→一覧ページのHTML/スクショ保存
  python a8_sync.py sync      # 本番：リンク取得→affiliate_links.txt更新（→任意でdeploy）
  python a8_sync.py login     # ログイン確認のみ
"""
import os
import re
import sys
import json
import time
import subprocess

import setuptools  # noqa: distutils互換(Python3.14)。uc より前に読み込む
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "a8_config.json")
CARDS_FILE = os.path.join(BASE_DIR, "data", "cards.json")
MAP_FILE = os.path.join(BASE_DIR, "data", "a8_program_map.json")
LINKS_FILE = os.path.join(BASE_DIR, "data", "affiliate_links.txt")
PROFILE_DIR = os.path.join(BASE_DIR, "a8_profile")
LOG_FILE = os.path.join(BASE_DIR, "a8_sync.log")
DEPLOY_PS1 = os.path.join(BASE_DIR, "deploy.ps1")

# ===================== CALIBRATE（初回 inspect で実値に合わせる節）=====================
# A8会員エリアのURL/セレクタ。実DOMを見て必要なら修正する。
A8_LOGIN_URL = "https://www.a8.net/"
# 参加プログラム一覧（提携状況が見えるページ）。inspectで実URLを確認して差し替える。
JOINED_PROGRAMS_URL = "https://pub.a8.net/a8v2/asProgramAttribute.htm"
# 一覧の「次ページ」リンクのテキスト（ページネーション）。無ければ単一ページ扱い。
NEXT_PAGE_TEXT = "次へ"
# プログラム1件を表す行要素のCSS（inspectで確認）。空なら全ページからpxリンクを総取り。
PROGRAM_ROW_CSS = ""
# =====================================================================================

# A8のアフィリンク（テキスト/バナーのクリック先）パターン
PX_LINK_RE = re.compile(r"https?://px\.a8\.net/svt/ejp\?a8mat=[A-Za-z0-9_+/=.\-]+")


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config():
    # 方式A（専用プロファイルに横浜アカウントで初回手動ログイン）では認証情報は必須ではない。
    # config が無くても auto_deploy=false の既定で動作する。
    cfg = {"login_id": "", "password": "", "auto_deploy": False}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    return cfg


# ----------------------------- driver / login -----------------------------

def _chrome_major():
    try:
        out = subprocess.check_output(
            ["reg", "query", r"HKCU\Software\Google\Chrome\BLBeacon", "/v", "version"],
            text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"version\s+REG_SZ\s+(\d+)\.", out)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def make_driver(headless=False):
    os.makedirs(PROFILE_DIR, exist_ok=True)
    opts = uc.ChromeOptions()
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    # ロック画面/証明書対策（既存パターン踏襲）
    opts.add_argument("--ignore-certificate-errors")
    kwargs = dict(options=opts, headless=headless, use_subprocess=True, user_data_dir=PROFILE_DIR)
    major = _chrome_major()
    if major:
        kwargs["version_main"] = major
    return uc.Chrome(**kwargs)


def is_logged_in(driver):
    """A8会員エリアに入れているか判定。ログアウト導線やマイページ要素の有無で判定。"""
    src = driver.page_source
    url = driver.current_url
    # 会員ページは pub.a8.net 配下。ログアウトリンクや「メディア会員」表示があればログイン済み。
    if "pub.a8.net" in url:
        return True
    if "ログアウト" in src or "logout" in src.lower():
        return True
    return False


def _wait_logged_in(driver, wait_seconds):
    for _ in range(max(1, wait_seconds // 5)):
        time.sleep(5)
        try:
            if is_logged_in(driver):
                return True
        except Exception:
            pass
    return False


def login(driver, cfg, wait_seconds=240):
    """A8にログイン。方式A=専用プロファイルに横浜アカウントで初回手動ログイン→セッション保存。
    一度ログインすればプロファイルに残り、次回以降は手動不要で自動再利用される。
    config に login_id/password があれば自動入力を試み、無ければ手動ログインを待つ。
    """
    driver.get(A8_LOGIN_URL)
    time.sleep(4)
    if is_logged_in(driver):
        log("既にログイン済み（セッション再利用・横浜アカウント）")
        return True

    def find_first(css_list):
        for css in css_list:
            els = [e for e in driver.find_elements(By.CSS_SELECTOR, css) if e.is_displayed()]
            if els:
                return els[0]
        return None

    # 認証情報があれば自動入力を試す（任意・便宜用）。無ければ手動ログインへ。
    if cfg.get("login_id") and cfg.get("password"):
        id_box = find_first([
            "input[name='login']", "input#login",
            "input[type='email']", "input[type='text']",
        ])
        pw_box = find_first([
            "input[name='password']", "input#password", "input[type='password']",
        ])
        if id_box and pw_box:
            id_box.clear(); id_box.send_keys(cfg["login_id"])
            pw_box.clear(); pw_box.send_keys(cfg["password"])
            btn = find_first([
                "input[type='submit']", "button[type='submit']",
                "button#submit", ".btnLogin", "input.btnLogin",
            ])
            if btn:
                try:
                    btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", btn)
            else:
                pw_box.submit()
            if _wait_logged_in(driver, 30):
                log("ログイン成功（認証情報・横浜アカウント）")
                return True
            log("自動ログイン未確認（2段階/画像認証の可能性）→手動ログインに切替")

    # 手動ログイン待機（横浜アカウントで初回ログイン→プロファイルに保存）
    log(f"開いたブラウザで A8 に【横浜アカウント】で手動ログインしてください（最大{wait_seconds}秒待機）...")
    if _wait_logged_in(driver, wait_seconds):
        log("ログインを確認・セッション保存OK（次回以降は自動再利用）")
        return True
    log("時間内にログインを確認できませんでした")
    return False


# ----------------------------- 較正(inspect) -----------------------------

def inspect(cfg):
    """初回較正：ログイン→参加プログラム一覧を開き、HTMLとスクショを保存して実DOMを確認可能にする。"""
    driver = make_driver()
    try:
        if not login(driver, cfg):
            log("inspect: ログインできなかったため中断")
            return
        for tag, url in [("login_landing", driver.current_url),
                         ("joined_programs", JOINED_PROGRAMS_URL)]:
            driver.get(url)
            time.sleep(5)
            html_path = os.path.join(BASE_DIR, f"a8_inspect_{tag}.html")
            png_path = os.path.join(BASE_DIR, f"a8_inspect_{tag}.png")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            try:
                driver.save_screenshot(png_path)
            except Exception:
                pass
            n = len(PX_LINK_RE.findall(driver.page_source))
            log(f"inspect[{tag}] url={driver.current_url} px.a8リンク検出数={n} -> {os.path.basename(html_path)}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass


# ----------------------------- リンク収集 / 突合 -----------------------------

def collect_program_links(driver):
    """提携中プログラムの (プログラム名, px.a8リンク) を収集して返す。

    一覧ページ（＋ページネーション）を巡回し、px.a8.net リンクとその近傍テキストを拾う。
    PROGRAM_ROW_CSS が設定されていれば行単位で名前とリンクを対にし、無ければ
    ページ全体から px リンクを総取りして a要素のテキスト/周辺から名前を推定する。
    """
    results = []
    seen = set()
    driver.get(JOINED_PROGRAMS_URL)
    time.sleep(5)

    def harvest():
        if PROGRAM_ROW_CSS:
            rows = driver.find_elements(By.CSS_SELECTOR, PROGRAM_ROW_CSS)
            for r in rows:
                txt = (r.text or "").strip().split("\n")[0]
                links = [a.get_attribute("href") for a in r.find_elements(By.TAG_NAME, "a")]
                for href in links:
                    if href and PX_LINK_RE.match(href) and href not in seen:
                        seen.add(href)
                        results.append((txt, href))
        else:
            # 行セレクタ未確定時の総取り：px リンクを持つ a要素を全部拾う
            for a in driver.find_elements(By.TAG_NAME, "a"):
                href = a.get_attribute("href") or ""
                if PX_LINK_RE.match(href) and href not in seen:
                    seen.add(href)
                    name = (a.text or "").strip()
                    if not name:
                        # 近傍テキストを名前候補に
                        try:
                            name = (a.find_element(By.XPATH, "./ancestor::*[self::tr or self::li or self::div][1]")
                                    .text or "").strip().split("\n")[0]
                        except Exception:
                            name = ""
                    results.append((name, href))

    harvest()
    # ページネーション
    for _ in range(20):
        nexts = [a for a in driver.find_elements(By.PARTIAL_LINK_TEXT, NEXT_PAGE_TEXT) if a.is_displayed()]
        if not nexts:
            break
        try:
            nexts[0].click()
        except Exception:
            break
        time.sleep(4)
        harvest()
    return results


def load_map():
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def match_card_id(program_name, program_url, mapping):
    """A8のプログラム名/URLを creca-labo のカードIDに突合。一致しなければ None。"""
    name = program_name or ""
    for cid, info in mapping.items():
        pid = (info.get("a8_program_id") or "").strip()
        if pid and pid in program_url:
            return cid
        for key in info.get("match", []):
            if key and key in name:
                return cid
    return None


# ----------------------------- affiliate_links.txt 再生成 -----------------------------

def current_overrides():
    """既存 affiliate_links.txt の有効行を {id:url} で読む。"""
    ov = {}
    if not os.path.exists(LINKS_FILE):
        return ov
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()  # URLは空白を含まない→先頭=id, 2番目=url, 以降は行末コメント
            if len(parts) >= 2:
                ov[parts[0].strip()] = parts[1].strip()
    return ov


def write_links_file(overrides):
    """cards.json をテンプレに、overrides({id:url})を反映して affiliate_links.txt を再生成。"""
    d = json.load(open(CARDS_FILE, encoding="utf-8"))
    L = []
    L.append("# =====================================================")
    L.append("#  アフィリエイトリンク上書き表  (creca-labo)")
    L.append("#  形式: <id><空白><url>   （# 始まり・空行は無視）")
    L.append("#  ここに書いた id のリンクが cards.json の affiliate_url を上書きする。")
    L.append("#  未記載のものは公式URL（cards.json）にフォールバック。")
    L.append("#  a8_sync.py がA8承認済みリンクをこのファイルへ自動追記する。")
    L.append("# =====================================================")
    L.append("")

    def emit(title, items):
        L.append(f"# ---- {title} ----")
        for it in items:
            cid = it.get("id")
            if not cid:
                continue
            url = overrides.get(cid)
            if url:
                L.append(f"{cid:20} {url}    # {it.get('name','')}")
            else:
                L.append(f"# {cid:18}    # {it.get('name','')}（未反映・公式URLにフォールバック）")
        L.append("")

    emit("クレジットカード", d.get("cards", []))
    emit("証券", d.get("brokers", []))
    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ----------------------------- 本番 sync -----------------------------

def run_deploy():
    pwsh = r"C:\Program Files\PowerShell\7-preview\pwsh.exe"
    exe = pwsh if os.path.exists(pwsh) else "powershell"
    log("deploy.ps1 を実行...")
    subprocess.run([exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", DEPLOY_PS1],
                   cwd=BASE_DIR)


def sync(cfg):
    mapping = load_map()
    driver = make_driver()
    try:
        if not login(driver, cfg):
            log("sync: ログイン失敗のため中断")
            return
        pairs = collect_program_links(driver)
        log(f"提携中リンク候補 {len(pairs)} 件を取得")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    overrides = current_overrides()  # 既存（楽天など手動分）を保持
    matched, unmatched = 0, []
    for name, url in pairs:
        cid = match_card_id(name, url, mapping)
        if cid:
            overrides[cid] = url
            matched += 1
        else:
            unmatched.append(name or url)

    write_links_file(overrides)
    log(f"反映: {matched}件マッチ / 未マッチ {len(unmatched)}件")
    for u in unmatched:
        log(f"  未マッチ（要a8_program_map.json調整）: {u[:60]}")

    if cfg.get("auto_deploy"):
        run_deploy()
    else:
        log("auto_deploy=false のため反映のみ（手動で deploy.ps1 を実行してください）")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    cfg = load_config()
    if cmd == "inspect":
        inspect(cfg)
    elif cmd == "sync":
        sync(cfg)
    elif cmd == "login":
        d = make_driver()
        try:
            print("RESULT:", login(d, cfg))
        finally:
            try:
                d.quit()
            except Exception:
                pass
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
