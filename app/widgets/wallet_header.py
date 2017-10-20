from PyQt5 import QtWidgets

from app import settings
from app.backend.updater import Updater
from app.ui.wallet_header import Ui_widget_wallet_header


class WalletHeader(QtWidgets.QWidget, Ui_widget_wallet_header):

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        # Recover stored settings
        balance = settings.value('balance')
        if balance:
            self.label_wallet_balance.setText(self.format_balance(balance))
        address = settings.value('address')
        if address:
            self.label_wallet_address.setText(address)

        # Listen to balance/address updates
        self.updater = parent.updater
        self.updater.balance_changed.connect(self.on_balance_changed)
        self.updater.address_changed.connect(self.on_address_changed)

    def format_balance(self, balance):
        display = "{0:n}".format(balance.normalize()) if balance is not ' ' else balance
        return display + ' CHM'

    def on_balance_changed(self, balance):
        self.label_wallet_balance.setText(self.format_balance(balance))
        settings.setValue('balance', balance)

    def on_address_changed(self, address):
        self.label_wallet_address.setText(address)
        settings.setValue('address', address)


if __name__ == '__main__':
    import sys
    import traceback
    app = QtWidgets.QApplication(sys.argv)
    wrapper = QtWidgets.QWidget()
    wrapper.updater = Updater()
    wrapper.setLayout(QtWidgets.QHBoxLayout(wrapper))
    wrapper.layout().addWidget(WalletHeader(wrapper))
    wrapper.updater.start()
    wrapper.show()
    sys.excepthook = traceback.print_exception
    sys.exit(app.exec_())
