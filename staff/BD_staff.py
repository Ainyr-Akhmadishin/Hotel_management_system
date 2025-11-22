import csv
import sqlite3
from datetime import datetime, timedelta

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QDialog, QTableWidgetItem, QFileDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6 import uic


class EmptyPathError(Exception):
    pass

class InvalidFileFormatError(Exception):
    pass

class UploadCleaningWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()

        uic.loadUi('UI/Reg/Окно сохранения данных.ui', self)
        self.setWindowTitle(f"Сохранение данных об уборке")
        self.get_data()
        self.allowed_formats = ['.csv', '.txt']


        self.monthRadio.toggled.connect(self.get_data)
        self.sixMonthsRadio.toggled.connect(self.get_data)
        self.yearRadio.toggled.connect(self.get_data)

        self.browseButton.clicked.connect(self.browse)
        self.exportButton.clicked.connect(self.save)

    def validate_file_format(self, file_path):
        file_extension = file_path[file_path.rfind('.'):].lower()
        if file_extension not in self.allowed_formats:
            raise InvalidFileFormatError(
                f"Недопустимый формат файла: {file_extension}. "
                f"Разрешены только: {', '.join(self.allowed_formats)}"
            )


    def save(self):
        try:
            current_file_path = self.filePathEdit.text()

            if not current_file_path:
                raise EmptyPathError

            self.validate_file_format(current_file_path)

            if current_file_path.lower().endswith('.txt'):
                self.save_as_txt(current_file_path)
            else:
                self.save_as_csv(current_file_path)

            QMessageBox.information(self, "Успех", f"Отчет об уборке успешно сохранен в:\n{current_file_path}")
            self.filePathEdit.clear()

        except InvalidFileFormatError as e:
            QMessageBox.critical(self, "Ошибка формата файла", str(e))
        except EmptyPathError:
            QMessageBox.critical(self, "Ошибка пустого пути", "Выберите путь для записи")
        except PermissionError:
            QMessageBox.critical(self, "Ошибка доступа", "Файл заблокирован или нет прав для записи")
        except FileNotFoundError:
            QMessageBox.critical(self, "Ошибка пути", "Указан неверный путь к файлу")
        except UnicodeEncodeError:
            QMessageBox.critical(self, "Ошибка кодировки", "Ошибка при сохранении русских символов")
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Произошла непредвиденная ошибка:\n{str(e)}")

    def save_as_csv(self, file_path):
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(
                f,
                delimiter=';',
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL)


            writer.writerow(
                [self.previewTable.horizontalHeaderItem(i).text()
                 for i in range(self.previewTable.columnCount())
                 ]
            )


            for i in self.data:
                writer.writerow(i)

    def save_as_txt(self, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:

            f.write("ОТЧЕТ ОБ УБОРКЕ ПОМЕЩЕНИЙ\n")
            f.write("=" * 120 + "\n")
            f.write(
                f"Период: с {self.start_date.strftime('%d.%m.%Y')} по {datetime.now().date().strftime('%d.%m.%Y')}\n")
            f.write("=" * 120 + "\n\n")

            headers = [self.previewTable.horizontalHeaderItem(i).text() for i in range(self.previewTable.columnCount())]

            col_widths = [len(header) for header in headers]
            for row in self.data:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

            col_widths = [width + 2 for width in col_widths]

            header_line = "".join([headers[i].ljust(col_widths[i]) for i in range(len(headers))])
            f.write(header_line + "\n")
            f.write("-" * len(header_line) + "\n")

            for row in self.data:
                row_line = "".join([str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)])
                f.write(row_line + "\n")

            f.write("\n" + "=" * 120 + "\n")

    def browse(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчет об уборке",
                f"отчет_уборки_за_период_{self.start_date.strftime('%d.%m.%Y')}-{datetime.now().date().strftime('%d.%m.%Y')}",
                "CSV Files (*.csv);;Text Files (*.txt)"
            )

            if file_path:
                self.filePathEdit.setText(file_path)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка выбора файла", f"Не удалось выбрать файл")

    def update_preview_table(self, data):
        try:
            if not data:
                self.previewTable.setRowCount(0)
                return

            headers = [
                'ID задачи', 'Комната', 'Тип уборки', 'Описание',
                'Создал', 'Должность создателя', 'Исполнитель', 'Должность исполнителя',
                'Создана', 'Начата', 'Завершена', 'Статус', 'Длительность (ч)', 'Примечания'
            ]

            self.previewTable.setColumnCount(len(headers))
            self.previewTable.setHorizontalHeaderLabels(headers)

            self.previewTable.setRowCount(len(data))

            for row_num, row_data in enumerate(data):
                for col_num, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    self.previewTable.setItem(row_num, col_num, item)

            self.previewTable.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка обновления таблицы", f"Не удалось обновить таблицу")

    def get_cleaning_data_query(self):
        return """
        SELECT 
            mt.id as task_id,
            mt.room_number as room,

            -- Тип уборки
            CASE 
                WHEN mt.description LIKE '%полная%' OR mt.description LIKE '%генеральная%' THEN 'Полная уборка'
                WHEN mt.description LIKE '%ежедневная%' OR mt.description LIKE '%регулярная%' THEN 'Ежедневная уборка'
                WHEN mt.description LIKE '%после выезда%' THEN 'Уборка после выезда'
                WHEN mt.description LIKE '%ремонт%' OR mt.description LIKE '%починка%' THEN 'Ремонтные работы'
                ELSE 'Стандартная уборка'
            END as cleaning_type,

            mt.description as task_description,

            -- Кто создал задачу
            creator.first_name || ' ' || creator.last_name as created_by,
            creator.position as creator_position,

            -- Кто принял задачу
            COALESCE(assignee.first_name || ' ' || assignee.last_name, 'Не назначена') as assigned_to,
            COALESCE(assignee.position, 'Не назначена') as assignee_position,

            -- Время создания задачи
            strftime('%d.%m.%Y %H:%M', mt.created_at) as task_created,

            -- Время начала задачи
            CASE 
                WHEN mt.status = 'в работе' OR mt.status = 'выполнена' THEN strftime('%d.%m.%Y %H:%M', mt.created_at)
                ELSE 'Не начата' 
            END as task_started,

            -- Время завершения задачи
            CASE 
                WHEN mt.completed_at IS NOT NULL THEN strftime('%d.%m.%Y %H:%M', mt.completed_at)
                ELSE 'Не завершена' 
            END as task_completed,

            -- Статус задачи
            mt.status as task_status,

            -- Длительность выполнения (в часах)
            CASE 
                WHEN mt.completed_at IS NOT NULL AND mt.created_at IS NOT NULL THEN
                    ROUND((JULIANDAY(mt.completed_at) - JULIANDAY(mt.created_at)) * 24, 2)
                ELSE NULL
            END as duration_hours,

            -- Примечания к задаче
            COALESCE(mt.notes, 'Нет примечаний') as task_notes

        FROM maintenance_tasks mt
        LEFT JOIN staff creator ON mt.created_by = creator.id
        LEFT JOIN staff assignee ON mt.assigned_to = assignee.id
        WHERE date(mt.created_at) BETWEEN date(?) AND date('now')
        ORDER BY mt.created_at DESC
        """

    def get_data(self):
        try:
            self.filePathEdit.clear()
            today = datetime.now().date()

            if self.monthRadio.isChecked():
                self.start_date = today - timedelta(days=30)
            elif self.sixMonthsRadio.isChecked():
                self.start_date = today - timedelta(days=180)
            elif self.yearRadio.isChecked():
                self.start_date = today - timedelta(days=365)
            else:
                self.start_date = today - timedelta(days=30)  # По умолчанию месяц

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute(self.get_cleaning_data_query(), (self.start_date.strftime('%Y-%m-%d'),))
            self.data = cursor.fetchall()

            self.update_preview_table(self.data)

            conn.close()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось загрузить данные об уборке: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки данных", f"Произошла непредвиденная ошибка:\n{str(e)}")

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()