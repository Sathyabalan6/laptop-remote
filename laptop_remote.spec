# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

datas = [
    ('src/laptop_remote/static', 'laptop_remote/static'),
    ('presets.json', '.'),
]

if os.path.exists('logo.ico'):
    datas.append(('logo.ico', '.'))

hiddenimports = [
    'engineio.async_drivers.threading',
    'simple_websocket',
    'wsproto',
    'qrcode',
    'PIL',
    'PIL.ImageTk',
    'pyautogui',
    'laptop_remote',
    'laptop_remote.core',
    'laptop_remote.core.auth',
    'laptop_remote.core.config',
    'laptop_remote.core.input',
    'laptop_remote.core.keys',
    'laptop_remote.core.network',
    'laptop_remote.core.overlay',
    'laptop_remote.core.power',
    'laptop_remote.core.window',
    'laptop_remote.core.audio',
    'laptop_remote.gui',
    'laptop_remote.server',
    'laptop_remote.server._app',
    'laptop_remote.server.state',
    'laptop_remote.server.routes_auth',
    'laptop_remote.server.routes_input',
    'laptop_remote.server.websocket',
    'laptop_remote.server.discovery',
    'laptop_remote.server.main',
]

if sys.platform.startswith('win'):
    hiddenimports += ['win32api', 'win32con', 'win32gui']
elif sys.platform.startswith('linux'):
    hiddenimports += ['Xlib']

a = Analysis(
    ['src/laptop_remote/server/main.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LaptopRemote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico' if os.path.exists('logo.ico') else None,
)
