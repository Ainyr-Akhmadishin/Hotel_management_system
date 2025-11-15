from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6 import uic
import sqlite3
from datetime import datetime
from regist.guest_registration_window import GuestRegistrationWindow
from bd_manager import YandexDiskUploader


class GuestUpdateWindow(GuestRegistrationWindow):
    closed = pyqtSignal()
    guest_updated = pyqtSignal()

    def __init__(self, parent=None, guest_data=None):
        self.guest_data = guest_data  # Данные текущего гостя
        super().__init__(parent)

        # Переопределяем настройки после вызова родительского __init__
        self.setWindowTitle("Изменение данных гостя")
        self.label.setText("Изменение данных гостя")
        self.pushButton.setText("Сохранить изменения")

        # Заполняем поля текущими данными гостя
        if guest_data:
            self.fill_guest_data()

        # Переподключаем кнопку на свою функцию
        self.pushButton.clicked.disconnect()
        self.pushButton.clicked.connect(self.update_guest)

    def fill_guest_data(self):
        """Заполнение полей текущими данными гостя"""
        try:
            if self.guest_data:
                # guest_data должен содержать: first_name, last_name, patronymic, passport, phone, room_number, check_in, check_out
                self.name.setText(self.guest_data.get('first_name', ''))
                self.fam.setText(self.guest_data.get('last_name', ''))
                self.otch.setText(self.guest_data.get('patronymic', ''))
                self.pas.setText(self.guest_data.get('passport', ''))
                self.phone.setText(self.guest_data.get('phone', ''))

                # Устанавливаем даты
                check_in = self.guest_data.get('check_in')
                if check_in:
                    if isinstance(check_in, str):
                        check_in = QDate.fromString(check_in, 'yyyy-MM-dd')
                    elif isinstance(check_in, datetime):
                        check_in = QDate(check_in.year, check_in.month, check_in.day)
                    self.dateIn.setDate(check_in)

                check_out = self.guest_data.get('check_out')
                if check_out:
                    if isinstance(check_out, str):
                        check_out = QDate.fromString(check_out, 'yyyy-MM-dd')
                    elif isinstance(check_out, datetime):
                        check_out = QDate(check_out.year, check_out.month, check_out.day)
                    self.dateOut.setDate(check_out)

                # Обновляем доступные номера и устанавливаем текущий
                self.update_available_rooms()
                current_room = self.guest_data.get('room_number')
                if current_room:
                    index = self.number.findText(str(current_room))
                    if index >= 0:
                        self.number.setCurrentIndex(index)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка заполнения данных: {str(e)}")

    def update_available_rooms(self):
        """Переопределяем метод для учета текущего бронирования"""
        try:
            check_in = self.dateIn.date().toString("yyyy-MM-dd")
            check_out = self.dateOut.date().toString("yyyy-MM-dd")

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Запрос для получения доступных номеров, включая текущий номер гостя
            cursor.execute('''
                SELECT r.room_number 
                FROM rooms r
                WHERE r.id NOT IN (
                    SELECT b.room_id 
                    FROM bookings b
                    WHERE b.check_out_date > ? AND b.check_in_date < ?
                    AND b.id != ?  -- Исключаем текущее бронирование из проверки
                )
                ORDER BY r.room_number
            ''', (check_in, check_out, self.guest_data.get('booking_id', -1)))

            available_rooms = [row[0] for row in cursor.fetchall()]
            conn.close()

            self.number.clear()
            self.number.addItems(available_rooms)

            # Восстанавливаем текущий номер, если он доступен
            current_room = self.guest_data.get('room_number')
            if current_room:
                index = self.number.findText(str(current_room))
                if index >= 0:
                    self.number.setCurrentIndex(index)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def update_guest(self):
        """Метод для обновления данных гостя вместо создания нового"""
        try:
            # Используем функции проверки из родительского класса
            self.FIOCheck(self.name, "Имя")
            self.FIOCheck(self.fam, "Фамилия")
            self.FIOCheck(self.otch, "Отчество", required=False)
            self.FIOLowerCheck(self.name, self.fam, self.otch)
            self.PassportCheck(self.pas)
            self.PhoneCheck(self.phone)
            self.DateCheck(self.dateIn, self.dateOut)

            # Получение новых данных
            first_name = self.name.text().strip()
            last_name = self.fam.text().strip()
            patronymic = self.otch.text().strip()
            passport = self.pas.text().strip()
            phone = self.phone.text().strip()
            room_number = self.number.currentText()
            in_date = self.dateIn.date().toString("yyyy-MM-dd")
            out_date = self.dateOut.date().toString("yyyy-MM-dd")

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Обновление данных гостя
            cursor.execute('''
                UPDATE guests 
                SET first_name = ?, last_name = ?, patronymic = ?, passport_number = ?, phone_number = ?
                WHERE id = ?
            ''', (first_name, last_name, patronymic, passport, phone, self.guest_data.get('guest_id')))

            # Получение ID нового номера
            cursor.execute('SELECT id FROM rooms WHERE room_number = ?', (room_number,))
            room_id = cursor.fetchone()[0]

            # Обновление бронирования
            cursor.execute('''
                UPDATE bookings 
                SET room_id = ?, check_in_date = ?, check_out_date = ?
                WHERE id = ?
            ''', (room_id, in_date, out_date, self.guest_data.get('booking_id')))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Успех",
                                    f"Данные гостя успешно обновлены\n"
                                    f"Номер: {room_number}\n"
                                    f"Период: {in_date} - {out_date}")

            self.guest_updated.emit()

            # Синхронизация с Яндекс Диском
            uploader = YandexDiskUploader("y0__xD89tSJBBjblgMg1fC9ihUwhJeqlwgXFM-EwH6GAbo1cJ6dfjDG4_HR0g")
            if uploader.upload_db():
                print("Изменения загружены на Яндекс Диск")
            else:
                print("Не удалось загрузить изменения")

            self.close()

        except Exception as e:
            # Обработка исключений из родительского класса
            from regist.regist_exceptions import LowerNameError, PassportError, FIOException, DateError, PhoneError

            if isinstance(e, LowerNameError):
                QMessageBox.critical(self, "Ошибка", str(e))
                self.name.setText(e.first_name)
                self.fam.setText(e.last_name)
                self.otch.setText(e.third_name)
            elif isinstance(e, (PassportError, FIOException, DateError, PhoneError)):
                QMessageBox.critical(self, "Ошибка", str(e))
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить данные: {str(e)}")

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()