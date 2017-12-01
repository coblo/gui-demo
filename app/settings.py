from PyQt5.QtCore import QSettings

import app


class Settings(QSettings):
    def __init__(self):
        super().__init__(app.ORG_NAME, app.APP_NAME)
