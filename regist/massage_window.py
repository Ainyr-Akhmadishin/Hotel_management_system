import sqlite3

from PyQt6.QtWidgets import QDialog, QMainWindow
from PyQt6 import uic

class MassageWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('UI/Reg/Окно отправки сообщений.ui', self)
        self.setWindowTitle("Отправка сообщений")
        self.load_staff()

    def load_staff(self):
        conn =sqlite3.connect('Hotel_bd.db')
        cursor = conn.cursor()
        cursor.execute('''
                            SELECT last_name || ' ' || SUBSTR(first_name, 1, 1) || '. ' || SUBSTR(patronymic, 1, 1) || '.' || ' (' || position || ')' as staff_name 
                            FROM staff 
                            ''')
        self.recipients_list.addItems(row[0] for row in cursor.fetchall())

