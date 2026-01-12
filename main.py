import os
import time
import logging
import schedule
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# 加载环境变量（必须在最前面）
load_dotenv('.env', override=True)

# 设置浏览器路径为项目文件夹下的 browsers 目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BROWSERS_PATH = os.path.join(PROJECT_DIR, "browsers")
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = BROWSERS_PATH

# 从 .env 读取 Playwright 下载镜像源配置
DOWNLOAD_HOST = os.getenv("PLAYWRIGHT_DOWNLOAD_HOST", "https://npmmirror.com/mirrors/playwright/")
os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = DOWNLOAD_HOST

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/campus_network_login.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 从 .env 读取所有配置
LOGIN_URL = os.getenv("LOGIN_URL", "https://raas.hzu.edu.cn/")
USERNAME = os.getenv("CAMPUS_USERNAME", "")
PASSWORD = os.getenv("CAMPUS_PASSWORD", "")
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))


class CampusNetworkLogin:
    """校园网自动登录类"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.login_url = LOGIN_URL
    
    def check_network_status(self) -> bool:
        """检查网络连接状态
        
        Returns:
            bool: True表示已登录，False表示未登录
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()
                
                logger.info("正在检查网络状态...")
                page.goto(self.login_url, timeout=10000)
                time.sleep(2)
                
                # 检查是否已经登录（页面显示"注销下线"按钮表示已登录）
                try:
                    logout_button = page.locator("button.loggoff")
                    if logout_button.is_visible(timeout=3000):
                        logger.info("网络已登录，无需重新登录")
                        browser.close()
                        return True
                except:
                    pass
                
                # 检查是否有登录按钮（表示未登录）
                try:
                    login_button = page.locator("div.tab-group.account button.btn")
                    if login_button.is_visible(timeout=3000):
                        logger.info("检测到未登录状态")
                        browser.close()
                        return False
                except:
                    pass
                
                browser.close()
                return False
                
        except Exception as e:
            logger.error(f"检查网络状态时出错: {str(e)}")
            return False
    
    def login(self) -> bool:
        """执行自动登录
        
        Returns:
            bool: 登录成功返回True，失败返回False
        """
        if not self.username or not self.password:
            logger.error("用户名或密码未设置，请配置环境变量 CAMPUS_USERNAME 和 CAMPUS_PASSWORD")
            return False
        
        try:
            with sync_playwright() as p:
                # 启动浏览器（可见模式，方便调试）
                browser = p.chromium.launch(
                    headless=False,  # 设置为True可后台运行
                    slow_mo=500  # 放慢操作速度，模拟人工操作
                )
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    ignore_https_errors=True
                )
                page = context.new_page()
                
                logger.info(f"正在打开登录页面: {self.login_url}")
                page.goto(self.login_url, wait_until='networkidle')
                time.sleep(2)
                
                # 检查是否已经登录
                try:
                    logout_button = page.locator("button.loggoff")
                    if logout_button.is_visible(timeout=2000):
                        logger.info("已处于登录状态，无需重新登录")
                        browser.close()
                        return True
                except:
                    pass
                
                # 确保在账号登录标签页
                account_tab = page.locator("div.tab-group.account")
                if not account_tab.is_visible():
                    # 点击"帐号登录"选项卡
                    account_login_link = page.locator('a:has-text("帐号登录")')
                    if account_login_link.is_visible():
                        account_login_link.click()
                        time.sleep(1)
                
                # 填写用户名
                logger.info("正在填写用户名...")
                username_input = page.locator('input#user')
                username_input.clear()
                username_input.fill(self.username, timeout=5000)
                time.sleep(0.5)
                
                # 填写密码
                logger.info("正在填写密码...")
                password_input = page.locator('input#pass')
                password_input.clear()
                password_input.fill(self.password, timeout=5000)
                time.sleep(0.5)
                
                # 点击登录按钮
                logger.info("正在点击登录按钮...")
                login_button = page.locator("div.tab-group.account button.btn")
                login_button.click()
                
                # 等待登录完成
                time.sleep(3)
                
                # 验证登录是否成功
                try:
                    # 检查是否出现"注销下线"按钮
                    logout_button = page.locator("button.loggoff")
                    if logout_button.is_visible(timeout=5000):
                        logger.info("✓ 登录成功！")
                        time.sleep(2)
                        browser.close()
                        return True
                    else:
                        # 检查是否有错误提示
                        msg_zone = page.locator("div.msg-zone")
                        error_msg = msg_zone.inner_text() if msg_zone.is_visible() else "未知错误"
                        logger.error(f"✗ 登录失败: {error_msg}")
                        browser.close()
                        return False
                except PlaywrightTimeout:
                    logger.error("✗ 登录超时，请检查账号密码是否正确")
                    browser.close()
                    return False
                    
        except Exception as e:
            logger.error(f"登录过程中出错: {str(e)}")
            return False
    
    def auto_check_and_login(self):
        """自动检查并登录"""
        logger.info("="*50)
        logger.info(f"开始执行自动检查 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        
        if not self.check_network_status():
            logger.info("需要登录，开始自动登录流程...")
            self.login()
        else:
            logger.info("当前已登录，无需操作")


def main():
    """主函数"""
    # 创建logs目录
    os.makedirs('logs', exist_ok=True)
    
    # 检查账号密码配置
    username = os.getenv("CAMPUS_USERNAME", "")
    password = os.getenv("CAMPUS_PASSWORD", "")
    
    if not username or not password:
        logger.error("=" * 60)
        logger.error("错误: 未设置账号密码!")
        logger.error("请设置环境变量:")
        logger.error("  CAMPUS_USERNAME=你的学号")
        logger.error("  CAMPUS_PASSWORD=你的密码")
        logger.error("=" * 60)
        return
    
    # 创建登录实例
    campus_login = CampusNetworkLogin(username, password)
    
    # 首次立即执行
    logger.info("程序启动，立即执行首次检查...")
    campus_login.auto_check_and_login()
    
    # 设置定时任务
    schedule.every(CHECK_INTERVAL_SECONDS).seconds.do(campus_login.auto_check_and_login)
    
    logger.info(f"定时任务已设置，每 {CHECK_INTERVAL_SECONDS} 秒检查一次")
    logger.info("按 Ctrl+C 停止程序")
    
    # 持续运行
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次是否有待执行的任务
    except KeyboardInterrupt:
        logger.info("程序已停止")


if __name__ == "__main__":
    main()
