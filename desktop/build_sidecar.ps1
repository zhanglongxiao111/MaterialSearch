# MaterialSearch 桌面版后端打包脚本
# 使用 PyInstaller 将 Python 后端打包为独立可执行文件
# 
# 使用方法：
#   1. 在项目根目录运行：.\desktop\build_sidecar.ps1
#   2. 输出文件：desktop\src-tauri\binaries\materialsearch-server-x86_64-pc-windows-msvc.exe
#
# Tauri Sidecar 命名规范：
#   <sidecar-name>-<target-triple>.exe
#   例如：materialsearch-server-x86_64-pc-windows-msvc.exe

param(
    [switch]$Clean,      # 清理之前的构建
    [switch]$OneFile,    # 单文件模式（体积大但便携）
    [switch]$Debug       # 调试模式（显示控制台窗口）
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  MaterialSearch Sidecar 构建脚本                              ║" -ForegroundColor Cyan
Write-Host "║  将 Python 后端打包为 Tauri Sidecar 可执行文件                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 确定目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$DesktopDir = $ScriptDir
$BinariesDir = Join-Path $DesktopDir "src-tauri\binaries"
$DistDir = Join-Path $DesktopDir "dist"
$BuildDir = Join-Path $DesktopDir "build"

# Tauri Sidecar 目标三元组
$TargetTriple = "x86_64-pc-windows-msvc"
$SidecarName = "materialsearch-server"
$OutputName = "$SidecarName-$TargetTriple.exe"

Write-Host "[信息] 项目目录: $ProjectDir" -ForegroundColor Gray
Write-Host "[信息] 输出目录: $BinariesDir" -ForegroundColor Gray
Write-Host "[信息] 目标文件: $OutputName" -ForegroundColor Gray
Write-Host ""

# 清理旧构建
if ($Clean) {
    Write-Host "[1/5] 清理旧构建文件..." -ForegroundColor Yellow
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    Write-Host "      已清理" -ForegroundColor Green
} else {
    Write-Host "[1/5] 跳过清理（使用 -Clean 参数强制清理）" -ForegroundColor Gray
}

# 检查 PyInstaller
Write-Host "[2/5] 检查 PyInstaller..." -ForegroundColor Yellow
$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Host "      未找到 PyInstaller，正在安装..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      安装 PyInstaller 失败！" -ForegroundColor Red
        exit 1
    }
}
Write-Host "      PyInstaller 已就绪" -ForegroundColor Green

# 确保 binaries 目录存在
if (-not (Test-Path $BinariesDir)) {
    New-Item -ItemType Directory -Path $BinariesDir -Force | Out-Null
}

# 构建 PyInstaller 参数
Write-Host "[3/5] 准备 PyInstaller 配置..." -ForegroundColor Yellow

$PyInstallerArgs = @(
    "--name", $SidecarName,
    "--distpath", $DistDir,
    "--workpath", $BuildDir,
    "--specpath", $DesktopDir,
    # 数据文件（相对于项目根目录）
    "--add-data", "$ProjectDir\static;static",
    "--add-data", "$ProjectDir\templates;templates",
    # 隐式导入（PyInstaller 可能检测不到的模块）
    "--hidden-import", "flask",
    "--hidden-import", "werkzeug",
    "--hidden-import", "jinja2",
    "--hidden-import", "PIL",
    "--hidden-import", "cv2",
    "--hidden-import", "torch",
    "--hidden-import", "transformers",
    "--hidden-import", "sentence_transformers",
    "--hidden-import", "sklearn.utils._cython_blas",
    "--hidden-import", "sklearn.neighbors.typedefs",
    # 排除不需要的模块（减小体积）
    "--exclude-module", "tkinter",
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy.spatial.cKDTree",
    # 其他选项
    "--noconfirm",
    "--clean"
)

# 单文件 vs 目录模式
if ($OneFile) {
    $PyInstallerArgs += "--onefile"
    Write-Host "      模式: 单文件打包（体积较大，约 2-3GB）" -ForegroundColor Gray
} else {
    $PyInstallerArgs += "--onedir"
    Write-Host "      模式: 目录打包（启动更快，推荐）" -ForegroundColor Gray
}

# 调试 vs 发布模式
if ($Debug) {
    $PyInstallerArgs += "--console"
    Write-Host "      类型: 调试版（显示控制台窗口）" -ForegroundColor Gray
} else {
    $PyInstallerArgs += "--windowed"
    Write-Host "      类型: 发布版（隐藏控制台窗口）" -ForegroundColor Gray
}

# 入口脚本（最后一个参数）
$PyInstallerArgs += (Join-Path $DesktopDir "main_desktop.py")

Write-Host "      配置完成" -ForegroundColor Green

# 执行打包
Write-Host "[4/5] 开始 PyInstaller 打包..." -ForegroundColor Yellow
Write-Host "      这可能需要几分钟，请耐心等待..." -ForegroundColor Gray
Write-Host ""

Push-Location $ProjectDir
try {
    # 构建完整的参数字符串
    $ArgsString = $PyInstallerArgs -join " "
    Write-Host "      命令: pyinstaller $ArgsString" -ForegroundColor DarkGray
    
    # 使用 Invoke-Expression 执行
    $cmd = "pyinstaller $ArgsString"
    Invoke-Expression $cmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "      PyInstaller 打包失败！" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}
catch {
    Write-Host "      错误: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "      打包完成" -ForegroundColor Green

# 复制到 Tauri binaries 目录
Write-Host "[5/5] 部署到 Tauri binaries 目录..." -ForegroundColor Yellow

if ($OneFile) {
    # 单文件模式：直接复制 exe
    $SourceExe = Join-Path $DistDir "$SidecarName.exe"
    $TargetExe = Join-Path $BinariesDir $OutputName
    
    if (Test-Path $SourceExe) {
        Copy-Item -Path $SourceExe -Destination $TargetExe -Force
        Write-Host "      已复制: $OutputName" -ForegroundColor Green
    } else {
        Write-Host "      错误: 未找到打包输出 $SourceExe" -ForegroundColor Red
        exit 1
    }
} else {
    # 目录模式：复制整个目录并重命名主 exe
    $SourceDir = Join-Path $DistDir $SidecarName
    $TargetDir = Join-Path $BinariesDir $SidecarName
    
    if (Test-Path $SourceDir) {
        # 清理旧目录
        if (Test-Path $TargetDir) {
            Remove-Item -Recurse -Force $TargetDir
        }
        
        # 复制目录
        Copy-Item -Path $SourceDir -Destination $TargetDir -Recurse -Force
        
        # 重命名主 exe 以符合 Tauri 命名规范
        $SourceExe = Join-Path $TargetDir "$SidecarName.exe"
        $TargetExe = Join-Path $BinariesDir $OutputName
        
        if (Test-Path $SourceExe) {
            Copy-Item -Path $SourceExe -Destination $TargetExe -Force
            Write-Host "      已复制目录: $SidecarName\" -ForegroundColor Green
            Write-Host "      主程序: $OutputName" -ForegroundColor Green
        }
    } else {
        Write-Host "      错误: 未找到打包输出目录 $SourceDir" -ForegroundColor Red
        exit 1
    }
}

# 完成
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  构建成功！                                                   ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "输出文件:" -ForegroundColor White
Write-Host "  $BinariesDir\$OutputName" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor White
Write-Host "  1. 测试 Sidecar: .\$OutputName" -ForegroundColor Gray
Write-Host "  2. 构建 Tauri:  cd src-tauri && cargo tauri build" -ForegroundColor Gray
Write-Host ""
