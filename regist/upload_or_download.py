from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QDialog
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic

from regist.upload import UploadWindow
from regist.download import DownloadWindow

class UDWindow(QDialog):
    closed = pyqtSignal()

    def __init__(self, on_data_updated=None):  # ← добавляем callback
        super().__init__()
        self.on_data_updated = on_data_updated

        uic.loadUi('UI/Reg/Окно загрузка или выгрузка.ui', self)
        self.setWindowTitle(f"Выберите действие")
        self.load_button.clicked.connect(self.show_download)
        self.save_button.clicked.connect(self.show_upload)

    def show_download(self):
        self.download_window = DownloadWindow()
        self.download_window.closed.connect(self.show)
        if self.on_data_updated:
            self.download_window.data_updated.connect(self.on_data_updated)
        self.download_window.show()
        self.hide()

    def show_upload(self):
        self.upload_window = UploadWindow()
        self.upload_window.closed.connect(self.show)
        self.upload_window.show()
        self.hide()

def closeEvent(self, event):
        self.closed.emit()
        event.accept()