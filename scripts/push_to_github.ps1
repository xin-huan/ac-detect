# 将 ac-detect 推送到 GitHub（需先完成 gh auth login）
# 用法: powershell -ExecutionPolicy Bypass -File scripts\push_to_github.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "=== 检查 GitHub 登录 ===" -ForegroundColor Cyan
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "请先登录 GitHub：" -ForegroundColor Yellow
    Write-Host "  gh auth login"
    Write-Host "  选择: GitHub.com -> HTTPS -> Login with a web browser"
    exit 1
}

$RepoName = "ac-detect"
$GhUser = (gh api user -q .login)
$RemoteUrl = "https://github.com/$GhUser/$RepoName.git"

Write-Host ""
Write-Host "=== 在 GitHub 创建仓库 $RepoName (私有/公开由 gh 默认) ===" -ForegroundColor Cyan
gh repo view "$GhUser/$RepoName" 2>$null
if ($LASTEXITCODE -ne 0) {
    gh repo create $RepoName --public --source=. --remote=github --description "课堂多模态分析：人脸+声纹+YOLO行为+专注度"
} else {
    Write-Host "仓库已存在，跳过创建。"
    git remote remove github 2>$null
    git remote add github $RemoteUrl
}

Write-Host ""
Write-Host "=== 提交并推送 ===" -ForegroundColor Cyan
git add -A
git status
$msg = "chore: migrate to GitHub, unified ac_detect environment"
git commit -m $msg 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "无新提交或提交失败，继续尝试推送..." }

git push -u github master
if ($LASTEXITCODE -ne 0) { git push -u github master:main }

Write-Host ""
Write-Host "完成: https://github.com/$GhUser/$RepoName" -ForegroundColor Green
Write-Host "原 Gitee 远程仍为 origin，如需仅保留 GitHub 可执行:"
Write-Host "  git remote rename origin gitee"
Write-Host "  git remote rename github origin"
