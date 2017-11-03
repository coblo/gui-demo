from PyQt5.QtCore import QSettings
import app
import logging

log = logging.getLogger(__name__)

settings = QSettings(app.ORG_NAME, app.APP_NAME)
log.debug('init setting, keysare {}'.format(settings.allKeys()))
