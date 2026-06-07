# =====================================================
#  GitHub Pages 公開セットアップ（初回のみ実行）
#
#  事前準備:
#   1. https://github.com/ で無料アカウントを作成
#   2. 新しいリポジトリを作成（例: credit-card-lab）※Publicにすること
#   3. 作成後に表示される URL（例: https://github.com/ユーザー名/credit-card-lab.git）をコピー
#
#  実行方法:
#   pwsh -File setup_github.ps1 -RepoUrl "https://github.com/ユーザー名/credit-card-lab.git"
#
#  実行後:
#   GitHub のリポジトリ → Settings → Pages → Branch を main / (root) に設定して Save
#   数分後に https://ユーザー名.github.io/credit-card-lab/ で公開されます
# =====================================================
param(
    [Parameter(Mandatory=$true)]
    [string]$RepoUrl
)
$ErrorActionPreference = "Stop"
$SiteDir = "C:\Users\user\Desktop\affiliate-site"
Set-Location $SiteDir

Write-Host "リモートリポジトリを設定中: $RepoUrl" -ForegroundColor Cyan
$existing = git remote
if ($existing -contains "origin") {
    git remote set-url origin $RepoUrl
} else {
    git remote add origin $RepoUrl
}

Write-Host "初回 push 中..." -ForegroundColor Cyan
git push -u origin main

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host " push 完了！次の手順で公開を有効化してください:" -ForegroundColor Green
Write-Host " 1. GitHubのリポジトリページを開く" -ForegroundColor Green
Write-Host " 2. Settings → Pages" -ForegroundColor Green
Write-Host " 3. Branch: main / (root) を選び Save" -ForegroundColor Green
Write-Host " 4. 数分後に公開URLが表示されます" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
