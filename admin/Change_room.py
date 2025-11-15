from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox, QDialog, QInputDialog
from PyQt6.QtCore import QDate
import sqlite3
from datetime import datetime
from utils import get_resource_path

class RoomManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(get_resource_path('UI/Admin/Изменение номеров переделанная.ui'), self)

        self.setWindowTitle("Управление номерами")
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))

        # Инициализация БД
        self.conn = sqlite3.connect('Hotel_bd.db')
        self.cursor = self.conn.cursor()

        # Подключаем кнопки и элементы
        self.search_lineEdit.textChanged.connect(self.search_rooms)
        self.sort_comboBox.currentTextChanged.connect(self.sort_rooms)

        # Список кнопок номеров
        self.room_buttons = [
            self.pushButton_2, self.pushButton_5, self.pushButton_6,
            self.pushButton_15, self.pushButton_13, self.pushButton_11,
            self.pushButton_8
        ]

        # Список меток статуса
        self.status_labels = [
            self.label_4, self.label_5, self.label_6, self.label_7,
            self.label_8, self.label_9, self.label_10
        ]

        # Подключаем обработчики для кнопок номеров
        for button in self.room_buttons:
            button.clicked.connect(self.create_room_button_handler(button))

        # Загружаем данные номеров
        self.all_rooms = []
        self.load_rooms()

    def create_room_button_handler(self, button):
        """Создает обработчик для кнопки номера"""

        def handler():
            self.edit_room(button.text())

        return handler

    def load_rooms(self):
        """Загрузка номеров из БД"""
        try:
            self.cursor.execute("""
                SELECT r.room_number, 
                       CASE 
                           WHEN EXISTS (
                               SELECT 1 FROM bookings b 
                               WHERE b.room_id = r.id 
                               AND date('now') BETWEEN b.check_in_date AND b.check_out_date
                           ) THEN '+' 
                           ELSE '-' 
                       END as status
                FROM rooms r
                ORDER BY r.room_number
            """)
            self.all_rooms = self.cursor.fetchall()
            self.display_rooms(self.all_rooms)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки номеров: {str(e)}")

    def display_rooms(self, rooms):
        """Отображение номеров в интерфейсе"""
        # Очищаем кнопки и метки
        for button in self.room_buttons:
            button.setVisible(False)
        for label in self.status_labels:
            label.setVisible(False)

        # Заполняем данными
        for i, (room_number, status) in enumerate(rooms):
            if i >= len(self.room_buttons):
                break

            # Устанавливаем номер
            self.room_buttons[i].setText(room_number)
            self.room_buttons[i].setVisible(True)

            # Устанавливаем статус
            self.status_labels[i].setText(status)
            self.status_labels[i].setVisible(True)

            # Настраиваем цвет статуса
            if status == '+':
                self.status_labels[i].setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #27ae60; text-align: center; "
                    "background-color: #e8f8ef; padding: 6px 10px; border-radius: 4px;"
                )
            else:
                self.status_labels[i].setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #e74c3c; text-align: center; "
                    "background-color: #ffeaea; padding: 6px 10px; border-radius: 4px;"
                )

    def search_rooms(self):
        """Поиск номеров"""
        search_text = self.search_lineEdit.text().strip()

        if not search_text:
            self.display_rooms(self.all_rooms)
            return

        filtered_rooms = []
        for room_number, status in self.all_rooms:
            if search_text in room_number:
                filtered_rooms.append((room_number, status))

        self.display_rooms(filtered_rooms)

    def sort_rooms(self):
        """Сортировка номеров"""
        sort_option = self.sort_comboBox.currentText()

        if not self.all_rooms:
            return

        if sort_option == "Сначала занятые (+)":
            sorted_rooms = sorted(self.all_rooms, key=lambda x: (x[1] != '+', x[0]))
        elif sort_option == "Сначала свободные (-)":
            sorted_rooms = sorted(self.all_rooms, key=lambda x: (x[1] != '-', x[0]))
        elif sort_option == "По номеру (возрастание)":
            sorted_rooms = sorted(self.all_rooms, key=lambda x: x[0])
        elif sort_option == "По номеру (убывание)":
            sorted_rooms = sorted(self.all_rooms, key=lambda x: x[0], reverse=True)
        else:
            sorted_rooms = self.all_rooms

        self.display_rooms(sorted_rooms)

    def edit_room(self, room_number):
        """Редактирование номера"""
        try:
            # Получаем текущий номер
            current_room = room_number

            # Запрашиваем новый номер
            new_room, ok = QInputDialog.getText(
                self, "Изменение номера",
                f"Введите новый номер для {current_room}:",
                text=current_room
            )

            if ok and new_room.strip() and new_room != current_room:
                # Проверяем, существует ли уже такой номер
                self.cursor.execute("SELECT id FROM rooms WHERE room_number = ?", (new_room.strip(),))
                if self.cursor.fetchone():
                    QMessageBox.warning(self, "Ошибка", "Номер с таким названием уже существует!")
                    return

                # Обновляем номер в БД
                self.cursor.execute(
                    "UPDATE rooms SET room_number = ? WHERE room_number = ?",
                    (new_room.strip(), current_room)
                )
                self.conn.commit()

                QMessageBox.information(self, "Успех", f"Номер изменен: {current_room} → {new_room}")
                self.load_rooms()  # Перезагружаем данные

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка изменения номера: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

    def closeEvent(self, event):
        """Закрытие соединения с БД"""
        try:
            self.conn.close()
        except:
            pass
        event.accept()