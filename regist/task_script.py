import pickle
import sqlite3

from PyQt6.QtWidgets import QMainWindow, QDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic

from utils import get_resource_path


class TaskWindow(QDialog):
    task_created = pyqtSignal()
    closed = pyqtSignal()
    def __init__(self,room_number,user_id):

        super().__init__()
        self.room_number = room_number
        self.user_id = user_id
        uic.loadUi(get_resource_path('UI/Reg/Окно отправки заданий.ui'), self)
        self.setWindowTitle("Создание задания на уборку")
        self.room_label.setText(f"Номер комнаты: {room_number}")
        self.send_button.clicked.connect(lambda: self.create_task(user_id))
        self.cancel_button.clicked.connect(self.close)

    def create_task(self, user_id):
        try:
            db_path = get_resource_path('Hotel_bd.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            comment_text = self.comment_text.toPlainText().strip()
            notes = comment_text if comment_text else None

            binary_message = pickle.dumps(f"Требуется убраться в комнате номер: {self.room_number}")



            cursor.execute('''INSERT INTO maintenance_tasks 
                              (room_number, description, created_by, status, notes) 
                              VALUES (?, ?, ?, ?, ?)''',
                           (str(self.room_number),
                            f"Убраться в комнате номер: {self.room_number}",
                            user_id,
                            'в ожидании уборки',
                            notes))

            cursor.execute('''SELECT id FROM staff 
                                     WHERE position = 'обслуживающий персонал' ''')

            staff_members = cursor.fetchall()
            for staff_member in staff_members:
                staff_id = staff_member[0]
                cursor.execute('''INSERT INTO messages (from_user, to_user, text)
                                        VALUES (?, ?, ?)''',
                               (user_id, staff_id, binary_message))

            conn.commit()
            conn.close()

            QMessageBox.information(self,"Успех",f"Задание на уборку комнаты {self.room_number} создано!\n")

            self.task_created.emit()
            self.accept()

        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка базы данных",
                f"Не удалось создать задание:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Неожиданная ошибка:\n{str(e)}"
            )


