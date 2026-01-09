"""
打包脚本 - 自动化打包流程
使用 PyInstaller 将程序打包成 Windows 可执行文件

使用方法:
    python build.py
    或
    uv run python build.py
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_step(message):
    """打印步骤信息"""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60)


def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装 (版本: {PyInstaller.__version__})")
        return True
    except ImportError:
        return False


def install_pyinstaller():
    """安装 PyInstaller"""
    print_step("安装 PyInstaller")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            check=True
        )
        print("✓ PyInstaller 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller 安装失败: {e}")
        return False


def create_env_example():
    """创建 .env.example 配置模板"""
    print_step("创建配置文件模板")
    
    env_example = """# 校园网自动登录配置文件
# 首次使用请将此文件重命名为 .env 并填写您的账号密码

# 账号密码（必填）
CAMPUS_USERNAME=
CAMPUS_PASSWORD=

# 登录地址
LOGIN_URL=https://raas.hzu.edu.cn/

# Playwright 下载镜像源（国内加速）
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# 浏览器驱动存放路径（相对路径或绝对路径）
PLAYWRIGHT_BROWSERS_PATH=browsers

# 网络检查间隔（秒）
CHECK_INTERVAL_SECONDS=30
"""
    
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_example)
    
    print("✓ .env.example 创建成功")


def create_readme():
    """创建使用说明文件"""
    print_step("创建使用说明")
    
    readme = """校园网自动登录工具
==================

## 首次使用

1. 将 .env.example 重命名为 .env
2. 编辑 .env 文件，填写您的账号密码
3. 双击运行 校园网自动登录.exe
4. 首次运行会自动下载浏览器驱动（约 170 MB，使用国内镜像加速）

## 功能说明

- 🔐 测试登录：手动测试登录功能
- ▶ 开始监控：自动监控网络状态，断线自动重连
- ⚙ 打开配置：修改账号密码和其他设置
- 📦 安装依赖：手动安装浏览器驱动
- 🗑 清空日志：清空日志窗口
- ⚫ 最小化到托盘：点击关闭按钮时可选择最小化到系统托盘

## 目录说明

- 校园网自动登录.exe：主程序
- _internal/：程序依赖文件（由 PyInstaller 生成）
- browsers/：浏览器驱动文件夹（首次运行自动创建）
- logs/：日志文件夹（自动创建）
- .env：配置文件（需要手动创建）

## 注意事项

- 首次运行需要联网下载浏览器驱动
- Windows Defender 可能误报，请添加信任
- 监控模式下会定期检查网络状态并自动登录
- 日志文件保存在 logs 目录下

## 常见问题

### 程序无法启动？
- 检查是否被杀毒软件拦截
- 查看 logs 目录下的日志文件

### 浏览器驱动下载失败？
- 检查网络连接
- 手动点击"安装依赖"按钮重试
- 修改 .env 中的 PLAYWRIGHT_DOWNLOAD_HOST 镜像源

### 登录失败？
- 检查账号密码是否正确
- 检查登录地址是否正确
- 查看日志了解详细错误信息

## 技术支持

如有问题，请查看日志文件或联系开发者。
"""
    
    with open("README.txt", "w", encoding="utf-8") as f:
        f.write(readme)
    
    print("✓ README.txt 创建成功")


def run_pyinstaller():
    """运行 PyInstaller 打包"""
    print_step("开始打包程序")
    
    try:
        # 使用 spec 文件打包
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "build.spec", "--clean"],
            check=True
        )
        print("\n✓ 打包成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        return False


def organize_output():
    """整理输出文件"""
    print_step("整理输出文件")
    
    dist_dir = Path("dist/校园网自动登录")
    
    if not dist_dir.exists():
        print("✗ 输出目录不存在")
        return False
    
    # 复制配置模板
    if Path(".env.example").exists():
        shutil.copy(".env.example", dist_dir / ".env.example")
        print("✓ 已复制 .env.example")
    
    # 复制使用说明
    if Path("README.txt").exists():
        shutil.copy("README.txt", dist_dir / "README.txt")
        print("✓ 已复制 README.txt")
    
    # 创建空的 logs 目录
    logs_dir = dist_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    print("✓ 已创建 logs 目录")
    
    # 创建一个说明文件告诉用户如何开始
    quick_start = """快速开始
========

1. 将 .env.example 重命名为 .env
2. 用记事本打开 .env，填写您的账号密码
3. 双击运行 校园网自动登录.exe
4. 首次运行会提示安装浏览器驱动（约 170MB）

详细说明请查看 README.txt
"""
    
    with open(dist_dir / "快速开始.txt", "w", encoding="utf-8") as f:
        f.write(quick_start)
    print("✓ 已创建快速开始说明")
    
    print("\n" + "=" * 60)
    print(f"  打包完成！输出目录：")
    print(f"  {dist_dir.absolute()}")
    print("=" * 60)
    
    return True


def clean_build():
    """清理构建文件"""
    print_step("清理构建文件")
    
    dirs_to_clean = ["build", "__pycache__"]
    files_to_clean = ["*.pyc", "*.spec~"]
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"✓ 已删除 {dir_name}")
    
    print("✓ 清理完成")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  校园网自动登录 - 打包脚本")
    print("=" * 60)
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        print("⚠ PyInstaller 未安装")
        reply = input("是否现在安装？(y/n): ").lower()
        if reply == 'y':
            if not install_pyinstaller():
                print("\n✗ 打包失败：无法安装 PyInstaller")
                sys.exit(1)
        else:
            print("\n提示：请先安装 PyInstaller")
            print("命令：pip install pyinstaller")
            print("或：  uv pip install pyinstaller")
            sys.exit(1)
    
    # 创建配置文件
    create_env_example()
    
    # 创建使用说明
    create_readme()
    
    # 运行打包
    if not run_pyinstaller():
        print("\n✗ 打包失败！")
        sys.exit(1)
    
    # 整理输出
    if not organize_output():
        print("\n⚠ 输出文件整理失败")
    
    # 清理构建文件
    clean_build()
    
    print("\n" + "=" * 60)
    print("  🎉 打包完成！")
    print("=" * 60)
    print("\n下一步：")
    print("  1. 进入 dist/校园网自动登录 目录")
    print("  2. 阅读 快速开始.txt")
    print("  3. 配置 .env 文件")
    print("  4. 运行 校园网自动登录.exe")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ 用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
