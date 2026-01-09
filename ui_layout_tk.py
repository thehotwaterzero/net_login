"""
UI 布局文件 - 使用 tkinter
定义主界面和配置界面的布局
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class MainWindowUI:
    """主窗口UI布局"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("校园网自动登录")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建 PanedWindow 实现可调整大小的布局
        self.paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧面板
        self.left_panel = self._create_left_panel()
        self.paned.add(self.left_panel, weight=1)
        
        # 右侧面板
        self.right_panel = self._create_right_panel()
        self.paned.add(self.right_panel, weight=3)
    
    def _create_left_panel(self):
        """创建左侧按钮面板"""
        panel = ttk.Frame(self.paned)
        
        # 标题
        title_label = ttk.Label(panel, text="控制面板", font=("Microsoft YaHei", 12, "bold"))
        title_label.pack(pady=10)
        
        # 测试登录按钮
        self.btn_test_login = ttk.Button(panel, text="🔐 测试登录")
        self.btn_test_login.pack(fill=tk.X, padx=5, pady=5, ipady=10)
        
        # 开始/停止监控按钮
        self.btn_monitor = ttk.Button(panel, text="▶ 开始监控")
        self.btn_monitor.pack(fill=tk.X, padx=5, pady=5, ipady=10)
        
        # 打开配置按钮
        self.btn_config = ttk.Button(panel, text="⚙️ 打开配置")
        self.btn_config.pack(fill=tk.X, padx=5, pady=5, ipady=10)
        
        # 清空日志按钮
        self.btn_clear_log = ttk.Button(panel, text="🧹 清空日志")
        self.btn_clear_log.pack(fill=tk.X, padx=5, pady=5, ipady=10)
        
        # 安装依赖按钮
        self.btn_install_deps = ttk.Button(panel, text="📦 安装依赖")
        self.btn_install_deps.pack(fill=tk.X, padx=5, pady=5, ipady=10)
        
        # 占位符，将状态标签推到底部
        ttk.Frame(panel).pack(fill=tk.BOTH, expand=True)
        
        # 状态标签
        self.status_label = ttk.Label(
            panel,
            text="状态: 未启动",
            relief=tk.SUNKEN,
            padding=10,
            font=("Microsoft YaHei", 9)
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        return panel
    
    def _create_right_panel(self):
        """创建右侧日志面板"""
        panel = ttk.Frame(self.paned)
        
        # 标题
        title_label = ttk.Label(panel, text="日志输出", font=("Microsoft YaHei", 12, "bold"))
        title_label.pack(pady=5)
        
        # 日志文本框（使用 ScrolledText）
        self.log_text = scrolledtext.ScrolledText(
            panel,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        return panel


class ConfigDialog:
    """配置对话框"""
    
    def __init__(self, parent):
        self.result = None
        
        # 创建顶层窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("配置设置")
        self.dialog.geometry("500x520")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (520 // 2)
        self.dialog.geometry(f"500x520+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建配置对话框组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表单框架
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 账号
        ttk.Label(form_frame, text="账号:").grid(row=0, column=0, sticky=tk.E, padx=5, pady=10)
        self.input_username = ttk.Entry(form_frame, width=40)
        self.input_username.grid(row=0, column=1, sticky=tk.W, padx=5, pady=10)
        
        # 密码
        ttk.Label(form_frame, text="密码:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=10)
        self.input_password = ttk.Entry(form_frame, width=40, show="*")
        self.input_password.grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)
        
        # 登录地址
        ttk.Label(form_frame, text="登录地址:").grid(row=2, column=0, sticky=tk.E, padx=5, pady=10)
        self.input_login_url = ttk.Entry(form_frame, width=40)
        self.input_login_url.grid(row=2, column=1, sticky=tk.W, padx=5, pady=10)
        
        # 下载镜像源
        ttk.Label(form_frame, text="下载镜像源:").grid(row=3, column=0, sticky=tk.E, padx=5, pady=10)
        self.input_download_host = ttk.Entry(form_frame, width=40)
        self.input_download_host.grid(row=3, column=1, sticky=tk.W, padx=5, pady=10)
        
        # 浏览器路径
        ttk.Label(form_frame, text="Playwright Cache:").grid(row=4, column=0, sticky=tk.E, padx=5, pady=10)
        self.input_browsers_path = ttk.Entry(form_frame, width=40)
        self.input_browsers_path.grid(row=4, column=1, sticky=tk.W, padx=5, pady=10)
        
        # 检查间隔
        ttk.Label(form_frame, text="检查间隔(秒):").grid(row=5, column=0, sticky=tk.E, padx=5, pady=10)
        self.input_check_interval = ttk.Entry(form_frame, width=40)
        self.input_check_interval.grid(row=5, column=1, sticky=tk.W, padx=5, pady=10)
        
        # 提示信息
        help_frame = ttk.LabelFrame(main_frame, text="💡 提示", padding=10)
        help_frame.pack(fill=tk.X, pady=10)
        
        help_text = (
            "• 账号密码将保存到 .env 文件\n"
            "• 镜像源用于加速 Playwright 浏览器下载\n"
            "• Playwright Cache 是浏览器驱动存储路径（相对或绝对路径）\n"
            "• 检查间隔建议设置为 30-300 秒"
        )
        ttk.Label(help_frame, text=help_text, justify=tk.LEFT).pack()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="保存", command=self._on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self._on_cancel).pack(side=tk.RIGHT)
    
    def _on_save(self):
        """保存按钮回调"""
        self.result = {
            'username': self.input_username.get().strip(),
            'password': self.input_password.get().strip(),
            'login_url': self.input_login_url.get().strip(),
            'download_host': self.input_download_host.get().strip(),
            'browsers_path': self.input_browsers_path.get().strip(),
            'check_interval': self.input_check_interval.get().strip()
        }
        self.dialog.destroy()
    
    def _on_cancel(self):
        """取消按钮回调"""
        self.result = None
        self.dialog.destroy()
    
    def set_values(self, values):
        """设置输入值"""
        self.input_username.delete(0, tk.END)
        self.input_username.insert(0, values.get('username', ''))
        
        self.input_password.delete(0, tk.END)
        self.input_password.insert(0, values.get('password', ''))
        
        self.input_login_url.delete(0, tk.END)
        self.input_login_url.insert(0, values.get('login_url', 'https://raas.hzu.edu.cn/'))
        
        self.input_download_host.delete(0, tk.END)
        self.input_download_host.insert(0, values.get('download_host', 'https://npmmirror.com/mirrors/playwright/'))
        
        self.input_browsers_path.delete(0, tk.END)
        self.input_browsers_path.insert(0, values.get('browsers_path', 'browsers'))
        
        self.input_check_interval.delete(0, tk.END)
        self.input_check_interval.insert(0, str(values.get('check_interval', '30')))
    
    def show(self):
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result
