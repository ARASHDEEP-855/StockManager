# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['frameBase.py'],
    pathex=[],
    binaries=[],
    datas=[('checked.png', '.'), ('unchecked.png', '.'), ('icon96.png', '.'), ('images', '.')],
    hiddenimports=['cv2', 'PIL.ImageTk', 'tkcalendar', 'pytz'],
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
    name='frameBase',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon1.ico'],
)
