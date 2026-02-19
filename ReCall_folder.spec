# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for ReCall (one-folder mode)."""

import os

block_cipher = None
project_root = os.path.abspath('.')

a = Analysis(
    ['run.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # Bundle read-only resources (themes, translations, config)
        ('config', 'config'),
        ('docs', 'docs'),
        ('resources/icons', 'resources/icons'),
        ('resources/themes', 'resources/themes'),
        ('resources/translations', 'resources/translations'),
        # NOTE: data/ is NOT bundled — databases are user data created at runtime
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Unused Qt modules
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DExtras',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtQuick',
        'PySide6.QtQuickWidgets',
        'PySide6.QtQml',
        'PySide6.QtLocation',
        'PySide6.QtPositioning',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtRemoteObjects',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtStateMachine',
        'PySide6.QtVirtualKeyboard',
        # Unused stdlib
        'unittest', 'email', 'html', 'http', 'xml',
        'xmlrpc', 'pydoc', 'doctest', 'difflib',
        'tkinter', 'curses', 'distutils',
    ],
    noarchive=False,
    optimize=2,
)

# Remove unused Qt binary modules that hooks pulled in automatically.
# This is the real way to reduce PySide6 size — excludes= only filters Python imports.
QT_BINARY_EXCLUDES = [
    'Qt6WebEngine', 'Qt6WebEngineCore', 'Qt6WebEngineWidgets',
    'Qt6Multimedia', 'Qt6MultimediaWidgets',
    'Qt63DCore', 'Qt63DRender', 'Qt63DInput', 'Qt63DLogic',
    'Qt63DAnimation', 'Qt63DExtras',
    'Qt6Charts', 'Qt6DataVisualization',
    'Qt6Quick', 'Qt6QuickWidgets', 'Qt6Qml', 'Qt6QmlModels',
    'Qt6Location', 'Qt6Positioning',
    'Qt6Bluetooth', 'Qt6Nfc',
    'Qt6RemoteObjects', 'Qt6Sensors', 'Qt6SerialPort',
    'Qt6StateMachine', 'Qt6VirtualKeyboard',
    'Qt6Designer', 'Qt6Help', 'Qt6Test',
    # Qt plugins we don't need
    'qtvirtualkeyboardplugin', 'qtwebengine',
]
a.binaries = [
    b for b in a.binaries
    if not any(excl.lower() in b[0].lower() for excl in QT_BINARY_EXCLUDES)
]

# Remove specific unneeded plugin DLLs and Qt modules
BINARY_FILENAME_EXCLUDES = [
    # Qt modules not used by the app
    'Qt6Network.dll', 'QtNetwork.pyd',
    'Qt6Pdf.dll',
    'opengl32sw.dll',           # software OpenGL fallback (~20 MB); requires hardware OpenGL
    # Unneeded image formats
    'qicns.dll',                # Apple icon format
    'qtga.dll',                 # Truevision TGA
    'qtiff.dll',                # TIFF
    'qwbmp.dll',                # Wireless Bitmap
    'qwebp.dll',                # WebP
    'qpdf.dll',                 # PDF image plugin (separate from Qt6Pdf)
    # Unneeded platform backends
    'qminimal.dll',             # headless/testing only
    'qoffscreen.dll',           # offscreen rendering
    'qdirect2d.dll',            # alternative renderer; qwindows.dll handles normal rendering
    # Unneeded plugins
    'qtuiotouchplugin.dll',     # touch input protocol
    'qnetworklistmanager.dll',  # network information plugin
    # Unneeded TLS backends (keep qschannelbackend — native Windows TLS)
    'qopensslbackend.dll',
    'qcertonlybackend.dll',
]
a.binaries = [
    b for b in a.binaries
    if not any(
        b[0].replace('\\', '/').split('/')[-1].lower() == excl.lower()
        for excl in BINARY_FILENAME_EXCLUDES
    )
]

# Remove Qt's own translation files — the app has its own in resources/translations
a.datas = [
    d for d in a.datas
    if not d[0].replace('\\', '/').startswith('PySide6/translations/')
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ReCall',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # strip is a Unix tool, not available on Windows
    upx=True,
    console=False,          # No console window (GUI app)
    disable_windowed_traceback=False,
    icon='resources/icons/app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ReCall',
)
