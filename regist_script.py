from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic


class RegistrarWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, full_name, username):
        super().__init__()
        self.full_name = full_name
        self.username = username

        uic.loadUi('UI/Reg/Регистратор итог.ui', self)
        self.setWindowTitle(f"Регистратор - {self.full_name}")


    def closeEvent(self, event):
        self.closed.emit()
        event.accept()