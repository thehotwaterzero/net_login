# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将校园网自动登录工具打包成 Windows 可执行文件
"""

block_cipher = None

a = Analysis(
    ['gui_tk.py'],  # 主程序入口
    pathex=[],
    binaries=[],
    datas=[
        ('ui_layout_tk.py', '.'),  # UI 布局模块
        ('setup.py', '.'),  # 安装脚本
    ],
    hiddenimports=[
        # Playwright 相关
        'playwright',
        'playwright.sync_api',
        'playwright._impl._api_structures',
        'playwright._impl._api_types',
        'playwright._impl._browser',
        'playwright._impl._browser_context',
        'playwright._impl._browser_type',
        'playwright._impl._page',
        'playwright._impl._connection',
        'playwright._impl._transport',
        'playwright._impl._helper',
        'playwright._impl._driver',
        
        # GUI 相关
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        
        # 系统托盘
        'pystray',
        'pystray._win32',
        
        # 图像处理
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL._tkinter_finder',
        
        # 其他依赖
        'dotenv',
        'schedule',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='校园网自动登录',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用 UPX 压缩
    console=False,  # 无控制台窗口（GUI 程序）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.png',  # 如果有图标文件，取消注释
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='校园网自动登录',
)
