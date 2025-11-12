from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox, QDialog, QFileDialog
from PyQt6.QtCore import QDate
import sqlite3
import csv
from datetime import datetime


class EmployeeListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('Список сотрудников переделанная.ui', self)

        self.setWindowTitle("Список сотрудников")
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))

        # Инициализация БД
        self.conn = sqlite3.connect('Hotel_bd.db')
        self.cursor = self.conn.cursor()

        # Подключаем кнопки
        self.export_button.clicked.connect(self.export_data)
        self.add_button.clicked.connect(self.add_employee)
        self.refresh_button.clicked.connect(self.load_employees)
        self.sort_comboBox.currentTextChanged.connect(self.sort_employees)
        self.search_lineEdit.textChanged.connect(self.search_employees)

        # Список меток для сотрудников
        self.employee_labels = []
        for i in range(3, 23):  # label_3 to label_22
            label = getattr(self, f'label_{i}')
            self.employee_labels.append(label)

        # Загружаем сотрудников
        self.all_employees = []
        self.load_employees()

    def load_employees(self):
        """Загрузка сотрудников из БД"""
        try:
            self.cursor.execute("""
                SELECT first_name, last_name, patronymic, position 
                FROM staff 
                ORDER BY last_name, first_name
            """)
            self.all_employees = self.cursor.fetchall()
            self.display_employees(self.all_employees)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки сотрудников: {str(e)}")

    def display_employees(self, employees):
        """Отображение сотрудников в интерфейсе"""
        # Очищаем метки
        for label in self.employee_labels:
            label.setText("")
            label.setStyleSheet("padding: 4px 8px; border-radius: 3px;")

        # Заполняем метки
        for i, (first_name, last_name, patronymic, position) in enumerate(employees):
            if i >= len(self.employee_labels):
                break

            full_name = f"{last_name} {first_name}"
            if patronymic:
                full_name += f" {patronymic}"

            # Добавляем должность в скобках
            full_name += f" ({position})"

            self.employee_labels[i].setText(full_name)

            # Разные цвета для разных должностей
            if position == 'администратор':
                self.employee_labels[i].setStyleSheet(
                    "padding: 4px 8px; border-radius: 3px; background-color: #e3f2fd; font-weight: bold;"
                )
            elif position == 'регистратор':
                self.employee_labels[i].setStyleSheet(
                    "padding: 4px 8px; border-radius: 3px; background-color: #e8f5e8;"
                )
            else:
                self.employee_labels[i].setStyleSheet(
                    "padding: 4px 8px; border-radius: 3px; background-color: #fff3cd;"
                )

    def sort_employees(self):
        """Сортировка сотрудников"""
        sort_option = self.sort_comboBox.currentText()

        if not self.all_employees:
            return

        if sort_option == "Сортировка по Фамилии":
            sorted_employees = sorted(self.all_employees, key=lambda x: x[1])  # last_name
        elif sort_option == "Сортировка по Имени":
            sorted_employees = sorted(self.all_employees, key=lambda x: x[0])  # first_name
        elif sort_option == "Сортировка по Должности":
            sorted_employees = sorted(self.all_employees, key=lambda x: x[3])  # position
        else:
            sorted_employees = self.all_employees

        self.display_employees(sorted_employees)

    def search_employees(self):
        """Поиск сотрудников"""
        search_text = self.search_lineEdit.text().strip().lower()

        if not search_text:
            self.display_employees(self.all_employees)
            return

        filtered_employees = []
        for first_name, last_name, patronymic, position in self.all_employees:
            if (search_text in first_name.lower() or
                    search_text in last_name.lower() or
                    search_text in (patronymic or "").lower() or
                    search_text in position.lower()):
                filtered_employees.append((first_name, last_name, patronymic, position))

        self.display_employees(filtered_employees)

    def export_data(self):
        """Экспорт данных в CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Экспорт данных", f"сотрудники_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )

            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Фамилия', 'Имя', 'Отчество', 'Должность', 'Дата экспорта'])

                    for first_name, last_name, patronymic, position in self.all_employees:
                        writer.writerow([
                            last_name,
                            first_name,
                            patronymic or '',
                            position,
                            datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                        ])

                QMessageBox.information(self, "Успех", f"Данные экспортированы в {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта данных: {str(e)}")

    def add_employee(self):
        """Добавление нового сотрудника"""
        try:
            from PyQt6.QtWidgets import QInputDialog
            import hashlib

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

    def closeEvent(self, event):
        """Закрытие соединения с БД"""
        try:
            self.conn.close()
        except:
            pass
        event.accept()