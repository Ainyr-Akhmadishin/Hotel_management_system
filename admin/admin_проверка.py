from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel, QMessageBox
from PyQt6.QtCore import QDate
import sqlite3
import sys
import os


class AdminWindow(QMainWindow):
    def __init__(self, full_name, username):
        super().__init__()

        print(f"=== СОЗДАНИЕ АДМИН ОКНА ДЛЯ {full_name} ===")

        self.full_name = full_name
        self.username = username

        # Пробуем загрузить UI файл
        ui_loaded = self.try_load_ui()

        if not ui_loaded:
            # Если UI не загрузился, создаем простой интерфейс
            self.create_simple_interface()

        # Инициализация БД
        self.init_database()

        print("✅ Админ окно готово к показу")

    def try_load_ui(self):
        """Пытается загрузить UI файл, возвращает True если успешно"""
        try:
            # Пробуем разные пути к UI файлу
            possible_paths = [
                'UI/Admin/Админ переделанный.ui',
                '../UI/Admin/Админ переделанный.ui',
                '../../UI/Admin/Админ переделанный.ui',
                os.path.join(os.path.dirname(__file__), '../UI/Admin/Админ переделанный.ui'),
                os.path.join(os.path.dirname(__file__), '../../UI/Admin/Админ переделанный.ui')
            ]

            ui_file = None
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                print(f"Проверяем путь: {abs_path}")
                if os.path.exists(abs_path):
                    ui_file = abs_path
                    print(f"✅ Найден UI файл: {ui_file}")
                    break

            if not ui_file:
                print("❌ UI файл не найден ни по одному из путей")
                return False

            # Загружаем UI
            uic.loadUi(ui_file, self)
            print("✅ UI файл успешно загружен")

            # Настраиваем окно
            self.setWindowTitle(f"Администратор - {self.full_name}")

            # Устанавливаем дату
            if hasattr(self, 'current_date_label'):
                self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))

            # Подключаем кнопки если они есть
            self.connect_available_buttons()

            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки UI: {e}")
            return False

    def create_simple_interface(self):
        """Создает простой интерфейс как запасной вариант"""
        print("🔄 Создаем простой интерфейс...")

        self.setWindowTitle(f"Администратор - {self.full_name}")
        self.setGeometry(100, 100, 600, 400)

        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Создаем layout
        layout = QVBoxLayout()

        # Добавляем элементы
        title_label = QLabel(f"Панель администратора\nДобро пожаловать, {self.full_name}!")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px; text-align: center;")
        layout.addWidget(title_label)

        date_label = QLabel(f"Сегодня: {QDate.currentDate().toString('dd.MM.yyyy')}")
        date_label.setStyleSheet("font-size: 14px; margin: 10px; text-align: center;")
        layout.addWidget(date_label)

        # Информация о режиме
        info_label = QLabel("(Режим совместимости - UI файл не загружен)")
        info_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px; text-align: center;")
        layout.addWidget(info_label)

        # Тестовые кнопки
        test_btn = QPushButton("Проверить работу системы")
        test_btn.clicked.connect(self.test_function)
        test_btn.setStyleSheet("padding: 10px; font-size: 14px;")
        layout.addWidget(test_btn)

        # Кнопка выхода
        exit_btn = QPushButton("Выход")
        exit_btn.clicked.connect(self.close)
        exit_btn.setStyleSheet("padding: 10px; font-size: 14px; background-color: #e74c3c;")
        layout.addWidget(exit_btn)

        central_widget.setLayout(layout)
        print("✅ Простой интерфейс создан")

    def init_database(self):
        """Инициализация базы данных"""
        try:
            self.conn = sqlite3.connect('Hotel_bd.db')
            self.cursor = self.conn.cursor()
            print("✅ База данных подключена")
        except Exception as e:
            print(f"❌ Ошибка БД: {e}")

    def connect_available_buttons(self):
        """Подключает кнопки которые есть в UI"""
        try:
            # Список кнопок для подключения
            buttons = {
                'sort_registry_btn': self.sort_registry,
                'sort_staff_btn': self.sort_staff,
                'manage_employees_btn': self.manage_employees,
                'employees_list_btn': self.show_employees_list,
                'contact_registry_btn': self.contact_registry,
                'contact_staff_btn': self.contact_staff,
                'change_numbers_btn': self.change_numbers,
                'data_export_btn': self.data_export_import
            }

            connected = 0
            for btn_name, handler in buttons.items():
                if hasattr(self, btn_name):
                    button = getattr(self, btn_name)
                    button.clicked.connect(handler)
                    connected += 1
                    print(f"✅ Подключена кнопка: {btn_name}")

            print(f"Всего подключено кнопок: {connected}")

        except Exception as e:
            print(f"❌ Ошибка подключения кнопок: {e}")

    def test_function(self):
        """Тестовая функция"""
        QMessageBox.information(self, "Тест", f"Система работает!\nАдминистратор: {self.full_name}")

    def sort_registry(self):
        QMessageBox.information(self, "Сортировка", "Регистратура отсортирована")

    def sort_staff(self):
        QMessageBox.information(self, "Сортировка", "Персонал отсортирован")

    def manage_employees(self):
        QMessageBox.information(self, "Управление", "Управление сотрудниками")

    def show_employees_list(self):
        QMessageBox.information(self, "Список", "Список сотрудников")

    def contact_registry(self):
        QMessageBox.information(self, "Связь", "Связь с регистратурой")

    def contact_staff(self):
        QMessageBox.information(self, "Связь", "Связь с персоналом")

    def change_numbers(self):
        QMessageBox.information(self, "Номера", "Изменение номеров")

    def data_export_import(self):
        QMessageBox.information(self, "Данные", "Экспорт/импорт данных")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    print("=== ТЕСТОВЫЙ ЗАПУСК АДМИН ПАНЕЛИ ===")

    window = AdminWindow("Иван Иванов", "admin")
    window.show()

    print(f"Окно создано: {window is not None}")
    print(f"Окно видимо: {window.isVisible()}")

    sys.exit(app.exec())