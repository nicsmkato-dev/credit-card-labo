# =====================================================
#  クレカ比較ラボ デプロイスクリプト
#  サイトを再生成し、GitHub に push する（GitHub Pages で公開）
#  使い方:  pwsh -File deploy.ps1
# =====================================================
$ErrorActionPreference = "Stop"
$SiteDir = "C:\Users\user\Desktop\affiliate-site"
$Python  = "C:\Users\user\AppData\Local\Python\bin\python.exe"

Set-Location $SiteDir

Write-Host "[1/3] サイトを再生成中..." -ForegroundColor Cyan
& $Python "$SiteDir\generate.py"

Write-Host "[2/3] 変更をコミット中..." -ForegroundColor Cyan
git add -A
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
# 変更がある場合のみコミット
$changes = git status --porcelain
if ($changes) {
    git -c user.name="クレカ比較ラボ" -c user.email="nics.m.kato@gmail.com" commit -m "自動更新 $stamp"
} else {
    Write-Host "  変更なし。コミットをスキップします。" -ForegroundColor Yellow
}

Write-Host "[3/3] GitHub へ push 中..." -ForegroundColor Cyan
$hasRemote = git remote
if ($hasRemote) {
    git push origin main
    Write-Host "完了！数分後に GitHub Pages に反映されます。" -ForegroundColor Green
} else {
    Write-Host "リモートが未設定です。まず setup_github.ps1 を実行してください。" -ForegroundColor Yellow
}
