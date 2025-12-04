from PyQt6.QtWidgets import QDialog, QMessageBox, QMainWindow
from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6 import uic
import sqlite3
import os
from regist.regist_exceptions import FIOException, LowerNameError, PassportError, DateError, PhoneError


class CorrectionDialog(QMainWindow):
    correction_finished = pyqtSignal(list, int)

    def __init__(self, row_data, row_number, parent=None):
        super().__init__(parent)
        self.row_data = row_data
        self.row_number = row_number
        self.corrected_data = None

        try:
            ui_path = 'UI/Reg/Окно заселения гостя итог.ui'
            if not os.path.exists(ui_path):
                ui_path = '../UI/Reg/Окно заселения гостя итог.ui'

            uic.loadUi(ui_path, self)

            self.setWindowTitle(f"Исправление данных - Строка {row_number}")
            self.pushButton.setText("Сохранить исправления")
            self.label.setText(f"Исправление строки {row_number}")

            self.phone.setInputMask("+7(000)000-00-00")

            self.populate_fields()

            self.setup_star_handlers()
            self.setup_enter_handlers()

            self.remove_initial_stars()

            self.pushButton.clicked.connect(self.validate_and_save)

            self.update_available_rooms()

            self.dateIn.dateChanged.connect(self.update_available_rooms)
            self.dateOut.dateChanged.connect(self.update_available_rooms)

            self.setMinimumWidth(400)
            self.setMinimumHeight(550)

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось загрузить окно исправления")
            raise

    def remove_initial_stars(self):
        try:
            self.removeStar(self.label_2, self.name.text())
            self.removeStar(self.label_3, self.fam.text())
            self.removeStar(self.label_5, self.pas.text())
            self.removeStar(self.label_8, self.phone.text())
            self.removeStar(self.label_9, self.number.currentText())

            self.removeStar(self.label_6, self.dateIn.date().toString("yyyy-MM-dd"))
            self.removeStar(self.label_7, self.dateOut.date().toString("yyyy-MM-dd"))

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка")
    def setup_enter_handlers(self):
        try:
            self.name.returnPressed.connect(lambda: self.fam.setFocus())
            self.fam.returnPressed.connect(lambda: self.otch.setFocus())
            self.otch.returnPressed.connect(lambda: self.pas.setFocus())
            self.pas.returnPressed.connect(lambda: self.phone.setFocus())
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка")

    def setup_star_handlers(self):
        try:
            self.name.textChanged.connect(lambda: self.removeStar(self.label_2, self.name.text()))
            self.fam.textChanged.connect(lambda: self.removeStar(self.label_3, self.fam.text()))
            self.pas.textChanged.connect(lambda: self.removeStar(self.label_5, self.pas.text()))
            self.phone.textChanged.connect(lambda: self.removeStar(self.label_8, self.phone.text()))
            self.number.currentTextChanged.connect(lambda: self.removeStar(self.label_9, self.number.currentText()))

            self.dateIn.dateChanged.connect(
                lambda: self.removeStar(self.label_6, self.dateIn.date().toString("yyyy-MM-dd")))
            self.dateOut.dateChanged.connect(
                lambda: self.removeStar(self.label_7, self.dateOut.date().toString("yyyy-MM-dd")))

            self.remove_initial_stars()

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка")

    def removeStar(self, label, filled):
        try:
            if not hasattr(label, 'text'):
                return

            current_text = label.text()
            base_text = current_text.replace(' *', '')

            if filled and ' *' in current_text:
                label.setText(base_text)

            elif not filled and ' *' not in current_text:
                label.setText(f"{base_text} *")

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка")

    def populate_fields(self):
        try:
            if len(self.row_data) >= 8:
                self.name.setText(str(self.row_data[0]) if self.row_data[0] else "")
                self.fam.setText(str(self.row_data[1]) if self.row_data[1] else "")
                self.otch.setText(str(self.row_data[2]) if self.row_data[2] else "")
                self.pas.setText(str(self.row_data[3]) if self.row_data[3] else "")

                phone_text = str(self.row_data[4]) if self.row_data[4] else ""
                if phone_text and not phone_text.startswith('+7('):
                    digits = ''.join(filter(str.isdigit, phone_text))
                    if len(digits) >= 10:
                        phone_text = f"+7({digits[-10:-7]}){digits[-7:-4]}-{digits[-4:-2]}-{digits[-2:]}"
                self.phone.setText(phone_text)

                try:
                    check_in_str = str(self.row_data[5]) if self.row_data[5] else QDate.currentDate().toString(
                        "yyyy-MM-dd")
                    check_in = QDate.fromString(check_in_str, 'yyyy-MM-dd')
                    if check_in.isValid():
                        self.dateIn.setDate(check_in)
                    else:
                        self.dateIn.setDate(QDate.currentDate())
                except:
                    self.dateIn.setDate(QDate.currentDate())

                try:
                    check_out_str = str(self.row_data[6]) if self.row_data[6] else QDate.currentDate().addDays(
                        1).toString("yyyy-MM-dd")
                    check_out = QDate.fromString(check_out_str, 'yyyy-MM-dd')
                    if check_out.isValid():
                        self.dateOut.setDate(check_out)
                    else:
                        self.dateOut.setDate(QDate.currentDate().addDays(1))
                except:
                    self.dateOut.setDate(QDate.currentDate().addDays(1))

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка")

    def update_available_rooms(self):
        try:
            if not hasattr(self, 'dateIn') or not hasattr(self, 'dateOut') or not hasattr(self, 'number'):
                return

            check_in = self.dateIn.date().toString("yyyy-MM-dd")
            check_out = self.dateOut.date().toString("yyyy-MM-dd")

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT r.room_number 
                FROM rooms r
                WHERE r.id NOT IN (
                    SELECT b.room_id 
                    FROM bookings b
                    WHERE b.check_out_date > ? AND b.check_in_date < ?
                )
                ORDER BY r.room_number
            ''', (check_in, check_out))

            available_rooms = [str(row[0]) for row in cursor.fetchall()]
            conn.close()

            current_room = self.number.currentText()
            self.number.clear()
            self.number.addItems(available_rooms)

            room_set = False

            if len(self.row_data) >= 8 and self.row_data[7]:
                original_room = str(self.row_data[7])
                if original_room in available_rooms:
                    self.number.setCurrentText(original_room)
                    room_set = True

            if not room_set and current_room and current_room in available_rooms:
                self.number.setCurrentText(current_room)
                room_set = True

            if not room_set and available_rooms:
                self.number.setCurrentText(available_rooms[0])


        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка обновления доступных номеров")

    def FIOCheck(self, field, field_name, required=True):
        text = field.text().strip()
        field.setStyleSheet("")

        if not text:
            if required:
                field.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
                raise FIOException(f"Поле '{field_name}' не заполнено")
            else:
                return True

        if not text.isalpha():
            field.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise FIOException(f"Поле '{field_name}' должно содержать только буквы")

        if len(text) < 2:
            field.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise FIOException(f"Поле '{field_name}' должно быть не менее 2 символов")

    def FIOLowerCheck(self, field_name, field_fam, field_otchestvo):
        text_name = field_name.text().strip()
        text_fam = field_fam.text().strip()
        text_otch = field_otchestvo.text().strip()

        if not text_name.istitle() or not text_fam.istitle() or (text_otch and not text_otch.istitle()):
            raise LowerNameError(text_name, text_fam, text_otch)

    def PassportCheck(self, field_pas):
        text_pas = field_pas.text().strip()

        if not text_pas:
            field_pas.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise PassportError("Паспорт не заполнен")

        if not text_pas.isdigit():
            field_pas.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise PassportError("Паспорт должен содержать только цифры")

    def PhoneCheck(self, field_phone):
        text_phone = field_phone.text().strip()

        if len(text_phone) < 16:
            field_phone.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise PhoneError("Номер должен быть заполнен полностью")

    def DateCheck(self, field_dateIn, field_dateOut):
        date_in = field_dateIn.date()
        date_out = field_dateOut.date()

        field_dateIn.setStyleSheet("")
        field_dateOut.setStyleSheet("")

        if date_in > date_out:
            field_dateIn.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            field_dateOut.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise DateError("Дата заселения должна быть до даты выселения")

        if date_in < QDate.currentDate():
            field_dateIn.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise DateError("Дата заселения не может быть в прошлом")

    def validate_and_save(self):
        try:
            self.FIOCheck(self.name, "Имя")
            self.FIOCheck(self.fam, "Фамилия")
            self.FIOCheck(self.otch, "Отчество", required=False)
            self.FIOLowerCheck(self.name, self.fam, self.otch)
            self.PassportCheck(self.pas)
            self.PhoneCheck(self.phone)
            self.DateCheck(self.dateIn, self.dateOut)

            if not self.number.currentText():
                self.number.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
                raise Exception("Необходимо выбрать номер")

            self.corrected_data = [
                self.name.text().strip(),
                self.fam.text().strip(),
                self.otch.text().strip(),
                self.pas.text().strip(),
                self.phone.text().strip(),
                self.dateIn.date().toString("yyyy-MM-dd"),
                self.dateOut.date().toString("yyyy-MM-dd"),
                self.number.currentText()
            ]

            self.correction_finished.emit(self.corrected_data, self.row_number)
            self.close()

        except LowerNameError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.name.setText(e.first_name)
            self.fam.setText(e.last_name)
            self.otch.setText(e.third_name)

        except (PassportError, FIOException, DateError, PhoneError, Exception) as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def get_corrected_data(self):
        return self.corrected_data