import sqlite3
from calendar import monthrange
from datetime import datetime, timedelta

from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QDialog, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6 import uic, QtCore
from PyQt6.QtWidgets import QCalendarWidget
from PyQt6.QtCore import QDate

from regist.guest_registration_window import GuestRegistrationWindow
from regist.massage_window import MassageWindow

class RegistrarWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, full_name, username):
        super().__init__()
        self.full_name = full_name
        self.username = username
        self.current_date = datetime.now()
        self.visible_days = 14

        uic.loadUi('UI/Reg/Регистратор итог.ui', self)
        self.setWindowTitle(f"Регистратор - {self.full_name}")


        self.fill_rooms()
        self.update_month_display()

        self.updating_guest_data()

        # self.check_updating_guest_data()

        QtCore.QTimer.singleShot(100, self.updating_guest_data)

        self.current_month_label.mousePressEvent = self.on_month_label_click

        self.book_button.clicked.connect(self.guest_registration)
        self.staff_button.clicked.connect(self.open_massage)

        self.prev_month_button.clicked.connect(self.previous_month)
        self.next_month_button.clicked.connect(self.next_month)

        self.Button.clicked.connect(self.updating_guest_data)

    # def start_auto_refresh(self):
    #     self.refresh_timer = QtCore.QTimer()
    #     self.refresh_timer.timeout.connect(self.check_updating_guest_data)
    #     self.refresh_timer.start(2000)
    #
    #     self.check_updating_guest_data()
    #
    # def check_updating_guest_data(self):
    #     conn = sqlite3.connect('Hotel_bd.db')
    #     cursor = conn.cursor()
    #
    #     cursor.execute('''
    #                     SELECT COUNT(*)
    #                     FROM bookings
    #                 ''', )
    #     current_count = cursor.fetchone()[0]
    #
    #     if not hasattr(self, 'previous_guest_count'):
    #         self.previous_guest_count = current_count
    #         self.updating_guest_data()
    #         return
    #
    #     if current_count != self.previous_guest_count:
    #         self.previous_guest_count = current_count
    #         self.updating_guest_data()
    #
    #     conn.close()


    def clear_table_data(self):
        for row in range(self.guest_table.rowCount()):
            for column in range(1, self.guest_table.columnCount()):
                self.guest_table.setItem(row, column, None)

    def updating_guest_data(self):
        try:
            self.clear_table_data()
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            first_day_of_month = self.current_date.replace(day=1).strftime('%Y-%m-%d')
            last_day_of_month = (self.current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(
                days=1)
            last_day_of_month_str = last_day_of_month.strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT rooms.room_number, 
                       last_name || ' ' || SUBSTR(first_name, 1, 1) || '. ' || SUBSTR(patronymic, 1, 1) || '.' as guest_name, 
                       check_in_date, 
                       check_out_date 
                FROM bookings 
                JOIN guests ON bookings.guest_id = guests.id
                JOIN rooms ON bookings.room_id = rooms.id
                WHERE check_in_date <= ? AND check_out_date >= ?
            ''', (last_day_of_month_str, first_day_of_month))

            guests = cursor.fetchall()
            guest_set = False
            for guest in guests:
                room_number = guest[0]
                guest_name = guest[1]
                check_in_date = datetime.strptime(guest[2], '%Y-%m-%d').date()
                check_out_date = datetime.strptime(guest[3], '%Y-%m-%d').date()

                # Находим строку по номеру комнаты
                row = -1
                for i in range(self.guest_table.rowCount()):
                    header_item = self.guest_table.verticalHeaderItem(i)
                    if header_item and header_item.text() == room_number:
                        row = i
                        break

                if row == -1:
                    continue


                # Заполняем ячейки для периода бронирования
                for column in range(1, self.guest_table.columnCount()):
                    header = self.guest_table.horizontalHeaderItem(column)
                    if header:
                        header_text = header.text()
                        try:
                            day = int(header_text.split()[0])
                            header_date = datetime(self.current_date.year, self.current_date.month, day).date()

                            if check_in_date <= header_date <= check_out_date:

                                item = QTableWidgetItem(guest_name)
                                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                                from PyQt6.QtGui import QBrush
                                item.setBackground(QBrush(Qt.GlobalColor.green))

                                # if(check_in_date == header_date):
                                #     self.guest_table.setItem(row, column, item)
                                # else:
                                #     self.guest_table.setItem(row, column, " ")

                                self.guest_table.setItem(row, column, item)

                        except (ValueError, IndexError):
                            continue

            conn.close()

        except Exception as e:
            print(f"Ошибка в updating_guest_data: {e}")
            import traceback
            traceback.print_exc()





    def on_month_label_click(self, event):
        self.show_month_picker()

    def show_month_picker(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор месяца")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        calendar = QCalendarWidget()
        calendar.setSelectedDate(QDate(self.current_date.year, self.current_date.month, 1))
        calendar.setGridVisible(True)
        calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        calendar.setNavigationBarVisible(True)

        calendar.clicked.connect(lambda date: self.on_date_selected(date, dialog))

        layout.addWidget(calendar)

        dialog.exec()

    def on_date_selected(self, date, dialog):
        selected_date = date.toPyDate()
        self.current_date = datetime(selected_date.year, selected_date.month, 1)
        self.update_month_display()
        dialog.close()

    def guest_registration(self):
        self.guest_window = GuestRegistrationWindow(self)
        self.guest_window.guest_registered.connect(self.updating_guest_data)
        self.guest_window.show()

    def open_massage(self):
        self.massage_window = MassageWindow(self)
        self.massage_window.exec()

    def fill_rooms(self):
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('SELECT room_number FROM rooms ORDER BY room_number')
            rooms = cursor.fetchall()

            self.guest_table.setRowCount(0)
            self.guest_table.setRowCount(len(rooms))


            for row, room_data in enumerate(rooms):
                room_number = str(room_data[0])

                item = QTableWidgetItem(room_number)
                self.guest_table.setVerticalHeaderItem(row, item)

            conn.close()


        except Exception as e:
            print(f"Ошибка при заполнении комнат: {e}")
            import traceback
            traceback.print_exc()

    def get_month_dates(self):
        year = self.current_date.year
        month = self.current_date.month

        _, num_days = monthrange(year, month)

        dates = []
        for day in range(1, num_days + 1):
            date = datetime(year, month, day)
            dates.append(date)

        return dates

    def update_headers(self):
        dates = self.get_month_dates()

        self.guest_table.setColumnCount(len(dates) + 1)

        self.guest_table.setHorizontalHeaderItem(0, QTableWidgetItem("Номер"))

        for col, date in enumerate(dates, 1):
            day_name = self.get_russian_day_name(date.weekday())
            header_text = f"{date.day} {day_name}"
            header_item = QTableWidgetItem(header_text)
            header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.guest_table.setHorizontalHeaderItem(col, header_item)

    def get_russian_day_name(self, weekday):
        days = {
            0: "Пн",
            1: "Вт",
            2: "Ср",
            3: "Чт",
            4: "Пт",
            5: "Сб",
            6: "Вс"
        }
        return days.get(weekday, "")

    def update_month_display(self):
        try:
            if not hasattr(self, 'current_month_label'):
                print("Ошибка: current_month_label не найден")
                return

            month_names = {
                1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
                5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
                9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
            }

            month_name = month_names.get(self.current_date.month, "")
            year = self.current_date.year
            self.current_month_label.setText(f"{month_name} {year}")

            self.update_headers()

        except Exception as e:
            print(f"Ошибка в update_month_display: {e}")
            import traceback
            traceback.print_exc()

    def previous_month(self):
        first_day = self.current_date.replace(day=1)
        previous_month = first_day - timedelta(days=1)
        self.current_date = previous_month.replace(day=1)
        self.update_month_display()
        self.updating_guest_data()

    def next_month(self):
        year = self.current_date.year
        month = self.current_date.month

        if month == 12:
            next_date = datetime(year + 1, 1, 1)
        else:
            next_date = datetime(year, month + 1, 1)

        self.current_date = next_date
        self.update_month_display()
        self.updating_guest_data()



