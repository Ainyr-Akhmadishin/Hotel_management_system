import csv
import sqlite3
from datetime import datetime, timedelta

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QDialog, QTableWidgetItem, QFileDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6 import uic
from regist.regist_exceptions import EmptyPathError

class UploadWindow(QMainWindow):
    closed = pyqtSignal()
    def __init__(self):
        super().__init__()

        uic.loadUi('UI/Reg/Окно сохранения данных.ui', self)
        self.setWindowTitle(f"Сохранение данных о брони")
        self.get_data()
        self.monthRadio.toggled.connect(self.get_data)
        self.sixMonthsRadio.toggled.connect(self.get_data)

        self.yearRadio.toggled.connect(self.get_data)

        self.browseButton.clicked.connect(self.browse)

        self.exportButton.clicked.connect(self.save)

    def save(self):
        try:
            current_file_path = self.filePathEdit.text()

            if not current_file_path:
                raise EmptyPathError

            if current_file_path.lower().endswith('.txt'):
                self.save_as_txt(current_file_path)
            else:
                self.save_as_csv(current_file_path)

            QMessageBox.information(self, "Успех", f"Отчет успешно сохранен в:\n{current_file_path}")
            self.filePathEdit.clear()
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

            f.write("ОТЧЕТ О БРОНИРОВАНИЯХ\n")
            f.write("=" * 100 + "\n")
            f.write(
                f"Период: с {self.start_date.strftime('%d.%m.%Y')} по {datetime.now().date().strftime('%d.%m.%Y')}\n")
            f.write("=" * 100 + "\n\n")


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

            f.write("\n" + "=" * 100 + "\n")

    def browse(self):

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчет о бронированиях",
                f"отчет_бронирования_за_период_{self.start_date.strftime('%d.%m.%Y')}-{datetime.now().date().strftime('%d.%m.%Y')}",
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

            headers = ['Номер', 'Гость', 'Заезд', 'Выезд', 'Ночей', 'Тип', 'Стоимость', 'Общая стоимость', 'Статус']
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
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            cursor.execute('''SELECT 
                                         room_number, 
                                         last_name || '.' || SUBSTR(first_name,1,1) || '.' || SUBSTR(patronymic,1,1) as guest_initials, 
                                         check_in_date, 
                                         check_out_date,
                                         CAST(JULIANDAY(check_out_date) - JULIANDAY(check_in_date) AS INTEGER) as nights,
                                         room_type, 
                                         price_per_night, 
                                         (CAST(JULIANDAY(check_out_date) - JULIANDAY(check_in_date) AS INTEGER) * price_per_night) as total_cost,
                                         CASE 
                                           WHEN date(check_out_date) < date('now') THEN 'Завершено'
                                           WHEN date(check_in_date) <= date('now') THEN 'Активно'
                                           ELSE 'Ожидается'
                                         END as booking_status
                                FROM rooms JOIN bookings ON rooms.id = bookings.room_id 
                                JOIN guests ON bookings.guest_id = guests.id
                                WHERE check_in_date BETWEEN date(?) AND date('now')
                                ORDER BY check_in_date, room_number''', (self.start_date.strftime('%Y-%m-%d'),))

            self.data = cursor.fetchall()
            self.update_preview_table(self.data)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось загрузить базу данных")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки данных", f"Произошла непредвиденная ошибка:\n{str(e)}")

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()