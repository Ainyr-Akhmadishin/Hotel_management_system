import sqlite3

from PyQt6.QtWidgets import QDialog, QMainWindow
from PyQt6 import uic



class MassageWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('UI/Reg/Окно отправки сообщений.ui', self)
        self.setWindowTitle("Отправка сообщений")

        self.load_staff('')
        self.search_recipient_input.textChanged.connect(lambda: self.load_staff(self.search_recipient_input.text().title()))
        self.recipients_list.itemClicked.connect(self.selected_recipient)


    def selected_recipient(self, item):
        self.recipient = item.text()
        self.selected_recipient_label.setText("Отправить: " + self.recipient)

    def load_staff(self, name):
        try:
            conn =sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            if name and name.strip():
                search_pattern = f'{name}%'
                cursor.execute('''
                                    SELECT last_name || ' ' || first_name || ' (' || position || ')' as staff_name 
                                    FROM staff WHERE first_name LIKE ? OR last_name LIKE ? 
                                    ORDER BY last_name, first_name
                                    ''', (search_pattern, search_pattern))
            else:
                cursor.execute('''
                                    SELECT last_name || ' ' || first_name || ' (' || position || ')' as staff_name 
                                    FROM staff 
                                    ORDER BY last_name, first_name
                                    ''')
            self.recipients_list.clear()
            self.recipients_list.addItems(row[0] for row in cursor.fetchall())
            conn.close()


        except Exception as e:
            print(f"Ошибка загрузки сотрудников: {e}")
