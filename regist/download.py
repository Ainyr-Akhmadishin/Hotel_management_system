import csv
import sqlite3
from datetime import datetime

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QDialog, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6 import uic

from regist.guest_registration_window import GuestRegistrationWindow
from regist.regist_exceptions import *
from regist.validation_dialog import DataValidationDialog
from utils import get_resource_path, get_database_path


# from regist.upload_or_download import UDWindow


class DownloadWindow(QMainWindow):
    closed = pyqtSignal()
    data_updated = pyqtSignal()
    def __init__(self):
        super().__init__()

        uic.loadUi(get_resource_path('UI/Reg/Загрузка данных итог.ui'), self)
        self.setWindowTitle(f"Загрузка данных о брони")
        self.browseButton.clicked.connect(self.browse)
        self.loadButton.clicked.connect(self.download)
        self.cancelButton.clicked.connect(self.show_ud_window)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.check_and_close()
        else:
            super().keyPressEvent(event)

    def check_and_close(self):
        current_file_path = self.filePathEdit.text().strip()

        if current_file_path:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Подтверждение закрытия")
            msg_box.setText(f"Вы уже выбрали файл для загрузки\n\nЧто вы хотите сделать?")

            load_button = msg_box.addButton("Загрузить в базу", QMessageBox.ButtonRole.AcceptRole)
            close_button = msg_box.addButton("Закрыть", QMessageBox.ButtonRole.DestructiveRole)
            cancel_button = msg_box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)

            msg_box.setDefaultButton(cancel_button)
            msg_box.exec()

            clicked_button = msg_box.clickedButton()

            if clicked_button == load_button:
                self.download()
                self.show_ud_window()
            elif clicked_button == close_button:
                self.show_ud_window()
        else:
            self.show_ud_window()

    def show_ud_window(self):

        from regist.upload_or_download import UDWindow
        self.ud_window = UDWindow()
        self.ud_window.show()
        self.close()

    def FIOCheck(self, text, field_name, required=True):

        if not text:
            if required:
                raise FIOException(f"Поле '{field_name}' не заполнено")
            else:
                return True

        if not text.isalpha():
            raise FIOException(f"Поле '{field_name}' должно содержать только буквы")

        if len(text) < 2:
            raise FIOException(f"Поле '{field_name}' должно быть не менее 2 символов")

    def FIOLowerCheck(self, first_name, last_name, patronymic):

        if not first_name.istitle() or not last_name.istitle() or (patronymic and not patronymic.istitle()):
            raise LowerNameError(first_name, last_name, patronymic)

    def PassportCheck(self, passport):

        if not passport:
            raise PassportError("Паспорт не заполнен")

        if not passport.isdigit():
            raise PassportError("Паспорт должен содержать только цифры")

    def PhoneCheck(self, phone):
        if len(phone) < 10:
            raise PhoneError("Номер должен быть заполнен полностью")

    def DateCheck(self, check_in_str, check_out_str):

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            today = datetime.now().date()

            if check_in > check_out:
                raise DateError("Дата заселения должна быть до даты выселения")

            if check_in < today:
                raise DateError("Дата заселения не может быть в прошлом")

        except ValueError:
            raise DateError("Неверный формат даты")

    def RoomNumberCheck(self, room_number):
        try:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM rooms WHERE room_number = ?', (room_number,))
            result = cursor.fetchone()
            conn.close()

            if not result:
                raise RoomError(f"Номер {room_number} не существует в базе данных")

        except sqlite3.Error as e:
            QMessageBox.critical(self,"Ошибка","Ошибка базы данных")

    def BookingAvailabilityCheck(self, room_number, check_in_str, check_out_str):
        try:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM rooms WHERE room_number = ?', (room_number,))
            room_result = cursor.fetchone()

            if not room_result:
                raise RoomError(f"Номер {room_number} не существует")

            room_id = room_result[0]

            cursor.execute('''
                SELECT COUNT(*) FROM bookings 
                WHERE room_id = ? 
                AND check_out_date > ? 
                AND check_in_date < ?
            ''', (room_id, check_in_str, check_out_str))

            conflicting_bookings = cursor.fetchone()[0]
            conn.close()

            if conflicting_bookings > 0:
                raise BookingError(f"Номер {room_number} занят на указанные даты")

        except sqlite3.Error as e:
            QMessageBox.critical(self,"Ошибка","Ошибка базы данных")

    def check_data(self):
        errors_data = []

        for i, row in enumerate(self.data):
            try:
                if len(row) != 8:
                    errors_data.append(
                        (i + 1, row, f"Неправильное количество колонок (ожидается 8, получено {len(row)})"))
                    continue

                first_name, last_name, patronymic, passport, phone, check_in, check_out, room_number = row

                self.FIOCheck(first_name, "Имя")
                self.FIOCheck(last_name, "Фамилия")
                self.FIOCheck(patronymic, "Отчество", required=False)
                self.FIOLowerCheck(first_name, last_name, patronymic)
                self.PassportCheck(passport)
                self.PhoneCheck(phone)
                self.DateCheck(check_in, check_out)
                self.RoomNumberCheck(room_number)
                self.BookingAvailabilityCheck(room_number, check_in, check_out)

            except Exception as e:
                errors_data.append((i + 1, row, str(e)))

        return errors_data

    def download(self):

        if not hasattr(self, 'data') or not self.data:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите файл с данными")
            return

        errors_data = self.check_data()

        if errors_data:

            dialog = DataValidationDialog(errors_data, self)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:

                cancelled_rows = dialog.get_cancelled_rows()


                rows_to_remove = []
                for i, (row_num, row_data, error) in enumerate(errors_data):
                    if i in cancelled_rows:

                        original_index = row_num - 1
                        rows_to_remove.append(original_index)


                for index in sorted(rows_to_remove, reverse=True):
                    if index < len(self.data):
                        del self.data[index]


                self.update_preview_after_correction()

                cancelled_count = len(rows_to_remove)
                remaining_count = len(self.data)

                if remaining_count > 0:
                    QMessageBox.information(self, "Готово",
                                            f"Отменено строк: {cancelled_count}\n"
                                            f"Осталось строк: {remaining_count}\n\n"
                                            f"Функция загрузки в базу будет добавлена позже.")
                else:
                    QMessageBox.information(self, "Готово", "Все строки были отменены")

            else:
                pass
        else:
            try:
                db_path = get_database_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                for i, row in enumerate(self.data):

                    if len(row) != 8:
                        errors_data.append(
                            (i + 1, row, f"Неправильное количество колонок (ожидается 8, получено {len(row)})"))
                        continue

                    first_name, last_name, patronymic, passport, phone, check_in, check_out, room_number = row
                    cursor.execute('''
                                                        INSERT INTO guests (first_name, last_name, patronymic, passport_number, phone_number)
                                                        VALUES (?, ?, ?, ?, ?)
                                                    ''', (first_name, last_name, patronymic, passport, phone))

                    guest_id = cursor.lastrowid

                    cursor.execute('SELECT id FROM rooms WHERE room_number = ?', (room_number,))
                    room_id = cursor.fetchone()[0]

                    cursor.execute('''
                                                        INSERT INTO bookings (guest_id, room_id, check_in_date, check_out_date)
                                                        VALUES (?, ?, ?, ?)
                                                    ''', (guest_id, room_id, check_in, check_out))

                conn.commit()
                conn.close()
                self.data_updated.emit()
                QMessageBox.information(self, "Успех",
                                        "Загруженные данные добавлены в базу данных")
            except Exception as e:
                QMessageBox.critical(self,"Ошибка","Ошибка загрузки данных")



    def update_preview_after_correction(self):

        self.previewTable.setRowCount(len(self.data))

        for i, row in enumerate(self.data):
            for j, elem in enumerate(row):
                self.previewTable.setItem(i, j, QTableWidgetItem(elem))


    def browse(self):

        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Загрузить файл с данными",
                "",
                "CSV Files (*.csv);; Text Files (*.txt)"
            )

            if file_path:
                self.filePathEdit.setText(file_path)
                self.preview()


        except Exception as e:
            QMessageBox.critical(self, "Ошибка выбора файла", f"Не удалось выбрать файл:\n{str(e)}")

    def load_from_txt(self, file_path):

        with open(file_path, encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';', quotechar='"')


            titel = next(reader)
            self.previewTable.setColumnCount(len(titel))
            self.previewTable.setHorizontalHeaderLabels(titel)

            self.data = list(reader)

            for i, row in enumerate(self.data):
                self.previewTable.setRowCount(
                    self.previewTable.rowCount() + 1
                )
                for j, elem in enumerate(row):
                    self.previewTable.setItem(i, j, QTableWidgetItem(elem))

    def load_from_csv(self, file_path):
        with open(file_path, encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';', quotechar='"')
            titel = next(reader)
            self.previewTable.setColumnCount(len(titel))
            self.previewTable.setHorizontalHeaderLabels(titel)

            self.data = list(reader)

            for i, row in enumerate(self.data):
                self.previewTable.setRowCount(
                    self.previewTable.rowCount() + 1
                )
                for j, elem in enumerate(row):
                    self.previewTable.setItem(i, j, QTableWidgetItem(elem))

    def preview(self):
        current_path = self.filePathEdit.text()
        try:
            if current_path.lower().endswith('.txt'):
                self.load_from_txt(current_path)
            else:
                self.load_from_csv(current_path)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()