from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6 import uic
import sqlite3
from datetime import datetime

class GuestRegistrationWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        uic.loadUi('UI/Reg/Окно заселения гостя итог.ui', self)
        self.setWindowTitle("Заселение гостя")

        self.dateEdit.setDate(QDate.currentDate())
        self.dateEdit.dateChanged.connect(self.update_available_rooms)

        self.dateEdit.setDate(QDate.currentDate().addDays(1))
        self.dateEdit.dateChanged.connect(self.update_available_rooms)

        self.load_rooms_to_combobox()

        self.pushButton.clicked.connect(self.register_guest)


    def load_rooms_to_combobox(self):

        try:
            # Подключаемся к базе данных
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем все номера из таблицы rooms
            cursor.execute('SELECT room_number FROM rooms ORDER BY room_number')
            rooms = cursor.fetchall()

            # Очищаем комбобокс перед добавлением
            if hasattr(self, 'comboBox'):
                self.comboBox.clear()

                # Добавляем номера в комбобокс
                for room in rooms:
                    self.comboBox.addItem(room[0])  # room[0] - это room_number

                print(f"✅ Загружено номеров в комбобокс: {len(rooms)}")

            conn.close()

        except Exception as e:
            print(f"❌ Ошибка загрузки номеров из БД: {e}")
            # Если БД недоступна, добавляем тестовые номера
            self.add_test_rooms()

    def add_test_rooms(self):
        """Добавляет тестовые номера если БД недоступна"""
        test_rooms = ["101", "102", "103", "104", "105",
                      "201", "202", "203", "204",
                      "301", "302", "303", "304"]

        if hasattr(self, 'comboBox'):
            self.comboBox.clear()
            for room in test_rooms:
                self.comboBox.addItem(room)
            print("✅ Добавлены тестовые номера")

    def register_guest(self):
        """Обработка заселения гостя"""
        try:
            # Получаем выбранный номер
            selected_room = self.comboBox.currentText()

            QMessageBox.information(self, "Успех",
                                    f"Гость будет заселен в номер: {selected_room}\n\n"
                                    "Функция сохранения в БД будет добавлена позже.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()