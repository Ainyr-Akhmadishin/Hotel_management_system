from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox, QMainWindow
from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6.QtGui import QPalette, QColor
import sqlite3
import sys

from utils import get_resource_path

# Импортируем модули для каждого функционала
from admin.Add_Delete_sotrudnic import EmployeeManagementDialog
from admin.List_sotrudnic import EmployeeListDialog
from admin.Change_room import RoomManagementDialog
from admin.Download_Upload_data import DataExportDialog

from notifications_manager import SimpleNotificationsManager

from massage_window import MassageWindow

class OpenEmployeeManagementError(Exception):
    pass #Исключение для ошибок открытия управления сотрудниками

class OpenEmployeeListError(Exception):
    pass #Исключение для ошибок открытия списка сотрудников

class OpenRoomManagementError(Exception):
    pass #Исключение для ошибок открытия управления номерами

class OpenDataExportError(Exception):
    pass #Исключение для ошибок открытия экспорта данных

class OpenMassageWindowError(Exception):
    pass #Исключение для ошибок открытия окна сообщений


class AdminWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, full_name, username):
        super().__init__()
        uic.loadUi(get_resource_path('UI/Admin/Админ переделанный.ui'), self)
        self.user_id = self.get_user_id(username)
        self.full_name = full_name
        self.username = username
        # Инициализируем менеджер уведомлений
        self.notifications_manager = SimpleNotificationsManager(
            self.user_id,
            self.notifications_frame,
            self  # передаем ссылку на главное окно
        )

        self.init_database()
        # Подключаем кнопки
        self.manage_employees_btn.clicked.connect(self.manage_employees)
        self.employees_list_btn.clicked.connect(self.show_employees_list)
        self.staff_button.clicked.connect(self.open_massage)
        self.change_numbers_btn.clicked.connect(self.change_numbers)
        self.data_export_btn.clicked.connect(self.data_export_import)
        self.exit_button.clicked.connect(self.logout)  # Добавляем кнопку выхода
        # Устанавливаем текущую дату
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))
        # Загружаем данные сотрудников
        self.load_employees_data()

    def open_massage(self):
        try:
            self.massage_window = MassageWindow(full_name=self.full_name)
            self.massage_window.show()
        except Exception as e:
            self.show_error_message(f"Ошибка открытия окна сообщений: {str(e)}")

    def get_user_id(self, username):
        #Получение ID по логину
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM staff WHERE login = ?', (username,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 1
        except Exception as e:
            print(f"Ошибка получения ID пользователя: {e}")
            return 1

    def closeEvent(self, event):
        #Останавливаем обновления уведомлений при закрытии
        if hasattr(self, 'notifications_manager'):
            self.notifications_manager.stop_updates()
        super().closeEvent(event)

    def init_database(self):
        #Baza dannih
        try:
            self.conn = sqlite3.connect('Hotel_bd.db')
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось подключиться к базе данных: {str(e)}")

    def load_employees_data(self):
        #Загрузка данных сотрудников для отображения в главном окне
        try:
            # Загружаем администраторов и регистраторов
            self.cursor.execute("""
                SELECT first_name, last_name, patronymic 
                FROM staff 
                WHERE position IN ('администратор', 'регистратор')
                ORDER BY last_name, first_name, patronymic
                LIMIT 3
            """)
            registry_employees = self.cursor.fetchall()

            # Загружаем обслуживающий персонал
            self.cursor.execute("""
                SELECT first_name, last_name, patronymic 
                FROM staff 
                WHERE position = 'обслуживающий персонал'
                ORDER BY last_name, first_name, patronymic
                LIMIT 3
            """)
            staff_employees = self.cursor.fetchall()

            # Обновляем отображение регистратуры
            registry_labels = [self.label_5, self.label_7, self.label_10]
            for i, label in enumerate(registry_labels):
                if i < len(registry_employees):
                    first_name, last_name, patronymic = registry_employees[i]
                    full_name = f"{last_name} {first_name[0]}."
                    if patronymic:
                        full_name += f"{patronymic[0]}."
                    label.setText(full_name)
                else:
                    label.setText("")

            # Обновляем отображение персонала
            staff_labels = [self.label_6, self.label_8, self.label_9]
            for i, label in enumerate(staff_labels):
                if i < len(staff_employees):
                    first_name, last_name, patronymic = staff_employees[i]
                    full_name = f"{last_name} {first_name[0]}."
                    if patronymic:
                        full_name += f"{patronymic[0]}."
                    label.setText(full_name)
                else:
                    label.setText("")

        except sqlite3.Error as e:
            print(f"Ошибка загрузки данных сотрудников: {e}")

    def add_message(self, message):
        #Добавление сообщения в список
        current_list = self.model.stringList()
        current_list.append(f"{QDate.currentDate().toString('dd.MM.yyyy')} - {message}")
        self.model.setStringList(current_list)
        self.listView.scrollToBottom()

    def show_success_message(self, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Успех")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStyleSheet("QMessageBox { background-color: white; }")
        msg_box.exec()

    def show_error_message(self, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Ошибка")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setStyleSheet("QMessageBox { background-color: white; }")
        msg_box.exec()

    def manage_employees(self):
        #Управление сотрудниками
        try:
            dialog = EmployeeManagementDialog(self)
            dialog.exec()
            # Обновляем данные после закрытия диалога
            self.load_employees_data()
        except Exception as e:
            self.show_error_message(f"Ошибка открытия управления сотрудниками")

    def show_employees_list(self):
        #список работников
        try:
            dialog = EmployeeListDialog(self)
            dialog.exec()
        except Exception as e:
            self.show_error_message(f"Ошибка открытия списка сотрудников")

    def change_numbers(self):
        #Изменение номеров
        try:
            dialog = RoomManagementDialog(self)
            dialog.exec()
        except Exception as e:
            self.show_error_message(f"Ошибка открытия управления номерами")

    def data_export_import(self):
        #Выгрузка данных
        try:
            dialog = DataExportDialog(self)
            dialog.exec()
        except Exception as e:
            self.show_error_message(f"Ошибка открытия экспорта данных")

    def logout(self):
        """Выход из аккаунта"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Подтверждение выхода")
        msg_box.setText("Вы уверены, что хотите выйти из аккаунта?")
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # Устанавливаем белый фон и черный текст для всего диалога
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: black;
                font-size: 11px;
            }
            QMessageBox QPushButton {
                background-color: #4a6fa5;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 70px;
                font-size: 11px;
            }
            QMessageBox QPushButton:hover {
                background-color: #3a5a80;
            }
            QMessageBox QPushButton:pressed {
                background-color: #2a4a70;
            }
        """)

        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            self.closed.emit()
            self.close()

    def closeEvent(self, event):
        #Закрытие соединения с БД при закрытии приложения
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass
        event.accept()