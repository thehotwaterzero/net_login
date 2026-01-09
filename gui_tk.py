"""
校园网自动登录 GUI 版本（tkinter）
使用 tkinter 提供图形化界面
"""
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

import pystray
from PIL import Image, ImageDraw
from dotenv import load_dotenv, set_key
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from ui_layout_tk import MainWindowUI, ConfigDialog
from setup import setup as install_playwright_browsers


class LoginWorker(threading.Thread):
    """登录工作线程"""
    
    def __init__(self, username, password, login_url, on_log, on_status, on_finished):
        super().__init__(daemon=True)
        self.username = username
        self.password = password
        self.login_url = login_url
        self.on_log = on_log
        self.on_status = on_status
        self.on_finished = on_finished
        self.is_running = True
    
    def run(self):
        """执行登录"""
        try:
            self.on_log("="*60)
            self.on_log(f"[{datetime.now().strftime('%H:%M:%S')}] 开始登录流程...")
            self.on_status("正在登录...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, slow_mo=500)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                self.on_log(f"正在打开登录页面: {self.login_url}")
                page.goto(self.login_url, wait_until='networkidle')
                time.sleep(0.3)
                
                # 检查是否已登录
                try:
                    logout_button = page.locator("button.loggoff")
                    if logout_button.is_visible(timeout=2000):
                        self.on_log("✓ 已处于登录状态")
                        browser.close()
                        self.on_finished(True)
                        return
                except:
                    pass
                
                # 填写用户名
                self.on_log("正在填写用户名...")
                username_input = page.locator('input#user')
                username_input.clear()
                username_input.fill(self.username, timeout=5000)
                time.sleep(0.3)
                
                # 填写密码
                self.on_log("正在填写密码...")
                password_input = page.locator('input#pass')
                password_input.clear()
                password_input.fill(self.password, timeout=5000)
                time.sleep(0.3)
                
                # 点击登录按钮
                self.on_log("正在点击登录按钮...")
                login_button = page.locator("div.tab-group.account button.btn")
                login_button.click()
                self.on_log("等待认证完成...")
                time.sleep(3)
                
                # 验证登录结果
                try:
                    logout_button = page.locator("button.loggoff")
                    if logout_button.is_visible(timeout=8000):
                        self.on_log("✅ 登录成功！")
                        time.sleep(0.3)
                        browser.close()
                        self.on_finished(True)
                        return
                    else:
                        msg_zone = page.locator("div.msg-zone")
                        error_msg = msg_zone.inner_text() if msg_zone.is_visible() else "未知错误"
                        self.on_log(f"❌ 登录失败: {error_msg}")
                        browser.close()
                        self.on_finished(False)
                        return
                except PlaywrightTimeout:
                    self.on_log("❌ 登录超时")
                    browser.close()
                    self.on_finished(False)
                    return
        except Exception as e:
            self.on_log(f"❌ 发生错误: {str(e)}")
            self.on_finished(False)


class MonitorWorker(threading.Thread):
    """监控工作线程"""
    
    def __init__(self, login_url, check_interval, on_log, on_status, on_need_login):
        super().__init__(daemon=True)
        self.login_url = login_url
        self.check_interval = check_interval
        self.on_log = on_log
        self.on_status = on_status
        self.on_need_login = on_need_login
        self.is_running = True
    
    def run(self):
        """持续监控"""
        while self.is_running:
            try:
                self.on_log("="*60)
                self.on_log(f"[{datetime.now().strftime('%H:%M:%S')}] 开始检查网络状态...")
                self.on_status("检查中...")
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context()
                    page = context.new_page()
                    
                    page.goto(self.login_url, timeout=10000)
                    time.sleep(0.3)
                    
                    try:
                        logout_button = page.locator("button.loggoff")
                        if logout_button.is_visible(timeout=3000):
                            self.on_log("✓ 网络已登录")
                            self.on_status("监控中 - 已登录")
                            browser.close()
                        else:
                            self.on_log("⚠️ 检测到未登录状态")
                            self.on_status("监控中 - 未登录")
                            browser.close()
                            self.on_need_login()
                    except:
                        login_button = page.locator("div.tab-group.account button.btn")
                        if login_button.is_visible(timeout=3000):
                            self.on_log("⚠️ 检测到未登录状态")
                            browser.close()
                            self.on_need_login()
                        else:
                            browser.close()
            except Exception as e:
                self.on_log(f"⚠️ 检查时出错: {str(e)}")
            
            # 等待下次检查
            for _ in range(self.check_interval):
                if not self.is_running:
                    break
                time.sleep(1)
        
        self.on_log("监控已停止")
    
    def stop(self):
        """停止监控"""
        self.is_running = False


class MainWindow:
    """主窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        
        # 设置环境（支持打包后运行）
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后运行
            self.project_dir = Path(sys.executable).parent
        else:
            # 开发环境运行
            self.project_dir = Path(__file__).parent
        
        self.env_file = self.project_dir / ".env"
        self._setup_environment()
        
        # 创建logs目录
        self.logs_dir = self.project_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # 设置日志文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.logs_dir / f"gui_login_{timestamp}.log"
        
        # 加载配置
        self.load_config()
        
        # 初始化UI
        self.ui = MainWindowUI(self.root)
        
        # 设置窗口图标（同时作用于窗口和任务栏）
        icon_path = self.project_dir / "icon.png"
        if icon_path.exists():
            try:
                icon_img = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon_img)
            except Exception as e:
                print(f"设置窗口图标失败: {e}")
        
        # 连接事件
        self.ui.btn_test_login.config(command=self.test_login)
        self.ui.btn_monitor.config(command=self.toggle_monitor)
        self.ui.btn_config.config(command=self.open_config)
        self.ui.btn_clear_log.config(command=self.clear_log)
        self.ui.btn_install_deps.config(command=self.install_dependencies)
        
        # 工作线程
        self.login_worker = None
        self.monitor_worker = None
        self.is_monitoring = False
        
        # 系统托盘
        self.tray_icon = None
        self.is_quitting = False
        
        # 按钮点击时间记录（防抖）
        self.last_click_time = {
            'test_login': 0,
            'monitor': 0,
            'config': 0,
            'clear_log': 0,
            'install_deps': 0
        }
        self.click_interval = 0.8  # 最短点击间隔（秒）
        
        # 关闭窗口事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 添加欢迎日志
        self.append_log("=" * 60)
        self.append_log("欢迎使用校园网自动登录系统")
        self.append_log("=" * 60)
        
        # 如果已配置账号密码，自动启动监控
        if self.username and self.password:
            self.append_log("检测到已配置账号密码，自动启动监控...")
            self.append_log("")
            # 延迟启动监控，确保UI完全初始化
            self.root.after(500, self.start_monitor)
        else:
            self.append_log("请先点击【打开配置】设置账号密码")
            self.append_log("")
    
    def _setup_environment(self):
        """设置环境变量"""
        # 先加载配置获取 browsers_path
        load_dotenv(self.env_file, override=True)
        browsers_path_config = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "browsers")
        
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(browsers_path_config):
            browsers_path = self.project_dir / browsers_path_config
        else:
            browsers_path = Path(browsers_path_config)
        
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
        os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = "https://npmmirror.com/mirrors/playwright/"
    
    def load_config(self):
        """加载配置"""
        load_dotenv(self.env_file, override=True)
        
        self.username = os.getenv("CAMPUS_USERNAME", "")
        self.password = os.getenv("CAMPUS_PASSWORD", "")
        self.login_url = os.getenv("LOGIN_URL", "https://raas.hzu.edu.cn/")
        self.download_host = os.getenv("PLAYWRIGHT_DOWNLOAD_HOST", "https://npmmirror.com/mirrors/playwright/")
        self.browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "browsers")
        self.check_interval = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))
    
    def save_config(self, config):
        """保存配置到 .env 文件"""
        if not self.env_file.exists():
            self.env_file.touch()
        
        set_key(self.env_file, "CAMPUS_USERNAME", config['username'])
        set_key(self.env_file, "CAMPUS_PASSWORD", config['password'])
        set_key(self.env_file, "LOGIN_URL", config['login_url'])
        set_key(self.env_file, "PLAYWRIGHT_DOWNLOAD_HOST", config['download_host'])
        set_key(self.env_file, "PLAYWRIGHT_BROWSERS_PATH", config['browsers_path'])
        set_key(self.env_file, "CHECK_INTERVAL_SECONDS", config['check_interval'])
        
        os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = config['download_host']
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = config['browsers_path']
        self.load_config()
    
    def append_log(self, message):
        """添加日志到文本框和文件"""
        # 显示到界面（使用 after 确保线程安全）
        self.root.after(0, lambda: self._append_log_ui(message))
        
        # 写入日志文件
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"写入日志文件失败: {e}")
    
    def _append_log_ui(self, message):
        """在UI线程中添加日志"""
        self.ui.log_text.insert(tk.END, message + "\n")
        self.ui.log_text.see(tk.END)
    
    def _create_tray_icon(self):
        """创建系统托盘图标"""
        # 尝试加载 icon.png
        icon_path = self.project_dir / "icon.png"
        
        if icon_path.exists():
            try:
                image = Image.open(icon_path)
                # 调整图标大小为标准尺寸
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"加载图标文件失败: {e}，使用默认图标")
                image = self._create_default_icon()
        else:
            # 如果 icon.png 不存在，使用默认图标
            image = self._create_default_icon()
        
        # 创建托盘菜单
        menu = pystray.Menu(
            pystray.MenuItem('显示主窗口', self._show_window, default=True),
            pystray.MenuItem('退出', self._quit_from_tray)
        )
        
        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            '校园网自动登录',
            image,
            '校园网自动登录',
            menu
        )
    
    def _create_default_icon(self):
        """创建默认图标（当 icon.png 不存在时）"""
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='#1e90ff')
        dc = ImageDraw.Draw(image)
        
        # 画一个简单的网络图标
        dc.ellipse([16, 16, 48, 48], fill='white', outline='white')
        dc.ellipse([28, 28, 36, 36], fill='#1e90ff', outline='#1e90ff')
        
        return image
    
    def _show_window(self, icon=None, item=None):
        """从托盘显示窗口"""
        self.root.after(0, self._do_show_window)
    
    def _do_show_window(self):
        """在主线程中显示窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def _hide_to_tray(self):
        """隐藏窗口到托盘"""
        self.root.withdraw()
        
        if self.tray_icon is None:
            self._create_tray_icon()
        
        # 在新线程中启动托盘图标
        if not self.tray_icon.visible:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def _quit_from_tray(self, icon=None, item=None):
        """从托盘退出"""
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.is_quitting = True
        self.root.after(0, self._do_quit)
    
    def _do_quit(self):
        """执行退出"""
        if self.monitor_worker and self.monitor_worker.is_alive():
            self.monitor_worker.stop()
        
        self.root.destroy()
    
    def clear_log(self):
        """清空日志"""
        if not self._check_click_interval('clear_log'):
            return
        self.ui.log_text.delete(1.0, tk.END)
        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] 日志已清空")
    
    def update_status(self, status):
        """更新状态标签"""
        self.root.after(0, lambda: self.ui.status_label.config(text=f"状态: {status}"))
    
    def _check_click_interval(self, button_name):
        """检查按钮点击间隔
        
        Args:
            button_name: 按钮名称
            
        Returns:
            bool: True 允许点击，False 间隔太短
        """
        current_time = time.time()
        last_time = self.last_click_time.get(button_name, 0)
        
        if current_time - last_time < self.click_interval:
            return False
        
        self.last_click_time[button_name] = current_time
        return True
    
    def test_login(self):
        """测试登录"""
        if not self._check_click_interval('test_login'):
            return
        
        # 检查浏览器依赖是否已安装
        if not check_browser_installed():
            messagebox.showwarning(
                "浏览器未安装",
                "检测到 Playwright 浏览器驱动未安装。\n\n"
                "请点击【📦 安装依赖】按钮进行安装。\n\n"
                "安装后即可正常使用登录功能。"
            )
            return
        
        if not self.username or not self.password:
            messagebox.showwarning("配置错误", "请先配置账号密码！")
            return
        
        if self.login_worker and self.login_worker.is_alive():
            messagebox.showinfo("提示", "登录任务正在进行中...")
            return
        
        self.ui.btn_test_login.config(state=tk.DISABLED)
        self.ui.btn_monitor.config(state=tk.DISABLED)
        self.ui.btn_config.config(state=tk.DISABLED)
        self.ui.btn_install_deps.config(state=tk.DISABLED)
        
        self.login_worker = LoginWorker(
            self.username, self.password, self.login_url,
            self.append_log, self.update_status, self.on_login_finished
        )
        self.login_worker.start()
    
    def on_login_finished(self, success):
        """登录完成"""
        def restore_buttons():
            self.ui.btn_test_login.config(state=tk.NORMAL)
            self.ui.btn_monitor.config(state=tk.NORMAL)
            self.ui.btn_config.config(state=tk.NORMAL)
            self.ui.btn_install_deps.config(state=tk.NORMAL)
        
        self.root.after(0, restore_buttons)
        if success:
            self.update_status("登录成功")
        else:
            self.update_status("登录失败")
    
    def toggle_monitor(self):
        """切换监控状态"""
        if not self._check_click_interval('monitor'):
            return
        if self.is_monitoring:
            self.stop_monitor()
        else:
            self.start_monitor()
    
    def start_monitor(self):
        """开始监控"""
        # 检查浏览器依赖是否已安装
        if not check_browser_installed():
            messagebox.showwarning(
                "浏览器未安装",
                "检测到 Playwright 浏览器驱动未安装。\n\n"
                "请点击【📦 安装依赖】按钮进行安装。\n\n"
                "安装后即可正常使用监控功能。"
            )
            return
        
        if not self.username or not self.password:
            messagebox.showwarning("配置错误", "请先配置账号密码！")
            return
        
        self.append_log("=" * 60)
        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] 启动监控...")
        self.append_log(f"检查间隔: {self.check_interval} 秒")
        
        self.is_monitoring = True
        self.ui.btn_monitor.config(text="⏸ 停止监控")
        self.ui.btn_test_login.config(state=tk.DISABLED)
        self.ui.btn_config.config(state=tk.DISABLED)
        self.ui.btn_install_deps.config(state=tk.DISABLED)
        self.update_status("监控中...")
        
        self.monitor_worker = MonitorWorker(
            self.login_url, self.check_interval,
            self.append_log, self.update_status, self.auto_login
        )
        self.monitor_worker.start()
    
    def stop_monitor(self):
        """停止监控"""
        if self.monitor_worker:
            self.monitor_worker.stop()
        
        self.is_monitoring = False
        self.ui.btn_monitor.config(text="▶ 开始监控")
        self.ui.btn_test_login.config(state=tk.NORMAL)
        self.ui.btn_config.config(state=tk.NORMAL)
        self.ui.btn_install_deps.config(state=tk.NORMAL)
        self.update_status("监控已停止")
        self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] 监控已停止")
    
    def auto_login(self):
        """自动登录（由监控线程触发）"""
        self.append_log("触发自动登录...")
        
        if self.login_worker and self.login_worker.is_alive():
            self.append_log("登录任务正在进行中，跳过本次...")
            return
        
        self.login_worker = LoginWorker(
            self.username, self.password, self.login_url,
            self.append_log, self.update_status, self.on_auto_login_finished
        )
        self.login_worker.start()
    
    def on_auto_login_finished(self, success):
        """自动登录完成"""
        if success:
            self.update_status("监控中 - 已登录")
        else:
            self.update_status("监控中 - 登录失败")
    
    def open_config(self):
        """打开配置对话框"""
        if not self._check_click_interval('config'):
            return
        
        dialog = ConfigDialog(self.root)
        
        dialog.set_values({
            'username': self.username,
            'password': self.password,
            'login_url': self.login_url,
            'download_host': self.download_host,
            'browsers_path': self.browsers_path,
            'check_interval': self.check_interval
        })
        
        config = dialog.show()
        
        if config:
            # 验证配置
            if not config['username'] or not config['password']:
                messagebox.showwarning("配置错误", "账号和密码不能为空！")
                return
            
            try:
                interval = int(config['check_interval'])
                if interval < 10:
                    messagebox.showwarning("配置错误", "检查间隔不能小于 10 秒！")
                    return
            except ValueError:
                messagebox.showwarning("配置错误", "检查间隔必须是数字！")
                return
            
            # 保存配置
            self.save_config(config)
            
            self.append_log("=" * 60)
            self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] 配置已保存")
            self.append_log(f"账号: {config['username']}")
            self.append_log(f"登录地址: {config['login_url']}")
            self.append_log(f"检查间隔: {config['check_interval']} 秒")
            self.append_log("=" * 60)
            
            messagebox.showinfo("成功", "配置已保存！")
    
    def install_dependencies(self):
        """安装 Playwright 浏览器依赖"""
        reply = messagebox.askyesno(
            "安装依赖",
            "即将安装 Playwright 浏览器驱动（约 170 MB）。\n\n"
            "使用国内镜像加速下载，请查看日志窗口了解进度。\n\n"
            "是否继续？"
        )
        
        if reply:
            self.append_log("=" * 60)
            self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] 开始安装 Playwright 浏览器驱动...")
            self.append_log("=" * 60)
            
            self.ui.btn_install_deps.config(state=tk.DISABLED, text="安装中...")
            self.update_status("正在安装依赖...")
            
            # 在新线程中执行安装
            threading.Thread(target=self._do_install_dependencies, daemon=True).start()
    
    def _do_install_dependencies(self):
        """执行安装依赖，实时显示进度"""
        import subprocess
        
        try:
            # 设置浏览器下载路径
            browsers_path_config = self.browsers_path
            
            # 处理相对路径和绝对路径
            if not os.path.isabs(browsers_path_config):
                browsers_path = self.project_dir / browsers_path_config
            else:
                browsers_path = Path(browsers_path_config)
            
            # 创建目录
            browsers_path.mkdir(parents=True, exist_ok=True)
            
            self.append_log(f"浏览器将安装到: {browsers_path}")
            self.append_log(f"下载镜像源: {self.download_host}")
            self.append_log("")
            
            # 设置环境变量
            env = os.environ.copy()
            env["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
            env["PLAYWRIGHT_DOWNLOAD_HOST"] = self.download_host
            
            # 构建安装命令
            if getattr(sys, 'frozen', False):
                # 打包后的环境
                self.append_log("检测到打包环境，使用内置 playwright 驱动...")
                
                # 在打包环境中，playwright驱动位于 _internal/playwright/driver 目录
                exe_dir = Path(sys.executable).parent
                internal_dir = exe_dir / "_internal"
                
                # 尝试多个可能的路径
                driver_paths = [
                    internal_dir / "playwright" / "driver" / "node.exe",  # 正确的node.exe路径
                    internal_dir / "playwright" / "driver" / "package" / "lib" / "cli" / "cli.js",  # CLI脚本
                ]
                
                driver_executable = None
                for path in driver_paths:
                    if path.exists():
                        driver_executable = path
                        self.append_log(f"找到驱动: {driver_executable}")
                        break
                
                if driver_executable is None:
                    self.append_log("❌ 未找到playwright驱动文件")
                    raise FileNotFoundError("未找到playwright驱动文件")
                
                # 使用node.exe执行playwright CLI
                node_exe = internal_dir / "playwright" / "driver" / "node.exe"
                cli_js = internal_dir / "playwright" / "driver" / "package" / "cli.js"
                
                if node_exe.exists() and cli_js.exists():
                    cmd = [str(node_exe), str(cli_js), "install", "chromium"]
                    env_to_use = env
                    self.append_log(f"使用 node.exe 执行安装")
                else:
                    self.append_log("❌ 缺少必要的驱动文件")
                    raise FileNotFoundError(f"node.exe或cli.js不存在: node={node_exe.exists()}, cli={cli_js.exists()}")
            else:
                # 开发环境
                cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
                env_to_use = env
            
            self.append_log(f"执行命令: {' '.join(cmd)}")
            self.append_log("")
            
            # 实时执行命令并捕获输出
            process = subprocess.Popen(
                cmd,
                env=env_to_use,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 实时读取输出
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.append_log(line.rstrip())
            
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                self.append_log("")
                self.append_log("=" * 60)
                self.append_log("✅ Playwright 浏览器驱动安装成功！")
                self.append_log(f"✅ 安装位置: {browsers_path}")
                self.append_log("=" * 60)
                
                self.root.after(0, lambda: messagebox.showinfo("安装完成", "Playwright 浏览器驱动安装成功！"))
                self.update_status("依赖安装完成")
            else:
                self.append_log("")
                self.append_log(f"❌ 安装失败，退出码: {return_code}")
                self.root.after(0, lambda: messagebox.showerror(
                    "安装失败",
                    f"安装失败，退出码: {return_code}\n\n请查看日志了解详细错误信息。"
                ))
                self.update_status("依赖安装失败")
            
        except Exception as e:
            self.append_log("")
            self.append_log(f"❌ 安装失败: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "安装失败",
                f"安装失败：{str(e)}\n\n请查看日志了解详细错误信息。"
            ))
            self.update_status("依赖安装失败")
        
        finally:
            self.root.after(0, lambda: self.ui.btn_install_deps.config(state=tk.NORMAL, text="📦 安装依赖"))
    
    def on_closing(self):
        """关闭窗口事件"""
        if self.is_quitting:
            return
        
        # 弹出对话框询问用户
        dialog = tk.Toplevel(self.root)
        dialog.title("关闭选项")
        dialog.geometry("350x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (150 // 2)
        dialog.geometry(f"350x150+{x}+{y}")
        
        result = {'action': None}
        
        def on_minimize():
            result['action'] = 'minimize'
            dialog.destroy()
        
        def on_quit():
            result['action'] = 'quit'
            dialog.destroy()
        
        def on_cancel():
            result['action'] = 'cancel'
            dialog.destroy()
        
        # 创建对话框内容
        from tkinter import ttk
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="选择关闭方式：",
            font=("微软雅黑", 10)
        ).pack(pady=(0, 15))
        
        button_frame = ttk.Frame(frame)
        button_frame.pack()
        
        ttk.Button(
            button_frame,
            text="⚫ 最小化到托盘",
            command=on_minimize,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="❌ 退出程序",
            command=on_quit,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            frame,
            text="取消",
            command=on_cancel
        ).pack(pady=(15, 0))
        
        # 等待对话框关闭
        dialog.wait_window()
        
        # 根据用户选择执行操作
        if result['action'] == 'minimize':
            self._hide_to_tray()
            self.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] 已最小化到系统托盘")
        elif result['action'] == 'quit':
            self.is_quitting = True
            if self.tray_icon:
                self.tray_icon.stop()
            if self.monitor_worker and self.monitor_worker.is_alive():
                self.monitor_worker.stop()
            self.root.destroy()
    
    def run(self):
        """运行主循环"""
        self.root.mainloop()


def check_browser_installed():
    """检查 Playwright 浏览器是否已安装"""
    # 支持打包后运行
    if getattr(sys, 'frozen', False):
        project_dir = Path(sys.executable).parent
    else:
        project_dir = Path(__file__).parent
    
    env_file = project_dir / ".env"
    
    # 加载配置获取 browsers_path
    if env_file.exists():
        load_dotenv(env_file, override=True)
    
    browsers_path_config = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "browsers")
    
    # 处理相对路径和绝对路径
    if not os.path.isabs(browsers_path_config):
        browsers_path = project_dir / browsers_path_config
    else:
        browsers_path = Path(browsers_path_config)
    
    if browsers_path.exists():
        chromium_dirs = list(browsers_path.glob("chromium-*"))
        if chromium_dirs:
            return True
    return False


def main():
    """主函数"""
    # 直接创建并运行主窗口，不检查浏览器是否已安装
    # 用户可以通过界面上的"安装依赖"按钮手动安装浏览器驱动
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
