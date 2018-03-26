import sys
from cx_Freeze import Executable, setup


base = 'Win32GUI' if sys.platform == 'win32' else None

options = {
    'build_exe':
        {
            'includes': 'atexit',
            'packages': ['requests', 'idna', 'timeago', 'sqlalchemy'],
            'excludes': [],
            'include_msvcr': True,
        },
    'bdist_mac':
        {
            'iconfile': 'dist/app.icns',
            'custom_info_plist': 'dist/mac.plist',
        },
    'bdist_dmg':
        {
            'applications_shortcut': True,
            'volume_label': 'ContentBlockchainProject Demo',
        },
}

executables = [
    Executable(
        'main.py',
        base=base,
        initScript=None,
        icon='app.ico',
        targetName='coblo.exe',
        shortcutName='Content Blockchain',
        shortcutDir='DesktopFolder',
        copyright='Copyright (C) 2018 The Content Blockchain Project',
    )
]

setup(
    name='Coblo',
    version='0.3.0',
    description='Content Blockchain Demo',
    options=options,
    executables=executables
)
