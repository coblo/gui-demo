import sys
from cx_Freeze import Executable, setup


base = 'Win32GUI' if sys.platform == 'win32' else None

options = {
    'build_exe':
        {
            'includes': 'atexit',
            'packages': ['requests', 'idna', 'timeago'],
            'excludes': [],
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
        copyright='Copyright (C) 2017 The Content Blockchain Project',
    )
]

setup(
    name='Coblo',
    version='0.2.0',
    description='Content Blockchain Demo',
    options=options,
    executables=executables
)
