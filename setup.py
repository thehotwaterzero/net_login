"""
安装脚本 - 安装 Playwright 浏览器驱动
运行此脚本来完成初始化设置
"""
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

def setup():
    """执行设置步骤"""
    print("=" * 60)
    print("正在安装 Playwright 浏览器驱动...")
    print("=" * 60)
    
    # 设置浏览器下载路径
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 加载 .env 配置文件
    env_file = Path(project_dir) / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print("✓ 已加载 .env 配置文件")
    else:
        print("⚠ 未找到 .env 文件，使用默认配置")
    
    # 从 .env 读取浏览器路径配置
    browsers_path_config = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "browsers")
    
    # 处理相对路径和绝对路径
    if not os.path.isabs(browsers_path_config):
        browsers_path = os.path.join(project_dir, browsers_path_config)
    else:
        browsers_path = browsers_path_config
    
    # 创建目录
    os.makedirs(browsers_path, exist_ok=True)
    
    # 从 .env 读取下载镜像源配置
    download_host = os.getenv("PLAYWRIGHT_DOWNLOAD_HOST", "https://npmmirror.com/mirrors/playwright/")
    
    print(f"浏览器将安装到: {browsers_path}")
    print(f"下载镜像源: {download_host}")
    print()
    
    try:
        # 设置环境变量并安装 Playwright 浏览器
        env = os.environ.copy()
        env["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
        env["PLAYWRIGHT_DOWNLOAD_HOST"] = download_host
        
        # 不捕获输出，让进度信息实时显示
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            env=env
        )
        
        print("\n" + "=" * 60)
        print("✓ Playwright 浏览器驱动安装成功!")
        print(f"✓ 安装位置: {browsers_path}")
        print("=" * 60)
        print("\n设置完成！现在你可以运行程序了:")
        print("  python main.py")
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print(f"✗ 安装失败: {e}")
        print(e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup()
