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
    'bdist_msi':
        {
            'data':
                {
                    'Shortcut': [
                        ("DesktopShortcut",     # Shortcut
                        "DesktopFolder",        # Directory_
                        "Content Blockchain 2",   # Name
                        "TARGETDIR",            # Component_
                        "[TARGETDIR]coblo2.exe", # Target
                        None,                   # Arguments
                        None,                   # Description
                        None,                   # Hotkey
                        None,                   # Icon
                        None,                   # IconIndex
                        None,                   # ShowCmd
                        'TARGETDIR'             # WkDir
                        ),
                        ("StartupShortcut",     # Shortcut
                        "StartupFolder",        # Directory_
                        "Content Blockchain 2",   # Name
                        "TARGETDIR",            # Component_
                        "[TARGETDIR]coblo2.exe", # Target
                        None,                   # Arguments
                        None,                   # Description
                        None,                   # Hotkey
                        None,                   # Icon
                        None,                   # IconIndex
                        None,                   # ShowCmd
                        'TARGETDIR'             # WkDir
                        ),
                    ]
                }
        }
}

executables = [
    Executable(
        'main.py',
        base=base,
        initScript=None,
        icon='app.ico',
        targetName='coblo2.exe',
        shortcutName='Content Blockchain 2',
        shortcutDir='DesktopFolder',
        copyright='Copyright (C) 2018 The Content Blockchain Project',
    )
]

setup(
    name='Coblo2',
    version='1.0.2',
    description='Content Blockchain Demo 2',
    options=options,
    executables=executables
)
