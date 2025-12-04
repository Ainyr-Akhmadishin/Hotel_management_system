import sys
import sqlite3
import hashlib

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6 import uic


from admin.Admin import AdminWindow
from regist.regist_script import RegistrarWindow
from staff.staff_script import StaffWindow

from sync_update import SimpleAutoSync

from utils import get_resource_path, get_database_path

class EmptyCredentialsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.start_sync()

        uic.loadUi(get_resource_path('UI/Вход в систему итог.ui'), self)


        self.pushButton.clicked.connect(self.login)
        self.lineEdit_3.returnPressed.connect(self.login)

        self.employee_window = None
        self.admin_window = None
        self.registrar_window = None
        self.load_saved_credentials()

    def load_saved_credentials(self):

        settings = QSettings("HotelApp", "Login")

        remember_me = settings.value("remember_me", False, type=bool)

        if remember_me:
            username = settings.value("username", "")
            password = settings.value("password", "")

            self.lineEdit.setText(username)
            self.lineEdit_3.setText(password)

            self.remember_me_checkbox.setChecked(True)

    def save_credentials(self, username, password, remember_me):
        settings = QSettings("HotelApp", "Login")

        if remember_me:
            settings.setValue("remember_me", True)
            settings.setValue("username", username)
            settings.setValue("password", password)
        else:
            settings.remove("remember_me")
            settings.remove("username")
            settings.remove("password")

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_credentials(self, username, password):
        try:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            password_hash = self.hash_password(password)

            cursor.execute('''
                SELECT first_name, last_name, position FROM staff 
                WHERE login = ? AND password_hash = ?
            ''', (username, password_hash))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'first_name': result[0],
                    'last_name': result[1],
                    'position': result[2]
                }
            return None

        except sqlite3.Error as e:
            QMessageBox.warning(self, "Ошибка", "Ошибка базы данных")
            return None
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", "Неизвестная ошибка")



    def login(self):
        try:
            username = self.lineEdit.text()
            password = self.lineEdit_3.text()

            if not username or not password:
                raise EmptyCredentialsError("Введите логин и пароль")

            user_info = self.verify_credentials(username, password)

            if not user_info:
                raise InvalidCredentialsError("Неверный логин или пароль")

            remember_me = self.remember_me_checkbox.isChecked()

            self.save_credentials(username, password, remember_me)

            position = user_info['position']
            full_name = f"{user_info['first_name']} {user_info['last_name']}"
            self.open_role_window(position, full_name, username)

        except EmptyCredentialsError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except InvalidCredentialsError as e:
            QMessageBox.warning(self, "Ошибка авторизации", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Произошла непредвиденная ошибка: {str(e)}")

    def open_role_window(self, position, full_name, username):
        self.hide()
        if position == "обслуживающий персонал":
            self.staff_window = StaffWindow(full_name, username)
            self.staff_window.show()
            self.staff_window.closed.connect(self.show_login)

        elif position == "администратор":
            self.admin_window = AdminWindow(full_name, username)
            self.admin_window.show()
            self.admin_window.closed.connect(self.show_login)

        elif position == "регистратор":
            self.registrar_window = RegistrarWindow(full_name, username)
            self.registrar_window.show()
            self.registrar_window.closed.connect(self.show_login)

    def show_login(self):
        self.lineEdit.clear()
        self.lineEdit_3.clear()
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())