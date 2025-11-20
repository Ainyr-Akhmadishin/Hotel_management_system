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
        self.lineEdit.textChanged.connect(self.search_rooms)
        self.comboBox.currentTextChanged.connect(self.sort_rooms)
        self.verticalScrollBar.valueChanged.connect(self.scroll_rooms)

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

        # Переменные для управления данными
        self.all_rooms = []
        self.filtered_rooms = []
        self.current_start_index = 0

        # Загружаем данные номеров
        self.load_rooms()

    def create_room_button_handler(self, button):
        """Создает обработчик для кнопки номера"""

        def handler():
            room_number = button.property("room_number")
            if room_number:
                self.edit_room(room_number)

        return handler

    def load_rooms(self):
        """Загрузка номеров из БД"""
        try:
            # Сначала получим все комнаты
            self.cursor.execute("SELECT id, room_number FROM rooms ORDER BY room_number")
            all_rooms_data = self.cursor.fetchall()

            # Теперь для каждой комнаты проверим занятость
            self.all_rooms = []
            current_date = datetime.now().strftime('%Y-%m-%d')

            for room_id, room_number in all_rooms_data:
                # Проверяем есть ли активное бронирование на сегодня
                # Убираем проверку статуса, так как колонки может не быть
                self.cursor.execute("""
                    SELECT COUNT(*) FROM bookings 
                    WHERE room_id = ? 
                    AND ? BETWEEN check_in_date AND check_out_date
                """, (room_id, current_date))

                is_occupied = self.cursor.fetchone()[0] > 0
                status = '+' if is_occupied else '-'

                self.all_rooms.append((room_id, room_number, status))

            self.filtered_rooms = self.all_rooms.copy()

            # Настраиваем прокрутку
            self.setup_scrollbar()

            # Отображаем комнаты
            self.display_rooms()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки номеров: {str(e)}")

    def setup_scrollbar(self):
        """Настройка прокрутки"""
        total_rooms = len(self.filtered_rooms)
        visible_rooms = len(self.room_buttons)

        if total_rooms > visible_rooms:
            self.verticalScrollBar.setMaximum(total_rooms - visible_rooms)
            self.verticalScrollBar.setVisible(True)
        else:
            self.verticalScrollBar.setMaximum(0)
            self.verticalScrollBar.setVisible(False)

    def display_rooms(self):
        """Отображение номеров в интерфейсе"""
        # Очищаем кнопки и метки
        for button in self.room_buttons:
            button.setVisible(False)
            button.setText("")
            button.setProperty("room_number", "")
        for label in self.status_labels:
            label.setVisible(False)
            label.setText("")

        # Определяем диапазон отображаемых комнат
        end_index = min(self.current_start_index + len(self.room_buttons), len(self.filtered_rooms))
        rooms_to_display = self.filtered_rooms[self.current_start_index:end_index]

        # Заполняем данными
        for i, (room_id, room_number, status) in enumerate(rooms_to_display):
            if i >= len(self.room_buttons):
                break

            # Устанавливаем номер
            self.room_buttons[i].setText(room_number)
            self.room_buttons[i].setProperty("room_number", room_number)
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

    def scroll_rooms(self, value):
        """Прокрутка списка номеров"""
        self.current_start_index = value
        self.display_rooms()

    def search_rooms(self):
        """Поиск номеров"""
        search_text = self.lineEdit.text().strip()

        if not search_text:
            self.filtered_rooms = self.all_rooms.copy()
        else:
            self.filtered_rooms = []
            for room_id, room_number, status in self.all_rooms:
                if search_text.lower() in room_number.lower():
                    self.filtered_rooms.append((room_id, room_number, status))

        # Сбрасываем прокрутку
        self.current_start_index = 0
        self.verticalScrollBar.setValue(0)

        # Настраиваем прокрутку заново
        self.setup_scrollbar()
        self.display_rooms()

    def sort_rooms(self):
        """Сортировка номеров"""
        sort_option = self.comboBox.currentText()

        if not self.filtered_rooms:
            return

        # Используем текущий отфильтрованный список для сортировки
        rooms_to_sort = self.filtered_rooms.copy()

        if sort_option == "Сортировать по \"+\"":
            sorted_rooms = sorted(rooms_to_sort, key=lambda x: (x[2] != '+', x[1]))
        elif sort_option == "Сортировать по \"-\"":
            sorted_rooms = sorted(rooms_to_sort, key=lambda x: (x[2] != '-', x[1]))
        else:
            sorted_rooms = rooms_to_sort

        self.filtered_rooms = sorted_rooms

        # Сбрасываем прокрутку
        self.current_start_index = 0
        self.verticalScrollBar.setValue(0)

        # Настраиваем прокрутку заново
        self.setup_scrollbar()
        self.display_rooms()

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