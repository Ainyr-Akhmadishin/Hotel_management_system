import sys
import sqlite3
import hashlib
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6 import uic


from admin.admin_script import AdminWindow
from regist.regist_script import RegistrarWindow
from staff.staff_script import StaffWindow


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('UI/Вход в систему итог.ui', self)


        self.pushButton.clicked.connect(self.login)
        self.lineEdit_3.returnPressed.connect(self.login)


        self.employee_window = None
        self.admin_window = None
        self.registrar_window = None


    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_credentials(self, username, password):
        try:
            conn = sqlite3.connect('Hotel_bd.db')
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
            print(f"Ошибка базы данных: {e}")
            return None

    def login(self):
        username = self.lineEdit.text()
        password = self.lineEdit_3.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return


        user_info = self.verify_credentials(username, password)

        if user_info:
            position = user_info['position']
            full_name = f"{user_info['first_name']} {user_info['last_name']}"
            self.open_role_window(position, full_name, username)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

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