from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtCore import QDate
import sqlite3
import hashlib
from utils import get_resource_path

class EmployeeManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(get_resource_path('UI/Admin/Добавить или удалить сотрудника переделенная.ui'), self)

        self.setWindowTitle("Управление персоналом")
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))

        # Инициализация БД
        self.conn = sqlite3.connect('Hotel_bd.db')
        self.cursor = self.conn.cursor()

        # Подключаем кнопки
        self.add_employee_btn.clicked.connect(self.add_employee)
        self.fire_selected_btn.clicked.connect(self.fire_employee)
        self.search_edit.textChanged.connect(self.search_employees)

        # Группа для кнопок сотрудников
        self.employee_buttons = []
        for i in range(1, 15):
            button = getattr(self, f'employee_btn_{i}')
            button.clicked.connect(self.create_button_handler(button))
            self.employee_buttons.append(button)

        # Загружаем сотрудников
        self.load_employees()
        self.selected_employee = None

    def create_button_handler(self, button):
        """Создает обработчик для кнопки сотрудника"""

        def handler():
            self.select_employee(button)

        return handler

    def select_employee(self, button):
        """Выбор сотрудника"""
        # Сбрасываем выделение у всех кнопок
        for btn in self.employee_buttons:
            btn.setStyleSheet(
                "background-color: #f8f9fa; color: #2c3e50; border: 1px solid #e1e5eb; text-align: left; padding: 8px 12px;")
            btn.setChecked(False)

        # Выделяем выбранную кнопку
        button.setStyleSheet(
            "background-color: #4a6fa5; color: white; border: 1px solid #3a5a80; text-align: left; padding: 8px 12px;")
        button.setChecked(True)

        self.selected_employee = button.text()
        self.selected_employee_label.setText(f"Выбран: {self.selected_employee}")
        self.fire_selected_btn.setEnabled(True)

    def load_employees(self):
        """Загрузка сотрудников из БД"""
        try:
            # Очищаем кнопки
            for button in self.employee_buttons:
                button.setText("")
                button.setVisible(False)

            # Загружаем сотрудников
            self.cursor.execute("""
                SELECT first_name, last_name, patronymic, position 
                FROM staff 
                ORDER BY 
                    CASE 
                        WHEN position = 'администратор' THEN 1
                        WHEN position = 'регистратор' THEN 2
                        ELSE 3 
                    END,
                    last_name
            """)
            employees = self.cursor.fetchall()

            # Распределяем по колонкам
            registry_index = 0
            staff_index = 0

            for first_name, last_name, patronymic, position in employees:
                full_name = f"{last_name} {first_name}"
                if patronymic:
                    full_name += f" {patronymic}"

                if position in ['администратор', 'регистратор']:
                    # Регистратура - левая колонка
                    if registry_index < 7:
                        button = self.employee_buttons[registry_index * 2]
                        button.setText(full_name)
                        button.setVisible(True)
                        registry_index += 1
                else:
                    # Персонал - правая колонка
                    if staff_index < 7:
                        button = self.employee_buttons[staff_index * 2 + 1]
                        button.setText(full_name)
                        button.setVisible(True)
                        staff_index += 1

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки сотрудников: {str(e)}")

    def search_employees(self):
        """Поиск сотрудников"""
        search_text = self.search_edit.text().strip().lower()

        if not search_text:
            self.load_employees()
            return

        try:
            self.cursor.execute("""
                SELECT first_name, last_name, patronymic, position 
                FROM staff 
                WHERE lower(first_name) LIKE ? OR lower(last_name) LIKE ? OR lower(patronymic) LIKE ?
                ORDER BY last_name
            """, (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%'))

            employees = self.cursor.fetchall()

            # Очищаем кнопки
            for button in self.employee_buttons:
                button.setText("")
                button.setVisible(False)

            # Заполняем результаты поиска
            for i, (first_name, last_name, patronymic, position) in enumerate(employees):
                if i >= len(self.employee_buttons):
                    break

                full_name = f"{last_name} {first_name}"
                if patronymic:
                    full_name += f" {patronymic}"

                button = self.employee_buttons[i]
                button.setText(full_name)
                button.setVisible(True)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {str(e)}")

    def add_employee(self):
        """Добавление нового сотрудника"""
        try:
            from PyQt6.QtWidgets import QInputDialog

            # Ввод данных
            first_name, ok = QInputDialog.getText(self, "Добавление сотрудника", "Введите имя:")
            if not ok or not first_name.strip():
                return

            last_name, ok = QInputDialog.getText(self, "Добавление сотрудника", "Введите фамилию:")
            if not ok or not last_name.strip():
                return

            patronymic, ok = QInputDialog.getText(self, "Добавление сотрудника", "Введите отчество:")
            if not ok:
                patronymic = ""

            position, ok = QInputDialog.getItem(self, "Добавление сотрудника", "Выберите должность:",
                                                ['администратор', 'регистратор', 'обслуживающий персонал'], 0, False)
            if not ok:
                return

            login, ok = QInputDialog.getText(self, "Добавление сотрудника", "Введите логин:")
            if not ok or not login.strip():
                return

            password, ok = QInputDialog.getText(self, "Добавление сотрудника", "Введите пароль:")
            if not ok or not password.strip():
                return

            # Хешируем пароль
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Добавляем в БД
            self.cursor.execute('''
                INSERT INTO staff (first_name, last_name, patronymic, login, password_hash, position)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (first_name.strip(), last_name.strip(), patronymic.strip(), login.strip(), password_hash, position))

            self.conn.commit()

            QMessageBox.information(self, "Успех", "Сотрудник успешно добавлен!")
            self.load_employees()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Сотрудник с таким логином уже существует!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления сотрудника: {str(e)}")

    def fire_employee(self):
        """Увольнение выбранного сотрудника"""
        if not self.selected_employee:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника для увольнения!")
            return

        try:
            # Извлекаем фамилию из выбранного сотрудника
            last_name = self.selected_employee.split()[0]

            reply = QMessageBox.question(self, "Подтверждение",
                                         f"Вы уверены, что хотите уволить {self.selected_employee}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                self.cursor.execute("DELETE FROM staff WHERE last_name = ?", (last_name,))
                self.conn.commit()

                QMessageBox.information(self, "Успех", f"Сотрудник {self.selected_employee} уволен!")
                self.selected_employee = None
                self.selected_employee_label.setText("Выбран: нет")
                self.fire_selected_btn.setEnabled(False)
                self.load_employees()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка увольнения сотрудника: {str(e)}")

    def closeEvent(self, event):
        """Закрытие соединения с БД"""
        try:
            self.conn.close()
        except:
            pass
        event.accept()