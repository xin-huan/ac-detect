# 创建 ac-detect 统一 Conda 环境
# 用法: powershell -ExecutionPolicy Bypass -File scripts/setup_env.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EnvFile = Join-Path $ProjectRoot "envs\ac_detect.yml"
$EnvName = "ac_detect"

Write-Host "=== ac-detect 环境安装 ===" -ForegroundColor Cyan
Write-Host "项目目录: $ProjectRoot"

$CondaExe = $null
if (Get-Command conda -ErrorAction SilentlyContinue) { $CondaExe = "conda" }
elseif (Test-Path "C:\Users\80943\anaconda3\Scripts\conda.exe") { $CondaExe = "C:\Users\80943\anaconda3\Scripts\conda.exe" }
if (-not $CondaExe) {
    Write-Error "未找到 conda，请先安装 Anaconda/Miniconda。"
}

$existing = & $CondaExe env list 2>$null | Select-String "^\s*$EnvName\s"
if ($existing) {
    Write-Host "环境 '$EnvName' 已存在。若要重建请先执行: conda env remove -n $EnvName" -ForegroundColor Yellow
} else {
  Write-Host "从 $EnvFile 创建环境（约 15-30 分钟）..." -ForegroundColor Green
  & $CondaExe env create -f $EnvFile -n $EnvName
}

Write-Host ""
Write-Host "=== 下一步 ===" -ForegroundColor Cyan
Write-Host "  conda activate $EnvName"
Write-Host "  在项目根目录创建 .env 并设置 HF_TOKEN=你的HuggingFace令牌"
Write-Host "  python app.py"
Write-Host ""
Write-Host "模型说明（首次运行自动下载）:" -ForegroundColor Gray
Write-Host "  - InsightFace buffalo_l  (~/.insightface)"
Write-Host "  - YOLO best.pt            (项目根目录)"
Write-Host "  - Whisper medium          (voice_system)"
Write-Host "  - pyannote 说话人分离/声纹  (需 HF_TOKEN 并接受模型协议)"
