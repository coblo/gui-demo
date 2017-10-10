from PyQt5 import QtWidgets
from app.ui.wallet_header import Ui_widget_wallet_header

class WalletHeader(QtWidgets.QWidget, Ui_widget_wallet_header):

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.updater = parent.updater
        self.updater.balance_changed.connect(self.on_balance_changed)
        self.updater.address_changed.connect(self.on_address_changed)
        self.updater.start()

    def on_balance_changed(self, balance):
        print('Balance Changed')
        self.label_wallet_balance.setText(str(balance))

    def on_address_changed(self, address):
        self.label_wallet_address.setText(address)


if __name__ == '__main__':
    import sys
    import traceback
    app = QtWidgets.QApplication(sys.argv)
    window = WalletHeader(None)
    window.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
