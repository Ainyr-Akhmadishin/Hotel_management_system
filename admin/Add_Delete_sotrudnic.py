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

        # Группа для кнопок сотрудников - теперь 21 кнопка
        self.employee_buttons = []
        for i in range(1, 22):  # Изменено с 15 на 22
            try:
                button = getattr(self, f'employee_btn_{i}')
                button.clicked.connect(self.create_button_handler(button))
                self.employee_buttons.append(button)
            except AttributeError:
                # Если кнопки не существует, пропускаем
                continue

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
                "background-color: #ffffff; color: #2c3e50; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
            btn.setChecked(False)

        # Если выбрана кнопка "Пусто", выделяем ее и устанавливаем выбор
        if button.text() == "Пусто":
            button.setStyleSheet(
                "background-color: #4a6fa5; color: white; border: 1px solid #3a5a80; text-align: left; padding: 10px 15px; border-radius: 4px;")
            button.setChecked(True)
            self.selected_employee = "Пусто"
            self.selected_employee_label.setText("Выбран: Пусто")
            self.fire_selected_btn.setEnabled(True)
            return

        # Выделяем выбранную кнопку с сотрудником
        button.setStyleSheet(
            "background-color: #4a6fa5; color: white; border: 1px solid #3a5a80; text-align: left; padding: 10px 15px; border-radius: 4px;")
        button.setChecked(True)

        self.selected_employee = button.text()
        self.selected_employee_label.setText(f"Выбран: {self.selected_employee}")
        self.fire_selected_btn.setEnabled(True)

    def load_employees(self):
        """Загрузка сотрудников из БД"""
        try:
            # Очищаем кнопки
            for button in self.employee_buttons:
                button.setText("Пусто")
                button.setVisible(True)
                button.setStyleSheet(
                    "background-color: #ffffff; color: #cccccc; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
                button.setChecked(False)

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

            # Распределяем по колонкам (3 колонки по 7 строк)
            admin_index = 0      # Колонка 0 - Администраторы (кнопки 15, 16, 17, 18, 19, 20, 21)
            registry_index = 0   # Колонка 1 - Регистраторы (кнопки 1, 3, 5, 7, 9, 11, 13)
            staff_index = 0      # Колонка 2 - Персонал (кнопки 2, 4, 6, 8, 10, 12, 14)

            for first_name, last_name, patronymic, position in employees:
                full_name = f"{last_name} {first_name}"
                if patronymic:
                    full_name += f" {patronymic}"

                if position == 'администратор':
                    # Администраторы - левая колонка (кнопки 15-21)
                    if admin_index < 7:
                        button_index = 14 + admin_index  # 14-20
                        if button_index < len(self.employee_buttons):
                            button = self.employee_buttons[button_index]
                            button.setText(full_name)
                            button.setStyleSheet(
                                "background-color: #ffffff; color: #2c3e50; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
                            admin_index += 1
                elif position == 'регистратор':
                    # Регистраторы - средняя колонка (кнопки 1,3,5,7,9,11,13)
                    if registry_index < 7:
                        button_index = registry_index * 2  # 0,2,4,6,8,10,12
                        if button_index < len(self.employee_buttons):
                            button = self.employee_buttons[button_index]
                            button.setText(full_name)
                            button.setStyleSheet(
                                "background-color: #ffffff; color: #2c3e50; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
                            registry_index += 1
                else:
                    # Персонал - правая колонка (кнопки 2,4,6,8,10,12,14)
                    if staff_index < 7:
                        button_index = staff_index * 2 + 1  # 1,3,5,7,9,11,13
                        if button_index < len(self.employee_buttons):
                            button = self.employee_buttons[button_index]
                            button.setText(full_name)
                            button.setStyleSheet(
                                "background-color: #ffffff; color: #2c3e50; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
                            staff_index += 1

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки сотрудников: {str(e)}")
        except IndexError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка распределения сотрудников: {str(e)}")

    def search_employees(self):
        """Поиск сотрудников по фамилии"""
        search_text = self.search_edit.text().strip()

        if not search_text:
            self.load_employees()
            return

        try:
            # Поиск по фамилии (без учета регистра)
            self.cursor.execute("""
                SELECT first_name, last_name, patronymic, position 
                FROM staff 
                WHERE last_name LIKE ? OR last_name LIKE ? OR last_name LIKE ?
                ORDER BY 
                    CASE 
                        WHEN position = 'администратор' THEN 1
                        WHEN position = 'регистратор' THEN 2
                        ELSE 3 
                    END,
                    last_name
            """, (f'{search_text}%', f'%{search_text}%', f'%{search_text}'))

            employees = self.cursor.fetchall()

            # Очищаем кнопки
            for button in self.employee_buttons:
                button.setText("Пусто")
                button.setStyleSheet(
                    "background-color: #ffffff; color: #cccccc; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
                button.setChecked(False)

            # Распределяем найденных сотрудников по колонкам
            admin_index = 0      # Колонка 0 - Администраторы
            registry_index = 0   # Колонка 1 - Регистраторы
            staff_index = 0      # Колонка 2 - Персонал

            for first_name, last_name, patronymic, position in employees:
                full_name = f"{last_name} {first_name}"
                if patronymic:
                    full_name += f" {patronymic}"

                if position == 'администратор':
                    if admin_index < 7:
                        button_index = 14 + admin_index
                        if button_index < len(self.employee_buttons):
                            button = self.employee_buttons[button_index]
                            button.setText(full_name)
                            button.setStyleSheet(
                                "background-color: #ffffff; color: #2c3e50; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
                            admin_index += 1
                elif position == 'регистратор':
                    if registry_index < 7:
                        button_index = registry_index * 2
                        if button_index < len(self.employee_buttons):
                            button = self.employee_buttons[button_index]
                            button.setText(full_name)
                            button.setStyleSheet(
                                "background-color: #ffffff; color: #2c3e50; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
                            registry_index += 1
                else:
                    if staff_index < 7:
                        button_index = staff_index * 2 + 1
                        if button_index < len(self.employee_buttons):
                            button = self.employee_buttons[button_index]
                            button.setText(full_name)
                            button.setStyleSheet(
                                "background-color: #ffffff; color: #2c3e50; border: 1px solid #e1e5eb; text-align: left; padding: 10px 15px; border-radius: 4px;")
                            staff_index += 1

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {str(e)}")
        except IndexError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка распределения при поиске: {str(e)}")

    def validate_name(self, name):
        """Проверка имени/фамилии/отчества"""
        if not name:
            return False
        if len(name) < 2:
            return False
        if not name[0].isupper():
            return False
        if not name.replace('-', '').isalpha():  # Разрешаем дефисы в именах
            return False
        return True

    def add_employee(self):
        """Добавление нового сотрудника"""
        try:
            from PyQt6.QtWidgets import QInputDialog

            # Ввод ФИО одним полем
            full_name, ok = QInputDialog.getText(self, "Добавление сотрудника",
                                                "Введите ФИО сотрудника (обязательно фамилия и имя):")
            if not ok or not full_name.strip():
                return

            # Проверка на количество слов
            name_parts = full_name.strip().split()
            if len(name_parts) < 2:
                QMessageBox.warning(self, "Ошибка", "Введите фамилию и имя (минимум 2 слова)!")
                return

            # Извлекаем фамилию и имя
            last_name = name_parts[0]
            first_name = name_parts[1]
            patronymic = name_parts[2] if len(name_parts) > 2 else ""

            # Проверка фамилии
            if not self.validate_name(last_name):
                QMessageBox.warning(self, "Ошибка",
                                  "Фамилия должна:\n- Содержать минимум 2 буквы\n- Начинаться с заглавной буквы\n- Содержать только буквы")
                return

            # Проверка имени
            if not self.validate_name(first_name):
                QMessageBox.warning(self, "Ошибка",
                                  "Имя должно:\n- Содержать минимум 2 буквы\n- Начинаться с заглавной буквы\n- Содержать только буквы")
                return

            # Проверка отчества (если есть)
            if patronymic and not self.validate_name(patronymic):
                QMessageBox.warning(self, "Ошибка",
                                  "Отчество должно:\n- Содержать минимум 2 буквы\n- Начинаться с заглавной буквы\n- Содержать только буквы")
                return

            # Выбор должности
            position, ok = QInputDialog.getItem(self, "Добавление сотрудника", "Выберите должность:",
                                                ['администратор', 'регистратор', 'обслуживающий персонал'], 0, False)
            if not ok:
                return

            # Ввод логина
            login, ok = QInputDialog.getText(self, "Добавление сотрудника", "Введите логин:")
            if not ok or not login.strip():
                return

            # Ввод пароля
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

        # Проверяем, если выбрано "Пусто"
        if self.selected_employee == "Пусто":
            QMessageBox.warning(self, "Ошибка", "Нельзя уволить 'Пусто'! Выберите реального сотрудника.")
            return

        try:
            # Извлекаем фамилию и имя из выбранного сотрудника
            parts = self.selected_employee.split()
            if len(parts) >= 2:
                last_name = parts[0]
                first_name = parts[1]
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный формат имени сотрудника!")
                return

            reply = QMessageBox.question(self, "Подтверждение",
                                         f"Вы уверены, что хотите уволить {self.selected_employee}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                self.cursor.execute("DELETE FROM staff WHERE last_name = ? AND first_name = ?",
                                   (last_name, first_name))
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