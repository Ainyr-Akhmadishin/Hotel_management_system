import sqlite3
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, QHeaderView, QPushButton, QMessageBox,
                             QHBoxLayout, QTabWidget, QMenu)
from PyQt6.QtCore import Qt
from datetime import datetime


class HotelManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление отелем - Сообщения и Бронирования")
        self.setGeometry(100, 100, 1200, 700)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Инициализация интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем вкладки
        self.tabs = QTabWidget()

        # Вкладка сообщений
        self.messages_tab = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_tab)
        self.messages_table = QTableWidget()
        self.messages_layout.addWidget(self.messages_table)

        # Вкладка бронирований
        self.bookings_tab = QWidget()
        self.bookings_layout = QVBoxLayout(self.bookings_tab)
        self.bookings_table = QTableWidget()
        self.bookings_layout.addWidget(self.bookings_table)

        self.tabs.addTab(self.messages_tab, "💬 Сообщения")
        self.tabs.addTab(self.bookings_tab, "📋 Бронирования")

        # Панель кнопок
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.load_data)

        self.delete_btn = QPushButton("🗑️ Удалить выбранное")
        self.delete_btn.clicked.connect(self.delete_selected)

        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()

        layout.addWidget(self.tabs)
        layout.addLayout(button_layout)

        # Настраиваем таблицы
        self.setup_tables()

    def setup_tables(self):
        """Настройка таблиц"""
        # Настройка таблицы сообщений
        self.messages_table.setColumnCount(6)
        self.messages_table.setHorizontalHeaderLabels([
            'ID', 'Отправитель', 'Получатель', 'Текст', 'Дата', 'Прочитано'
        ])
        self.messages_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.messages_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.messages_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.messages_table.customContextMenuRequested.connect(self.show_messages_context_menu)

        # Настройка таблицы бронирований
        self.bookings_table.setColumnCount(6)
        self.bookings_table.setHorizontalHeaderLabels([
            'ID', 'Гость', 'Номер', 'Заезд', 'Выезд', 'Статус'
        ])
        self.bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.bookings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.bookings_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.bookings_table.customContextMenuRequested.connect(self.show_bookings_context_menu)

    def show_messages_context_menu(self, position):
        """Контекстное меню для сообщений"""
        menu = QMenu(self)
        delete_action = menu.addAction("Удалить сообщение")

        action = menu.exec(self.messages_table.viewport().mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_messages()

    def show_bookings_context_menu(self, position):
        """Контекстное меню для бронирований"""
        menu = QMenu(self)
        delete_action = menu.addAction("Удалить бронирование")

        action = menu.exec(self.bookings_table.viewport().mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_bookings()

    def load_data(self):
        """Загрузка всех данных"""
        self.load_messages()
        self.load_bookings()

    def load_messages(self):
        """Загрузка сообщений из базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем сообщения с именами отправителей и получателей
            query = """
            SELECT 
                m.id,
                COALESCE(s1.first_name || ' ' || s1.last_name, 'Система') as from_user,
                COALESCE(s2.first_name || ' ' || s2.last_name, 'Неизвестно') as to_user,
                m.text,
                m.created_at,
                m.is_read
            FROM messages m
            LEFT JOIN staff s1 ON m.from_user = s1.id
            LEFT JOIN staff s2 ON m.to_user = s2.id
            ORDER BY m.created_at DESC
            """

            cursor.execute(query)
            messages = cursor.fetchall()

            # Заполняем таблицу
            self.messages_table.setRowCount(len(messages))

            for row, message in enumerate(messages):
                for col, value in enumerate(message):
                    item = QTableWidgetItem(str(value) if value is not None else "")

                    # Форматируем дату
                    if col == 4 and value:
                        try:
                            date_obj = datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
                            item.setText(date_obj.strftime('%d.%m.%Y %H:%M'))
                        except:
                            pass

                    # Форматируем статус прочтения
                    if col == 5:
                        if value == 1 or str(value).lower() == 'true':
                            item.setText("✅ Да")
                            item.setBackground(Qt.GlobalColor.lightGreen)
                        else:
                            item.setText("❌ Нет")
                            item.setBackground(Qt.GlobalColor.lightGray)

                    # Обрезаем длинный текст
                    if col == 3 and len(str(value)) > 100:
                        item.setText(str(value)[:100] + "...")
                        item.setToolTip(str(value))

                    self.messages_table.setItem(row, col, item)

            conn.close()
            print(f"Загружено сообщений: {len(messages)}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сообщения:\n{str(e)}")

    def load_bookings(self):
        """Загрузка бронирований из базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем бронирования с информацией о гостях и номерах
            query = """
            SELECT 
                b.id,
                g.last_name || ' ' || g.first_name as guest_name,
                r.room_number,
                b.check_in_date,
                b.check_out_date,
                CASE 
                    WHEN date(b.check_out_date) < date('now') THEN 'Завершено'
                    WHEN date(b.check_in_date) <= date('now') AND date(b.check_out_date) >= date('now') THEN 'Активно'
                    ELSE 'Ожидается'
                END as status
            FROM bookings b
            JOIN guests g ON b.guest_id = g.id
            JOIN rooms r ON b.room_id = r.id
            ORDER BY b.check_in_date DESC
            """

            cursor.execute(query)
            bookings = cursor.fetchall()

            # Заполняем таблицу
            self.bookings_table.setRowCount(len(bookings))

            for row, booking in enumerate(bookings):
                for col, value in enumerate(booking):
                    item = QTableWidgetItem(str(value) if value is not None else "")

                    # Форматируем даты
                    if col in [3, 4] and value:
                        try:
                            date_obj = datetime.strptime(str(value), '%Y-%m-%d')
                            item.setText(date_obj.strftime('%d.%m.%Y'))
                        except:
                            try:
                                date_obj = datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
                                item.setText(date_obj.strftime('%d.%m.%Y'))
                            except:
                                pass

                    # Цветовая индикация статуса
                    if col == 5:
                        if value == 'Активно':
                            item.setBackground(Qt.GlobalColor.green)
                            item.setForeground(Qt.GlobalColor.white)
                        elif value == 'Ожидается':
                            item.setBackground(Qt.GlobalColor.yellow)
                        elif value == 'Завершено':
                            item.setBackground(Qt.GlobalColor.lightGray)

                    self.bookings_table.setItem(row, col, item)

            conn.close()
            print(f"Загружено бронирований: {len(bookings)}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить бронирования:\n{str(e)}")

    def delete_selected(self):
        """Удаление выбранных записей в активной вкладке"""
        current_tab = self.tabs.currentIndex()

        if current_tab == 0:  # Сообщения
            self.delete_selected_messages()
        elif current_tab == 1:  # Бронирования
            self.delete_selected_bookings()

    def delete_selected_messages(self):
        """Удаление выбранных сообщений"""
        selected_rows = self.messages_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите сообщения для удаления")
            return

        # Получаем ID выбранных сообщений
        message_ids = []
        for model_index in selected_rows:
            row = model_index.row()
            id_item = self.messages_table.item(row, 0)
            if id_item:
                message_ids.append(id_item.text())

        if not message_ids:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить ID сообщений")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить {len(message_ids)} сообщений?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect('Hotel_bd.db')
                cursor = conn.cursor()

                # Создаем плейсхолдеры для SQL запроса
                placeholders = ','.join('?' for _ in message_ids)
                cursor.execute(f"DELETE FROM messages WHERE id IN ({placeholders})", message_ids)

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Успех", f"Удалено сообщений: {len(message_ids)}")
                self.load_messages()  # Перезагружаем данные

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сообщения:\n{str(e)}")

    def delete_selected_bookings(self):
        """Удаление выбранных бронирований"""
        selected_rows = self.bookings_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите бронирования для удаления")
            return

        # Получаем ID выбранных бронирований
        booking_ids = []
        for model_index in selected_rows:
            row = model_index.row()
            id_item = self.bookings_table.item(row, 0)
            if id_item:
                booking_ids.append(id_item.text())

        if not booking_ids:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить ID бронирований")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить {len(booking_ids)} бронирований?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect('Hotel_bd.db')
                cursor = conn.cursor()

                # Создаем плейсхолдеры для SQL запроса
                placeholders = ','.join('?' for _ in booking_ids)
                cursor.execute(f"DELETE FROM bookings WHERE id IN ({placeholders})", booking_ids)

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Успех", f"Удалено бронирований: {len(booking_ids)}")
                self.load_bookings()  # Перезагружаем данные

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить бронирования:\n{str(e)}")


def main():
    # Проверка наличия базы данных
    try:
        conn = sqlite3.connect('Hotel_bd.db')
        cursor = conn.cursor()

        # Проверяем существование таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]

        required_tables = ['messages', 'bookings', 'guests', 'rooms', 'staff']
        missing_tables = [table for table in required_tables if table not in tables]

        if missing_tables:
            QMessageBox.warning(
                None,
                "Внимание",
                f"Отсутствуют таблицы: {', '.join(missing_tables)}\n"
                f"Программа может работать некорректно."
            )

        conn.close()

    except sqlite3.Error as e:
        QMessageBox.critical(
            None,
            "Ошибка базы данных",
            f"Не удалось подключиться к базе данных:\n{str(e)}"
        )
        return

    # Запуск приложения
    app = QApplication(sys.argv)
    window = HotelManager()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()