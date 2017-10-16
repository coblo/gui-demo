import time

from app.ui.create_privilege_request import Ui_widget_create_privilege_request
from app.backend.api import Api

from PyQt5.QtCore import QSizeF
from PyQt5.QtGui import QFont, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QDialog, QWidget


class CreatePrivilegeRequest(QWidget, Ui_widget_create_privilege_request):
    def __init__(self, parent, change_stack_index):
        super().__init__(parent)
        self.api = Api()
        self.setupUi(self)

        self.btn_print_proof.clicked.connect(self.print_proof)

    def print_proof(self):
        printer = QPrinter(96)
        printer.setOrientation(QPrinter.Landscape)
        printer.setOutputFileName('tmp.pdf')
        printer.setPageMargins(16, 12, 20, 12, QPrinter.Millimeter)

        text = "Date:\n{}\n\n".format(time.strftime("%d/%m/%Y"))
        text += "Address:\n{}\n\n".format(self.api.get_main_address())
        text += "Current Blockhash:\n{}".format(self.api.get_actual_hash())

        document = QTextDocument()
        document.setPageSize(QSizeF(printer.pageRect().size()))
        document.setDefaultFont(QFont("Arial", 30))
        document.setPlainText(text)

        dialog = QPrintDialog()
        if dialog.exec_() == QDialog.Accepted:
            dialog.printer().setOrientation(QPrinter.Landscape)
            document.print_(dialog.printer())