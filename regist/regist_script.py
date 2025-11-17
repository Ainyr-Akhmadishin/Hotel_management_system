import sqlite3
from calendar import monthrange
from datetime import datetime, timedelta

from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QDialog, QVBoxLayout, QMessageBox, QMenu
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6 import uic, QtCore, QtWidgets
from PyQt6.QtWidgets import QCalendarWidget
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QBrush, QColor, QAction

from regist.guest_registration_window import GuestRegistrationWindow
from massage_window import MassageWindow

from regist.guest_update_window import GuestUpdateWindow  # Добавьте эту строку в импорты
from regist.upload_or_download import UDWindow

from utils import get_resource_path
from notifications_manager import SimpleNotificationsManager

class RegistrarWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, full_name, username):
        super().__init__()
        self.full_name = full_name
        self.username = username
        self.current_date = datetime.now()
        self.visible_days = 14

        uic.loadUi(get_resource_path('UI/Reg/Регистратор итог.ui'), self)
        self.setWindowTitle(f"Регистратор - {self.full_name}")

        self.user_id = self.get_user_id(username)

        # Инициализируем менеджер уведомлений
        self.notifications_manager = SimpleNotificationsManager(
            self.user_id,
            self.notifications_frame,
            self  # передаем ссылку на главное окно
        )

        self.guest_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.guest_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.guest_table.customContextMenuRequested.connect(self.show_context_menu)

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
        self.data_button.clicked.connect(self.upload_or_download)

    def upload_or_download(self):

        self.udwindow = UDWindow(on_data_updated=self.updating_guest_data)
        self.udwindow.show()

    def get_user_id(self, username):
        """Получение ID пользователя по логину"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM staff WHERE login = ?', (username,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 1
        except Exception as e:
            print(f"Ошибка получения ID пользователя: {e}")
            return 1

    def closeEvent(self, event):
        """Останавливаем обновления уведомлений при закрытии"""
        if hasattr(self, 'notifications_manager'):
            self.notifications_manager.stop_updates()
        super().closeEvent(event)

    def get_guest_data(self, row, column):
        """Получение данных гостя для редактирования"""
        try:
            room_number = self.guest_table.verticalHeaderItem(row).text()
            guest_name = self.guest_table.item(row, column).text()

            # Получаем дату из заголовка колонки
            header = self.guest_table.horizontalHeaderItem(column)
            date_info = header.text() if header else "неизвестная дата"

            # Извлекаем день из даты в заголовке
            try:
                day = int(date_info.split()[0])
                current_date = datetime(self.current_date.year, self.current_date.month, day)
                current_date_str = current_date.strftime('%Y-%m-%d')
            except:
                current_date_str = self.current_date.strftime('%Y-%m-%d')

            # Подключаемся к базе данных для получения полной информации
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем полные данные о бронировании
            cursor.execute('''
                SELECT 
                    guests.id as guest_id,
                    guests.first_name,
                    guests.last_name,
                    guests.patronymic,
                    guests.phone_number,
                    guests.passport_number,
                    bookings.check_in_date,
                    bookings.check_out_date,
                    rooms.room_number,
                    bookings.id as booking_id
                FROM bookings 
                JOIN guests ON bookings.guest_id = guests.id
                JOIN rooms ON bookings.room_id = rooms.id
                WHERE rooms.room_number = ? 
                AND bookings.check_in_date <= ?
                AND bookings.check_out_date >= ?
            ''', (room_number, current_date_str, current_date_str))

            booking_info = cursor.fetchone()
            conn.close()

            if booking_info:
                (guest_id, first_name, last_name, patronymic, phone,
                 passport, check_in_date, check_out_date,
                 room_number, booking_id) = booking_info

                return {
                    'guest_id': guest_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'patronymic': patronymic,
                    'passport': passport,
                    'phone': phone,
                    'room_number': room_number,
                    'check_in': check_in_date,
                    'check_out': check_out_date,
                    'booking_id': booking_id
                }
            else:
                return None

        except Exception as e:
            print(f"Ошибка получения данных гостя: {e}")
            return None

    def edit_guest(self, row, column):
        """Функция для изменения данных постояльца"""
        try:
            # Получаем данные гостя
            guest_data = self.get_guest_data(row, column)
            if guest_data:
                # Открываем окно редактирования
                self.update_window = GuestUpdateWindow(self, guest_data)
                self.update_window.guest_updated.connect(self.updating_guest_data)
                self.update_window.show()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить данные гостя для редактирования")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно редактирования: {str(e)}")

    def show_context_menu(self, position):
        """Показать контекстное меню при клике на ячейку с постояльцем"""
        # Получаем индекс ячейки, по которой кликнули
        index = self.guest_table.indexAt(position)

        if index.isValid():
            row = index.row()
            column = index.column()

            # Проверяем, что кликнули на ячейку с данными (не на заголовок)
            if column > 0:  # Пропускаем колонку с номерами комнат
                item = self.guest_table.item(row, column)

                # Если в ячейке есть текст (постоялец)
                if item and item.text().strip():
                    # Создаем контекстное меню
                    context_menu = QMenu(self)

                    # Добавляем действия
                    edit_action = QAction("✏️ Изменить данные", self)
                    delete_action = QAction("🗑️ Удалить бронь", self)
                    info_action = QAction("ℹ️ Информация", self)

                    # Подключаем все функции
                    edit_action.triggered.connect(lambda: self.edit_guest(row, column))
                    delete_action.triggered.connect(lambda: self.delete_booking(row, column))
                    info_action.triggered.connect(lambda: self.show_guest_info(row, column))

                    # Добавляем действия в меню
                    context_menu.addAction(edit_action)
                    context_menu.addAction(delete_action)
                    context_menu.addSeparator()  # Разделитель
                    context_menu.addAction(info_action)

                    # Показываем меню в позиции клика
                    context_menu.exec(self.guest_table.viewport().mapToGlobal(position))

    def show_guest_info(self, row, column):
        """Функция для показа информации о постояльце"""
        try:
            room_number = self.guest_table.verticalHeaderItem(row).text()
            guest_name = self.guest_table.item(row, column).text()

            # Получаем дату из заголовка колонки
            header = self.guest_table.horizontalHeaderItem(column)
            date_info = header.text() if header else "неизвестная дата"

            # Извлекаем день из даты в заголовке
            try:
                day = int(date_info.split()[0])
                current_date = datetime(self.current_date.year, self.current_date.month, day)
                current_date_str = current_date.strftime('%Y-%m-%d')
            except:
                current_date_str = self.current_date.strftime('%Y-%m-%d')

            # Подключаемся к базе данных для получения подробной информации
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Запрос для получения информации о бронировании
            cursor.execute('''
                SELECT 
                    guests.first_name,
                    guests.last_name,
                    guests.patronymic,
                    guests.phone_number,
                    guests.passport_number,
                    bookings.check_in_date,
                    bookings.check_out_date,
                    rooms.room_number,
                    bookings.id
                FROM bookings 
                JOIN guests ON bookings.guest_id = guests.id
                JOIN rooms ON bookings.room_id = rooms.id
                WHERE rooms.room_number = ? 
                AND bookings.check_in_date <= ?
                AND bookings.check_out_date >= ?
            ''', (room_number, current_date_str, current_date_str))

            booking_info = cursor.fetchone()
            conn.close()

            if booking_info:
                (first_name, last_name, patronymic, phone,
                 passport_data, check_in_date, check_out_date,
                 room_number, booking_id) = booking_info

                # Рассчитываем количество ночей
                check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
                check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
                nights = (check_out - check_in).days

                # Формируем сообщение с информацией
                info_message = (
                    f"📋 Информация о бронировании\n\n"
                    f"👤 Гость:\n"
                    f"   ФИО: {last_name} {first_name} {patronymic or ''}\n"
                    f"   Телефон: {phone}\n"
                    f"   Паспорт: {passport_data}\n\n"
                    f"🏨 Номер:\n"
                    f"   Номер: {room_number}\n\n"
                    f"📅 Даты проживания:\n"
                    f"   Заезд: {check_in_date}\n"
                    f"   Выезд: {check_out_date}\n"
                    f"   Ночей: {nights}\n\n"
                    f"📊 ID бронирования: {booking_id}"
                )
            else:
                info_message = (
                    f"Информация о бронировании:\n\n"
                    f"Комната: {room_number}\n"
                    f"Постоялец в таблице: {guest_name}\n"
                    f"Дата просмотра: {date_info}\n\n"
                    f"❌ Бронь не найдена в базе данных для указанной даты."
                )

            QMessageBox.information(self, "Информация о постояльце", info_message)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить информацию: {str(e)}")

    def delete_booking(self, row, column):
        """Функция для удаления бронирования"""
        try:
            room_number = self.guest_table.verticalHeaderItem(row).text()
            guest_name = self.guest_table.item(row, column).text()

            # Получаем дату из заголовка колонки
            header = self.guest_table.horizontalHeaderItem(column)
            date_info = header.text() if header else "неизвестная дата"

            # Извлекаем день из даты в заголовке
            try:
                day = int(date_info.split()[0])
                current_date = datetime(self.current_date.year, self.current_date.month, day)
                current_date_str = current_date.strftime('%Y-%m-%d')
            except:
                current_date_str = self.current_date.strftime('%Y-%m-%d')

            # Подтверждение удаления
            reply = QMessageBox.question(
                self,
                "Удаление брони",
                f"Вы уверены, что хотите удалить бронь?\n\n"
                f"Комната: {room_number}\n"
                f"Постоялец: {guest_name}\n"
                f"Дата: {date_info}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Подключаемся к базе данных для удаления
                conn = sqlite3.connect('Hotel_bd.db')
                cursor = conn.cursor()

                # ИСПРАВЛЕННЫЙ ЗАПРОС - ищем бронирование по номеру комнаты и дате
                cursor.execute('''
                    SELECT bookings.id 
                    FROM bookings 
                    JOIN guests ON bookings.guest_id = guests.id
                    JOIN rooms ON bookings.room_id = rooms.id
                    WHERE rooms.room_number = ? 
                    AND bookings.check_in_date <= ?
                    AND bookings.check_out_date >= ?
                ''', (room_number, current_date_str, current_date_str))

                booking_id_result = cursor.fetchone()

                if booking_id_result:
                    booking_id = booking_id_result[0]

                    # Удаляем бронирование
                    cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
                    conn.commit()

                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Бронь успешно удалена!\n\n"
                        f"Комната: {room_number}\n"
                        f"Постоялец: {guest_name}"
                    )

                    # Обновляем таблицу
                    self.updating_guest_data()
                else:
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        "Бронь не найдена в базе данных для указанной даты"
                    )

                conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить бронь: {str(e)}")

    def setup_table_readonly(self):
        """Настройка таблицы как доступной только для чтения"""
        # Запрещаем редактирование таблицы
        self.guest_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # # Запрещаем выделение ячеек (опционально)
        # self.guest_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)

        # Или если хотите разрешить выделение, но без редактирования:
        self.guest_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        # Запрещаем изменение размера ячеек
        self.guest_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.guest_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)

        # Устанавливаем фокус политику - запрещаем фокусировку на ячейках
        self.guest_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
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

                row = -1
                for i in range(self.guest_table.rowCount()):
                    header_item = self.guest_table.verticalHeaderItem(i)
                    if header_item and header_item.text() == room_number:
                        row = i
                        break

                if row == -1:
                    continue


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


                                item.setBackground(QBrush(QColor("#74E868")))

                                # if(check_in_date == header_date):
                                #     self.guest_table.setItem(row, column, item)
                                # else:
                                #     self.guest_table.setItem(row, column, " ")

                                self.guest_table.setItem(row, column, item)

                        except (ValueError, IndexError):
                            continue

            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            # import traceback
            # traceback.print_exc()





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
        self.massage_window = MassageWindow(full_name=self.full_name)
        self.massage_window.show()

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



        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка загрузки данных о постояльцах", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            # import traceback
            # traceback.print_exc()

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
            day_name = self.get_day_name(date.weekday())
            header_text = f"{date.day} {day_name}"
            header_item = QTableWidgetItem(header_text)
            header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.guest_table.setHorizontalHeaderItem(col, header_item)

    def get_day_name(self, weekday):
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



