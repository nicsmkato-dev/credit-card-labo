# =====================================================
#  creca-labo deploy script (ASCII-only to avoid encoding issues
#  when run by Windows PowerShell 5.1 / scheduled task)
#  Regenerates the site and pushes to GitHub (Cloudflare Pages auto-deploys).
#  Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File deploy.ps1
# =====================================================
$ErrorActionPreference = "Continue"
$SiteDir = "C:\Users\user\Desktop\affiliate-site"
$Python  = "C:\Users\user\AppData\Local\Python\bin\python.exe"
$Log     = "$SiteDir\deploy.log"

function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg"
    Write-Host $line
    Add-Content -Path $Log -Value $line -Encoding UTF8
}

Set-Location $SiteDir
Log "===== deploy start ====="

# Clear any stale git lock from a crashed run
if (Test-Path "$SiteDir\.git\index.lock") {
    Remove-Item "$SiteDir\.git\index.lock" -Force -ErrorAction SilentlyContinue
    Log "removed stale .git/index.lock"
}

Log "[1/3] regenerating site..."
& $Python "$SiteDir\generate.py" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Log "ERROR: generate.py exited $LASTEXITCODE" }

Log "[2/3] committing changes..."
git add -A
$changes = git status --porcelain
if ($changes) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    git -c user.name="creca-labo-bot" -c user.email="nics.m.kato@gmail.com" commit -m "auto update $stamp" 2>&1 | ForEach-Object { Log $_ }
    if ($LASTEXITCODE -ne 0) { Log "ERROR: git commit exited $LASTEXITCODE" }
} else {
    Log "no changes; skipping commit"
}

Log "[3/3] pushing to GitHub..."
$hasRemote = git remote
if ($hasRemote) {
    git push origin main 2>&1 | ForEach-Object { Log $_ }
    if ($LASTEXITCODE -ne 0) {
        Log "ERROR: git push exited $LASTEXITCODE (check credentials / network)"
    } else {
        Log "push OK; Cloudflare Pages will redeploy in a few minutes"
    }
} else {
    Log "ERROR: no git remote configured"
}

Log "===== deploy end ====="
