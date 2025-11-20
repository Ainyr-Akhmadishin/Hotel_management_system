from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic

from utils import get_resource_path
from staff.BD_staff import UploadCleaningWindow
class StaffWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, full_name, username):
        super().__init__()
        self.full_name = full_name
        self.username = username

        uic.loadUi('UI/Staff/Окно обслуживающего персонала.ui', self)
        self.setWindowTitle(f"Персонал - {self.full_name}")
        self.upload_button.clicked.connect(self.open_upload)

    def open_upload(self):
        # СОЗДАЕМ ЭКЗЕМПЛЯР КЛАССА, а не обращаемся к классу
        self.upload_window = UploadCleaningWindow()  # Добавлены скобки ()
        self.upload_window.show()


    def closeEvent(self, event):
        self.closed.emit()
        event.accept()