from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic

from regist.guest_registration_window import GuestRegistrationWindow


class RegistrarWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, full_name, username):
        super().__init__()
        self.full_name = full_name
        self.username = username

        uic.loadUi('UI/Reg/Регистратор итог.ui', self)
        self.setWindowTitle(f"Регистратор - {self.full_name}")

        self.book_button.clicked.connect(self.guest_registration)


    def guest_registration(self):



        self.guest_window = GuestRegistrationWindow(self)



        self.guest_window.show()


