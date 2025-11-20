from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox, QDialog, QFileDialog
from PyQt6.QtCore import QDate
import sqlite3
import csv
from datetime import datetime
from utils import get_resource_path


class EmployeeListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(get_resource_path('UI/Admin/Список сотрудников переделанная.ui'), self)

        self.setWindowTitle("Список сотрудников")
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))

        # Устанавливаем полноэкранный режим
        self.showMaximized()

        # Инициализация БД
        self.conn = sqlite3.connect('Hotel_bd.db')
        self.cursor = self.conn.cursor()

        # Подключаем кнопки
        self.export_button.clicked.connect(self.export_data)
        self.refresh_button.clicked.connect(self.load_employees)
        self.sort_comboBox.currentTextChanged.connect(self.sort_employees)
        self.search_lineEdit.textChanged.connect(self.search_employees)

        # Список меток для сотрудников (организовано по колонкам)
        self.employee_labels = []
        # Создаем матрицу меток: 5 строк × 4 колонки
        self.label_matrix = [
            [self.label_3, self.label_5, self.label_4, self.label_8],  # строка 0
            [self.label_6, self.label_7, self.label_9, self.label_10],  # строка 1
            [self.label_11, self.label_12, self.label_13, self.label_14],  # строка 2
            [self.label_15, self.label_16, self.label_17, self.label_18],  # строка 3
            [self.label_19, self.label_20, self.label_21, self.label_22]  # строка 4
        ]

        # Преобразуем матрицу в плоский список для удобства
        for row in self.label_matrix:
            self.employee_labels.extend(row)

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
        """Отображение сотрудников в интерфейсе (слева направо, сверху вниз)"""
        # Очищаем все метки
        for label in self.employee_labels:
            label.setText("Пусто")
            label.setStyleSheet(
                "padding: 6px 10px; border-radius: 3px; color: #999999; background-color: #f8f9fa; font-style: italic;")
            label.setVisible(True)

        # Фильтруем только валидных сотрудников
        valid_employees = [emp for emp in employees if emp[0] and emp[1] and emp[3]]

        if not valid_employees:
            # Если нет сотрудников, показываем сообщение в первой ячейке
            self.label_3.setText("Нет сотрудников для отображения")
            self.label_3.setStyleSheet(
                "padding: 6px 10px; border-radius: 3px; color: #666666; background-color: #f8f9fa; font-weight: bold;")
            return

        # Заполняем метки по колонкам (сначала заполняем колонку, потом переходим к следующей)
        employee_index = 0
        total_employees = len(valid_employees)

        # Проходим по колонкам (всего 4 колонки)
        for col in range(4):  # 4 колонки
            for row in range(5):  # 5 строк
                if employee_index >= total_employees:
                    break

                first_name, last_name, patronymic, position = valid_employees[employee_index]

                full_name = f"{last_name} {first_name}"
                if patronymic:
                    full_name += f" {patronymic}"

                # Добавляем должность в скобках
                full_name += f" ({position})"

                # Устанавливаем текст в соответствующую метку
                label = self.label_matrix[row][col]
                label.setText(full_name)

                # Разные цвета для разных должностей
                if position.lower() == 'администратор':
                    label.setStyleSheet(
                        "background-color: #e3f2fd; padding: 6px 10px; border-radius: 3px; font-weight: bold; color: #000000;"
                    )
                elif position.lower() == 'регистратор':
                    label.setStyleSheet(
                        "background-color: #e8f5e8; padding: 6px 10px; border-radius: 3px; color: #000000;"
                    )
                else:
                    label.setStyleSheet(
                        "background-color: #fff3cd; padding: 6px 10px; border-radius: 3px; color: #000000;"
                    )

                employee_index += 1

    def sort_employees(self):
        """Сортировка сотрудников"""
        sort_option = self.sort_comboBox.currentText()

        if not self.all_employees:
            return

        # Фильтруем пустые записи перед сортировкой
        filtered_employees = [emp for emp in self.all_employees if emp[0] and emp[1] and emp[3]]

        if sort_option == "Сортировка по Фамилии":
            sorted_employees = sorted(filtered_employees, key=lambda x: x[1])  # last_name
        elif sort_option == "Сортировка по Должности":
            sorted_employees = sorted(filtered_employees, key=lambda x: x[3])  # position
        else:
            sorted_employees = filtered_employees

        self.display_employees(sorted_employees)

    def search_employees(self):
        """Поиск сотрудников"""
        search_text = self.search_lineEdit.text().strip().lower()

        if not search_text:
            # При отмене поиска показываем всех сотрудников (без пустых)
            filtered_employees = [emp for emp in self.all_employees if emp[0] and emp[1] and emp[3]]
            self.display_employees(filtered_employees)
            return

        filtered_employees = []
        for first_name, last_name, patronymic, position in self.all_employees:
            # Пропускаем пустые записи
            if not first_name or not last_name or not position:
                continue

            if (search_text in first_name.lower() or
                    search_text in last_name.lower() or
                    search_text in (patronymic or "").lower() or
                    search_text in position.lower()):
                filtered_employees.append((first_name, last_name, patronymic, position))

        self.display_employees(filtered_employees)

    def export_data(self):
        """Экспорт данных в CSV с правильной кодировкой"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Экспорт данных", f"сотрудники_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )

            if file_path:
                # Фильтруем пустые записи перед экспортом
                valid_employees = [emp for emp in self.all_employees if emp[0] and emp[1] and emp[3]]

                if not valid_employees:
                    QMessageBox.warning(self, "Предупреждение", "Нет данных для экспорта")
                    return

                # Используем кодировку utf-8-sig для правильного отображения кириллицы в Excel
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file, delimiter=';')  # Используем точку с запятой как разделитель
                    writer.writerow(['Фамилия', 'Имя', 'Отчество', 'Должность', 'Дата экспорта'])

                    for first_name, last_name, patronymic, position in valid_employees:
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

    def closeEvent(self, event):
        """Закрытие соединения с БД"""
        try:
            self.conn.close()
        except:
            pass
        event.accept()