from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6 import uic
import sqlite3
from datetime import datetime
from regist.regist_exceptions import FIOException, LowerNameError, PassportError, DateError, PhoneError


class GuestRegistrationWindow(QMainWindow):
    closed = pyqtSignal()
    guest_registered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        uic.loadUi('UI/Reg/Окно заселения гостя итог.ui', self)
        self.setWindowTitle("Заселение гостя")
        self.phone.setInputMask("+7(000)000-00-00")

        self.setup_star_handlers()

        self.dateIn.setDate(QDate.currentDate())
        self.update_available_rooms()
        self.dateIn.dateChanged.connect(self.update_available_rooms)

        self.dateOut.setDate(QDate.currentDate().addDays(1))
        self.update_available_rooms()
        self.dateOut.dateChanged.connect(self.update_available_rooms)


        self.pushButton.clicked.connect(self.register_guest)
        self.setup_enter_handlers()

    def setup_enter_handlers(self):
        try:
            # Только для текстовых полей
            self.name.returnPressed.connect(lambda: self.fam.setFocus())
            self.fam.returnPressed.connect(lambda: self.otch.setFocus())
            self.otch.returnPressed.connect(lambda: self.pas.setFocus())
            self.pas.returnPressed.connect(lambda: self.phone.setFocus())
            self.phone.returnPressed.connect(lambda: self.dateIn.setFocus())

        except Exception as e:
            print(f"Ошибка в setup_enter_handlers: {e}")


    def setup_star_handlers(self):

        try:
            self.name.textChanged.connect(lambda: self.removeStar(self.label_2,self.name.text()))
            self.fam.textChanged.connect(lambda: self.removeStar(self.label_3,self.fam.text()))
            self.pas.textChanged.connect(lambda: self.removeStar(self.label_5,self.pas.text()))
            self.phone.textChanged.connect(lambda: self.removeStar(self.label_8,self.phone.text()))
            self.number.currentTextChanged.connect(lambda: self.removeStar(self.label_9,self.number.currentText()))
            self.dateIn.dateChanged.connect(lambda: self.removeStar(self.label_6,self.dateIn.date()))
            self.dateOut.dateChanged.connect(lambda: self.removeStar(self.label_7,self.dateOut.date()))

            # self.name.textChanged.connect(lambda: self.name.setStyleSheet(""))
            # self.fam.textChanged.connect(lambda: self.fam.setStyleSheet(""))
            # self.otch.textChanged.connect(lambda: self.otch.setStyleSheet(""))
            # self.pas.textChanged.connect(lambda: self.pas.setStyleSheet(""))
            # self.phone.textChanged.connect(lambda: self.phone.setStyleSheet(""))

        except Exception as e:
            print(f"Ошибка в setup_star_handlers: {e}")

    def removeStar(self, label, filled):
        base_text = label.text()

        if filled:
            label.setText(base_text.replace(' *', ''))
        else:
            label.setText(f"{base_text} *")

    # def load_rooms_to_combobox(self):
    #
    #     try:
    #         # Подключаемся к базе данных
    #         conn = sqlite3.connect('Hotel_bd.db')
    #         cursor = conn.cursor()
    #
    #         # Получаем все номера из таблицы rooms
    #         cursor.execute('SELECT room_number FROM rooms ORDER BY room_number')
    #         rooms = cursor.fetchall()
    #
    #         # Очищаем комбобокс перед добавлением
    #         if hasattr(self, 'comboBox'):
    #             self.comboBox.clear()
    #
    #             # Добавляем номера в комбобокс
    #             for room in rooms:
    #                 self.comboBox.addItem(room[0])  # room[0] - это room_number
    #
    #             print(f"✅ Загружено номеров в комбобокс: {len(rooms)}")
    #
    #         conn.close()
    #
    #     except Exception as e:
    #         print(f"❌ Ошибка загрузки номеров из БД: {e}")


    # def add_test_rooms(self):
    #     """Добавляет тестовые номера если БД недоступна"""
    #     test_rooms = ["101", "102", "103", "104", "105",
    #                   "201", "202", "203", "204",
    #                   "301", "302", "303", "304"]
    #
    #     if hasattr(self, 'comboBox'):
    #         self.comboBox.clear()
    #         for room in test_rooms:
    #             self.comboBox.addItem(room)
    #         print("✅ Добавлены тестовые номера")

    def update_available_rooms(self):
        try:
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

            available_rooms = [row[0] for row in cursor.fetchall()]
            conn.close()
            self.number.clear()
            self.number.addItems(available_rooms)

        except Exception as e:
            print(f"Ошибка: {e}")

    def FIOCheck(self,field,field_name,required = True):

        text = field.text().strip()
        field.setStyleSheet("")

        if not text:
            if required:
                field.setStyleSheet("border: 2px solid red !important; background-color: #FFE6E6 !important;")
                raise FIOException(f"Поле '{field_name}' не заполнено")
            else:
                return True

        if not text.isalpha() :
            field.setStyleSheet("border: 2px solid red !important; background-color: #FFE6E6 !important;")
            raise FIOException(f"Поле '{field_name}' должно содержать только буквы")

        if len(text) < 2:
            field.setStyleSheet("border: 2px solid red !important; background-color: #FFE6E6 !important;")
            raise FIOException(f"Поле '{field_name}' должно быть не менее 2 символов")

        # Если данные введены с маленькой буквы, то вызывается ошибка, в которой они преобразовывваются в заглавные буквы
        # if not field.istitle() or not field.istitle():
        #     raise LowerNameError(first_name, last_name)



    def FIOLowerCheck(self,field_name,field_fam,field_otchestvo):

        text_name = field_name.text().strip()
        text_fam = field_fam.text().strip()
        text_otch = field_otchestvo.text().strip()


        if not text_name.istitle() or not text_fam.istitle() or not text_otch.istitle() and text_otch != "":
            raise LowerNameError(text_name,text_fam,text_otch)

    def PassportCheck(self,field_pas):
        text_pas = field_pas.text().strip()

        if not text_pas:
            field_pas.setStyleSheet("border: 2px solid red !important; background-color: #FFE6E6 !important;")
            raise PassportError("Паспорт не заполнен")

        if not text_pas.isdigit():
            field_pas.setStyleSheet("border: 2px solid red !important; background-color: #FFE6E6 !important;")
            raise PassportError("Паспорт должен содержать только цифры")


    def PhoneCheck(self, field_phone):
        text_phone = field_phone.text().strip()

        if len(text_phone) < 16:
            field_phone.setStyleSheet("border: 2px solid red !important; background-color: #FFE6E6 !important;")
            raise PhoneError("Номер должен быть заполнен полностью")



    def DateCheck(self,field_dateIn,field_dateOut):
        date_in = field_dateIn.date()
        date_out = field_dateOut.date()

        field_dateIn.setStyleSheet("")
        field_dateOut.setStyleSheet("")

        if date_in>date_out:
            field_dateIn.setStyleSheet("border: 2px solid red !important; background-color: #FFE6E6 !important;")
            raise DateError("Дата заселения должна быть до даты выселения")

        if date_in < QDate.currentDate():
            field_dateIn.setStyleSheet("border: 2px solid red !important; background-color: #FFE6E6 !important;")
            raise DateError("Дата заселения не может быть в прошлом")

    def register_guest(self):

        try:

            self.FIOCheck(self.name, "Имя")
            self.FIOCheck(self.fam, "Фамилия")
            self.FIOCheck(self.otch, "Отчество",required=False)

            self.FIOLowerCheck(self.name, self.fam, self.otch)

            self.PassportCheck(self.pas)

            self.PhoneCheck(self.phone)

            self.DateCheck(self.dateIn,self.dateOut)


            first_name = self.name.text().strip()
            last_name = self.fam.text().strip()
            otchestvo = self.otch.text().strip()
            passport = self.pas.text().strip()
            phone = self.phone.text().strip()
            guest_number = self.number.currentText()
            in_date = self.dateIn.date().toString("yyyy-MM-dd")
            out_date = self.dateOut.date().toString("yyyy-MM-dd")

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                        INSERT INTO guests (first_name, last_name, patronymic, passport_number, phone_number)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (first_name, last_name, otchestvo, passport, phone))

            guest_id = cursor.lastrowid


            cursor.execute('SELECT id FROM rooms WHERE room_number = ?', (guest_number,))
            room_id = cursor.fetchone()[0]


            cursor.execute('''
                        INSERT INTO bookings (guest_id, room_id, check_in_date, check_out_date)
                        VALUES (?, ?, ?, ?)
                    ''', (guest_id, room_id, in_date, out_date))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Успех",
                                    f"Гость успешно заселен\n"
                                    f"Номер: {guest_number}\n"
                                    f"Период: {in_date} - {out_date}")

            self.guest_registered.emit()

            self.close()


        except LowerNameError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.name.setText(e.first_name)
            self.fam.setText(e.last_name)
            self.otch.setText(e.third_name)

        except (PassportError,FIOException,DateError,PhoneError) as e:
            QMessageBox.critical(self, "Ошибка", str(e))





    def closeEvent(self, event):
        self.closed.emit()
        event.accept()