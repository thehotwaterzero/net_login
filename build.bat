@echo off
chcp 65001 >nul
echo ============================================================
echo   校园网自动登录 - 打包脚本 (使用 uv)
echo ============================================================
echo.

REM 检查是否安装了 uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 未检测到 uv 工具
    echo.
    echo 请先安装 uv：
    echo   https://docs.astral.sh/uv/
    echo.
    pause
    exit /b 1
)

echo ✓ 检测到 uv 工具
echo.

REM 确保虚拟环境存在并同步依赖
echo [1/4] 同步依赖...
echo ------------------------------------------------------------
uv sync
if %errorlevel% neq 0 (
    echo.
    echo ✗ 依赖同步失败
    pause
    exit /b 1
)
echo.

REM 安装 PyInstaller
echo [2/4] 安装 PyInstaller...
echo ------------------------------------------------------------
uv pip install pyinstaller
if %errorlevel% neq 0 (
    echo.
    echo ✗ PyInstaller 安装失败
    pause
    exit /b 1
)
echo.

REM 运行打包脚本
echo [3/4] 执行打包...
echo ------------------------------------------------------------
uv run python build.py
if %errorlevel% neq 0 (
    echo.
    echo ✗ 打包失败
    pause
    exit /b 1
)
echo.

REM 完成
echo [4/4] 完成
echo ============================================================
echo   🎉 打包成功！
echo ============================================================
echo.
echo 输出目录: dist\校园网自动登录
echo.
echo 按任意键打开输出目录...
pause >nul
explorer "dist\校园网自动登录"
