# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

hidden_mods = collect_submodules('modules')

a = Analysis(
    ['run_tray.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('configs/file_registry.json', 'configs'),
        ('configs/process_names.json', 'configs'),
        ('src/modules', 'modules'),
    ],
    hiddenimports=hidden_mods + [
        'pytz', 'psutil', 'pythoncom', 'win32gui', 'win32process',
        'win32com', 'PIL.ImageGrab'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='JarvisTray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    manifest='JarvisTray.exe.manifest',
)
