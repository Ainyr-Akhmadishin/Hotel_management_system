from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton, \
    QLabel
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
import sqlite3
import csv
import os
from utils import get_resource_path, get_database_path


class ImportPreviewDialog(QDialog):
    #Диалог предпросмотра импорта

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle("Предпросмотр импорта")
        self.setModal(True)
        self.setFixedSize(800, 600)

        self.setup_ui()
        self.load_preview_data()

    def setup_ui(self):
        #Настройка интерфейса диалога предпросмотра
        layout = QVBoxLayout(self)

        # Заголовок
        title_label = QLabel(f"Предпросмотр данных из файла: {os.path.basename(self.file_path)}")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        # Таблица предпросмотра
        self.preview_table = QtWidgets.QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.preview_table)

        # Информация о данных
        self.info_label = QLabel()
        self.info_label.setStyleSheet("margin: 5px; color: #666;")
        layout.addWidget(self.info_label)

        # Кнопки
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        self.import_btn = QPushButton("Импортировать")
        self.import_btn.clicked.connect(self.accept)
        self.import_btn.setStyleSheet("background-color: #4a6fa5; color: white; font-weight: bold;")

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.import_btn)

        layout.addLayout(button_layout)

    def load_preview_data(self):
        #Загрузка данных для предпросмотра
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as file:
                # Автоопределение разделителя
                sample = file.read(4096)
                file.seek(0)

                delimiter = ';' if ';' in sample else ','

                reader = csv.reader(file, delimiter=delimiter)
                rows = list(reader)

                if not rows:
                    self.info_label.setText("Файл пуст")
                    return

                # Настройка таблицы
                headers = rows[0]
                self.preview_table.setColumnCount(len(headers))
                self.preview_table.setHorizontalHeaderLabels(headers)

                # Показываем только первые 20 строк для предпросмотра
                preview_rows = rows[1:21]  # Пропускаем заголовок
                self.preview_table.setRowCount(len(preview_rows))

                for row_idx, row_data in enumerate(preview_rows):
                    for col_idx, cell_data in enumerate(row_data):
                        if col_idx < len(headers):
                            item = QTableWidgetItem(cell_data)
                            item.setForeground(QColor(0, 0, 0))
                            self.preview_table.setItem(row_idx, col_idx, item)

                # Информация о файле
                total_rows = len(rows) - 1  # Без заголовка
                preview_count = len(preview_rows)
                self.info_label.setText(
                    f"Всего строк: {total_rows}. Показано: {preview_rows}. "
                    f"Разделитель: '{delimiter}'. Колонки: {len(headers)}"
                )

                # Настройка ширины столбцов
                header = self.preview_table.horizontalHeader()
                for i in range(len(headers)):
                    header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        except Exception as e:
            self.info_label.setText(f"Ошибка чтения файла: {str(e)}")


class EmployeeListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(get_resource_path('UI/Admin/Список сотрудников переделанная.ui'), self)

        self.setWindowTitle("Список сотрудников")
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))

        # Инициализация БД
        db_path = get_database_path()
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # Настройка таблицы
        self.setup_table()

        # Загрузка данных
        self.load_employees_data()

        # Подключение сигналов
        self.export_button.clicked.connect(self.export_data)
        self.import_button.clicked.connect(self.import_data)
        self.refresh_button.clicked.connect(self.load_employees_data)
        self.search_lineEdit.textChanged.connect(self.filter_employees)
        self.sort_comboBox.currentTextChanged.connect(self.sort_employees)

    def setup_table(self):
        # Устанавливаем заголовки столбцов
        self.employees_table.setColumnCount(5)
        self.employees_table.setHorizontalHeaderLabels([
            'Фамилия', 'Имя', 'Отчество', 'Должность', 'Логин'
        ])

        # Настройка внешнего вида таблицы
        header = self.employees_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.employees_table.setAlternatingRowColors(True)
        self.employees_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.employees_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # Настройка ширины столбцов
        self.employees_table.setColumnWidth(0, 150)  # Фамилия
        self.employees_table.setColumnWidth(1, 120)  # Имя
        self.employees_table.setColumnWidth(2, 150)  # Отчество
        self.employees_table.setColumnWidth(3, 200)  # Должность

    def load_employees_data(self):
        #Загрузка из бд
        try:
            self.cursor.execute("""
                SELECT last_name, first_name, patronymic, position, login 
                FROM staff 
                ORDER BY last_name, first_name
            """)
            employees = self.cursor.fetchall()

            self.employees_table.setRowCount(len(employees))

            for row_idx, employee in enumerate(employees):
                for col_idx, data in enumerate(employee):
                    item = QTableWidgetItem(str(data) if data is not None else "")
                    # Устанавливаем черный цвет текста
                    item.setForeground(QColor(0, 0, 0))  # Черный цвет
                    self.employees_table.setItem(row_idx, col_idx, item)

            self.update_status(f"Загружено {len(employees)} сотрудников")

        except sqlite3.Error as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def filter_employees(self):
        #Фильтрация сотрудников
        search_text = self.search_lineEdit.text().lower()

        for row in range(self.employees_table.rowCount()):
            match = False
            for col in range(self.employees_table.columnCount()):
                item = self.employees_table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.employees_table.setRowHidden(row, not match)

    def sort_employees(self):
        #Сортировка сотрудников
        sort_type = self.sort_comboBox.currentText()

        try:
            if sort_type == "Сортировка по Фамилии":
                self.cursor.execute("""
                    SELECT last_name, first_name, patronymic, position, login 
                    FROM staff 
                    ORDER BY last_name, first_name
                """)
            else:  # Сортировка по Должности
                self.cursor.execute("""
                    SELECT last_name, first_name, patronymic, position, login 
                    FROM staff 
                    ORDER BY position, last_name
                """)

            employees = self.cursor.fetchall()

            self.employees_table.setRowCount(len(employees))

            for row_idx, employee in enumerate(employees):
                for col_idx, data in enumerate(employee):
                    item = QTableWidgetItem(str(data) if data is not None else "")
                    item.setForeground(QColor(0, 0, 0))  # Черный цвет
                    self.employees_table.setItem(row_idx, col_idx, item)

        except sqlite3.Error as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка сортировки: {str(e)}")

    def export_data(self):
        #Экспорт данных в CSV файл
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Экспорт данных сотрудников",
                f"сотрудники_{QDate.currentDate().toString('dd_MM_yyyy')}.csv",
                "CSV Files (*.csv)"
            )

            if file_path:
                self.export_to_csv(file_path)
                QMessageBox.information(self, "Успех", f"Данные экспортированы в {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")

    def export_to_csv(self, file_path):
        #Экспорт данных таблицы в CSV файл
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')

                # Записываем заголовки
                headers = []
                for col in range(self.employees_table.columnCount()):
                    header = self.employees_table.horizontalHeaderItem(col)
                    headers.append(header.text() if header else f"Column {col}")
                writer.writerow(headers)

                # Записываем данные
                for row in range(self.employees_table.rowCount()):
                    if not self.employees_table.isRowHidden(row):
                        row_data = []
                        for col in range(self.employees_table.columnCount()):
                            item = self.employees_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)

        except Exception as e:
            raise Exception(f"Ошибка записи файла: {str(e)}")

    def import_data(self):
        #Импорт данных из CSV
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Импорт данных сотрудников",
                "",
                "CSV Files (*.csv)"
            )

            if file_path:
                # Показываем диалог предпросмотра
                preview_dialog = ImportPreviewDialog(file_path, self)
                if preview_dialog.exec() == QDialog.DialogCode.Accepted:
                    # Если пользователь подтвердил импорт
                    self.import_from_csv(file_path)
                    QMessageBox.information(self, "Успех", "Данные успешно импортированы")
                else:
                    self.update_status("Импорт отменен")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка импорта: {str(e)}")

    def import_from_csv(self, file_path):
        #Импорт данных из CSV файла
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                # Автоопределение разделителя
                sample = file.read(4096)
                file.seek(0)

                delimiter = ';' if ';' in sample else ','

                reader = csv.reader(file, delimiter=delimiter)
                rows = list(reader)

                if not rows or len(rows) < 2:
                    QMessageBox.warning(self, "Ошибка", "Файл не содержит данных")
                    return

                # Проверяем соответствие структуры
                expected_headers = ['Фамилия', 'Имя', 'Отчество', 'Должность', 'Логин']
                file_headers = [h.strip() for h in rows[0]]

                # Если заголовки не совпадают, предупреждаем пользователя
                if file_headers != expected_headers:
                    reply = QMessageBox.question(
                        self,
                        "Несоответствие структуры",
                        f"Заголовки в файле: {file_headers}\n"
                        f"Ожидаемые заголовки: {expected_headers}\n\n"
                        "Продолжить импорт? Данные будут сопоставлены по порядку столбцов.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.No:
                        return

                # Пропускаем заголовок и добавляем данные в таблицу
                data_rows = rows[1:]
                self.employees_table.setRowCount(len(data_rows))

                imported_count = 0
                for row_idx, row_data in enumerate(data_rows):
                    # Пропускаем пустые строки
                    if not any(row_data):
                        continue

                    for col_idx, cell_data in enumerate(row_data):
                        if col_idx < self.employees_table.columnCount():
                            item = QTableWidgetItem(cell_data.strip())
                            item.setForeground(QColor(0, 0, 0))
                            self.employees_table.setItem(row_idx, col_idx, item)
                    imported_count += 1

                self.update_status(f"Импортировано {imported_count} сотрудников")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка импорта: {str(e)}")

    def update_status(self, message):
        self.statusbar.showMessage(message, 3000)  # Показываем сообщение 3 секунды

    def closeEvent(self, event):
        try:
            self.conn.close()
        except:
            pass
        event.accept()