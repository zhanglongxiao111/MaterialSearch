# MaterialSearch Workspace 桌面版启动脚本
# 双击运行即可启动

Write-Host ""
Write-Host "  ╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║                                            ║" -ForegroundColor Cyan
Write-Host "  ║   MaterialSearch Workspace                 ║" -ForegroundColor Cyan
Write-Host "  ║   SA Architects AI 素材工作站              ║" -ForegroundColor Cyan
Write-Host "  ║                                            ║" -ForegroundColor Cyan
Write-Host "  ╚════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir

Write-Host "[1/2] 启动 AI 后端服务..." -ForegroundColor Yellow

# 启动 Flask 后端
$backendProcess = Start-Process python -ArgumentList "main.py" -WorkingDirectory $ProjectDir -PassThru -WindowStyle Minimized
Write-Host "     后端已启动 (PID: $($backendProcess.Id))" -ForegroundColor Green

# 等待后端就绪
Write-Host "     等待服务就绪" -ForegroundColor Gray -NoNewline
$maxRetries = 30
$retryCount = 0
$ready = $false

while ($retryCount -lt $maxRetries -and -not $ready) {
    Start-Sleep -Milliseconds 500
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:5000/api/status" -TimeoutSec 1 -ErrorAction SilentlyContinue
        $ready = $true
    } catch {
        $retryCount++
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}
Write-Host ""

if ($ready) {
    Write-Host "     后端服务已就绪!" -ForegroundColor Green
} else {
    Write-Host "     后端正在加载模型,请稍候..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/2] 启动桌面界面..." -ForegroundColor Yellow

# 尝试不同位置的 exe
$exePaths = @(
    (Join-Path $ScriptDir "src-tauri\target\release\materialsearch.exe"),
    (Join-Path $ScriptDir "src-tauri\target\debug\materialsearch.exe"),
    (Join-Path $ProjectDir "MaterialSearch.exe")
)

$tauriExe = $null
foreach ($path in $exePaths) {
    if (Test-Path $path) {
        $tauriExe = $path
        break
    }
}

if ($tauriExe) {
    Start-Process $tauriExe -WorkingDirectory $ProjectDir
    Write-Host "     桌面客户端已启动!" -ForegroundColor Green
} else {
    Write-Host "     未找到桌面客户端,使用浏览器..." -ForegroundColor Yellow
    Start-Process "http://localhost:5000/workspace"
}

Write-Host ""
Write-Host "  ────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  提示: 关闭窗口后程序会最小化到系统托盘" -ForegroundColor Gray
Write-Host "  提示: 此窗口关闭将停止后端服务" -ForegroundColor Gray
Write-Host "  ────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# 等待后端进程
try {
    Wait-Process -Id $backendProcess.Id
} catch {}

Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
