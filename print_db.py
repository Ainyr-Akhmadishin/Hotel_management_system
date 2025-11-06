import sqlite3
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, QHeaderView, QPushButton, QMessageBox,
                             QHBoxLayout, QDialog, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6 import uic


class GuestDetailsDialog(QDialog):
    """Диалог для отображения полной информации о госте"""

    def __init__(self, guest_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Полная информация о госте")
        self.setGeometry(200, 200, 500, 400)

        self.setup_ui()
        self.display_guest_data(guest_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("font-family: Arial; font-size: 12px;")

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)

        layout.addWidget(self.text_edit)
        layout.addWidget(close_btn)

    def display_guest_data(self, guest_data):
        """Отображает полную информацию о госте"""
        text = f"""
╔═══════════════════════════════════════╗
║           ИНФОРМАЦИЯ О ГОСТЕ          ║
╚═══════════════════════════════════════╝

📋 ЛИЧНЫЕ ДАННЫЕ:
├─ Фамилия: {guest_data.get('last_name', 'Не указано')}
├─ Имя: {guest_data.get('first_name', 'Не указано')}
├─ Отчество: {guest_data.get('patronymic', 'Не указано')}
├─ Паспорт: {guest_data.get('passport_number', 'Не указано')}
├─ Телефон: {guest_data.get('phone_number', 'Не указано')}

🏨 ИНФОРМАЦИЯ О БРОНИРОВАНИИ:
├─ Номер комнаты: {guest_data.get('room_number', 'Не указано')}
├─ Дата заселения: {guest_data.get('check_in_date', 'Не указано')}
├─ Дата выселения: {guest_data.get('check_out_date', 'Не указано')}
        """
        self.text_edit.setText(text)


class BookingsViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Просмотр бронирований и постояльцев")
        self.setGeometry(100, 100, 1200, 700)

        self.setup_ui()
        self.load_bookings()

    def setup_ui(self):
        """Создание интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Создаем таблицу
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Фамилия", "Имя", "Отчество", "Паспорт", "Телефон", "Номер"
        ])

        # Настройка таблицы
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self.show_guest_details)

        # Панель кнопок
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.load_bookings)

        self.details_btn = QPushButton("👤 Подробнее о госте")
        self.details_btn.clicked.connect(self.show_selected_guest_details)

        self.check_db_btn = QPushButton("🔍 Проверить БД")
        self.check_db_btn.clicked.connect(self.check_database_structure)

        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.details_btn)
        button_layout.addWidget(self.check_db_btn)
        button_layout.addStretch()

        layout.addWidget(self.table)
        layout.addLayout(button_layout)

    def check_database_structure(self):
        """Проверяет структуру базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем список всех таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            table_info = "📊 СТРУКТУРА БАЗЫ ДАННЫХ:\n\n"

            for table in tables:
                table_name = table[0]
                table_info += f"📋 Таблица: {table_name}\n"

                # Получаем структуру таблицы
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                for col in columns:
                    table_info += f"   ├─ {col[1]} ({col[2]})\n"
                table_info += "\n"

            conn.close()

            QMessageBox.information(self, "Структура БД", table_info)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось проверить структуру БД: {str(e)}")

    def load_bookings(self):
        """Загрузка бронирований из базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Сначала попробуем простой запрос к таблице guests
            try:
                cursor.execute('''
                    SELECT 
                        last_name,
                        first_name,
                        patronymic,
                        passport_number,
                        phone_number
                    FROM guests
                ''')
                guests = cursor.fetchall()

                # Заполняем таблицу гостями
                self.table.setRowCount(len(guests))
                self.table.setColumnCount(5)
                self.table.setHorizontalHeaderLabels([
                    "Фамилия", "Имя", "Отчество", "Паспорт", "Телефон"
                ])

                for row, guest in enumerate(guests):
                    for col, value in enumerate(guest):
                        item = QTableWidgetItem(str(value) if value is not None else "")
                        self.table.setItem(row, col, item)

                    # Сохраняем данные гостя
                    guest_data = {
                        'last_name': guest[0],
                        'first_name': guest[1],
                        'patronymic': guest[2],
                        'passport_number': guest[3],
                        'phone_number': guest[4]
                    }
                    self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, guest_data)

                print(f"✅ Загружено гостей: {len(guests)}")

            except sqlite3.Error as e:
                QMessageBox.warning(self, "Внимание",
                                    f"Не удалось загрузить гостей: {str(e)}\n"
                                    f"Проверьте структуру базы данных.")
                return

            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось подключиться к базе данных: {str(e)}\n"
                                 f"Убедитесь что файл Hotel_bd.db существует.")

    def show_guest_details(self, index):
        """Показывает детали гостя при двойном клике"""
        row = index.row()
        guest_data = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.open_guest_details_dialog(guest_data)

    def show_selected_guest_details(self):
        """Показывает детали выбранного гостя"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            guest_data = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            self.open_guest_details_dialog(guest_data)
        else:
            QMessageBox.warning(self, "Внимание", "Выберите гостя из таблицы")

    def open_guest_details_dialog(self, guest_data):
        """Открывает диалог с детальной информацией о госте"""
        dialog = GuestDetailsDialog(guest_data, self)
        dialog.exec()


def main():
    app = QApplication(sys.argv)

    window = BookingsViewer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()