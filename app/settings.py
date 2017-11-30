from PyQt5.QtCore import QSettings


class Settings(QSettings):
    def __init__(self):
        super().__init__('Content-Blockchain', 'Coblo')
