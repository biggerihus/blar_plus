# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Selección automática del formato de icono según el sistema operativo donde se compila
if sys.platform == "win32" and os.path.exists("recursos/icono.ico"):
    icono_ejecutable = ["recursos/icono.ico"]
elif sys.platform == "darwin" and os.path.exists("recursos/icono.icns"):
    icono_ejecutable = ["recursos/icono.icns"]
else:
    icono_ejecutable = ["recursos/icono.png"]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('capa_de_datos/catalogo_dtc.json', 'capa_de_datos'),
        ('recursos', 'recursos'),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='BlarPlus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icono_ejecutable,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BlarPlus',
)

# Empaquetado nativo adicional para macOS (Unix)
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name='BlarPlus.app',
        icon=icono_ejecutable[0],
        bundle_identifier='mx.edu.uacm.blar.blarplus',
    )
