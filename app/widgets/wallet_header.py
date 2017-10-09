import logging
from PyQt5 import QtWidgets, QtGui
from app.backend.updater import Updater
from app.ui.wallet_header import Ui_widget_wallet_header

log = logging.getLogger(__name__)


class WalletHeader(QtWidgets.QWidget, Ui_widget_wallet_header):

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.updater = Updater(self)
        self.updater.balance_changed.connect(self.on_balance_changed)
        self.updater.address_changed.connect(self.on_address_changed)
        self.updater.rpc_error.connect(self.on_rpc_error)
        self.updater.start()

    def on_balance_changed(self, balance):
        print('Balance Changed')
        self.label_wallet_balance.setText(str(balance))

    def on_address_changed(self, address):
        self.label_wallet_address.setText(address)

    def on_rpc_error(self, error):
        log.error(error)


if __name__ == '__main__':
    import sys
    import traceback
    app = QtWidgets.QApplication(sys.argv)
    window = WalletHeader(None)
    window.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
