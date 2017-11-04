import sys
from cx_Freeze import Executable, setup

buildOptions = dict(
    packages=['requests', 'idna', 'timeago'],
    excludes=[],
)

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable(
        'main.py',
        base=base,
        targetName='charm.exe'
    )
]

setup(
    name='Charm',
    version='0.1.1',
    description='Content Blockchain Desktop App',
    options=dict(build_exe=buildOptions),
    executables=executables
)
