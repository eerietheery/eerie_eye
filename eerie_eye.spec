# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Main entry point

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('effects/*', 'effects'), ('ui/*', 'ui'), ('utils/*', 'utils')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EerieEye2.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None
    onefile=True
)
