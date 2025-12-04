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

from regist.guest_update_window import GuestUpdateWindow
from regist.upload_or_download import UDWindow
from regist.task_script import TaskWindow

from utils import get_resource_path, get_database_path
from notifications_manager import SimpleNotificationsManager

class RegistrarWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, full_name, username):
        super().__init__()
        self.showMaximized()
        self.full_name = full_name
        self.username = username
        self.current_date = datetime.now()
        self.visible_days = 14

        uic.loadUi(get_resource_path('UI/Reg/Регистратор итог.ui'), self)
        self.setWindowTitle(f"Регистратор - {self.full_name}")
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))
        self.user_id = self.get_user_id(username)

        self.notifications_manager = SimpleNotificationsManager(
            self.user_id,
            self.notifications_frame,
            self
        )

        self.guest_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self.guest_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.guest_table.customContextMenuRequested.connect(self.show_context_menu)

        self.fill_rooms()
        self.update_month_display()

        self.updating_guest_data()

        # self.check_updating_guest_data()


        self.checkout_timer = QtCore.QTimer()
        self.checkout_timer.timeout.connect(self.check_checkout_dates)
        self.checkout_timer.start(86400000)
        QtCore.QTimer.singleShot(5000, self.check_checkout_dates)

        QtCore.QTimer.singleShot(500, self.updating_guest_data)

        QtCore.QTimer.singleShot(50, self.scroll_to_current_date)

        self.last_status_count = 0
        self.setup_task_monitoring()

        # self.current_month_label.mousePressEvent = self.on_month_label_click

        self.book_button.clicked.connect(self.guest_registration)
        self.staff_button.clicked.connect(self.open_massage)

        self.prev_month_button.clicked.connect(self.previous_month)
        self.next_month_button.clicked.connect(self.next_month)

        self.Button.clicked.connect(self.updating_guest_data)
        self.data_button.clicked.connect(self.upload_or_download)

        self.search_button.clicked.connect(self.search_guest)
        self.search_input.returnPressed.connect(self.search_guest)  # Поиск по Enter

        self.exit_button.clicked.connect(self.logout)

        self.book_button.setMouseTracking(True)
        self.book_button.enterEvent = self.on_book_button_enter
        self.book_button.leaveEvent = self.on_button_leave

        self.staff_button.setMouseTracking(True)
        self.staff_button.enterEvent = self.on_staff_button_enter
        self.staff_button.leaveEvent = self.on_button_leave

        self.data_button.setMouseTracking(True)
        self.data_button.enterEvent = self.on_data_button_enter
        self.data_button.leaveEvent = self.on_button_leave

    def on_book_button_enter(self, event):
        if not self.statusBar().isVisible():
            self.statusBar().show()
        self.statusBar().showMessage("Нажмите для регистрации нового гостя")
        super(QtWidgets.QPushButton, self.book_button).enterEvent(event)

    def on_staff_button_enter(self, event):
        if not self.statusBar().isVisible():
            self.statusBar().show()
        self.statusBar().showMessage("Нажмите для отправки сообщения персоналу")
        super(QtWidgets.QPushButton, self.staff_button).enterEvent(event)

    def on_data_button_enter(self, event):
        if not self.statusBar().isVisible():
            self.statusBar().show()
        self.statusBar().showMessage("Нажмите для загрузки или сохранения данных о бронировании номеров")
        super(QtWidgets.QPushButton, self.data_button).enterEvent(event)

    def on_button_leave(self, event):
        self.statusBar().clearMessage()
        self.statusBar().hide()
        super().leaveEvent(event)

    def logout(self):

        reply = QMessageBox.question(
            self,
            "Подтверждение выхода",
            "Вы уверены, что хотите выйти из аккаунта?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.closed.emit()
            self.close()

    def closeEvent(self, event):

        event.accept()

    def setup_task_monitoring(self):
        self.task_check_timer = QtCore.QTimer()
        self.task_check_timer.timeout.connect(self.check_task_updates)
        self.task_check_timer.start(15000)


    def check_task_updates(self):

        try:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()


            cursor.execute('''
                SELECT GROUP_CONCAT(room_number || ':' || status, '|') 
                FROM maintenance_tasks 
                WHERE status IN ('в работе', 'в ожидании уборки', 'убрано')
                ORDER BY room_number
            ''')

            current_status_hash = cursor.fetchone()[0] or ""
            conn.close()


            if not hasattr(self, 'last_status_hash') or current_status_hash != self.last_status_hash:
                self.last_status_hash = current_status_hash
                self.update_status_column()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка")

    def closeEvent(self, event):
        if hasattr(self, 'task_check_timer'):
            self.task_check_timer.stop()
        if hasattr(self, 'notifications_manager'):
            self.notifications_manager.stop_updates()
        super().closeEvent(event)


    def scroll_to_current_date(self):
        try:
            today = datetime.now()
            target_day = today.day + 8

            _, days_in_month = monthrange(today.year, today.month)

            if target_day > days_in_month:
                target_day = days_in_month



            if today.year == self.current_date.year and today.month == self.current_date.month:

                for column in range(1, self.guest_table.columnCount()):
                    header = self.guest_table.horizontalHeaderItem(column)
                    if header:
                        header_text = header.text()
                        try:
                            day = int(header_text.split()[0])
                            if day == target_day:
                                self.guest_table.horizontalScrollBar().setValue(column)

                                if self.guest_table.rowCount() > 0:
                                    self.guest_table.setCurrentCell(0, column)


                                self.guest_table.verticalScrollBar().setValue(0)
                                break
                        except (ValueError, IndexError):
                            continue
                else:
                    pass
            else:
                pass

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка прокрутки к текущей дате")


    def search_guest(self):
        try:
            search_text = self.search_input.text().strip()
            if not search_text:
                QMessageBox.information(self, "Поиск", "Введите фамилию для поиска")
                return

            found_cells = []

            for row in range(self.guest_table.rowCount()):
                for column in range(1, self.guest_table.columnCount()):  # Пропускаем столбец статусов
                    item = self.guest_table.item(row, column)
                    if item and item.text():
                        if search_text.lower() in item.text().lower():
                            found_cells.append((row, column, item.text()))

            if found_cells:
                row, column, guest_name = found_cells[0]

                self.scroll_to_cell(row, column)

                self.highlight_found_cell(row, column)

                QMessageBox.information(
                    self,
                    "Найден",
                    f"Гость: {guest_name}"
                )

            else:
                QMessageBox.information(
                    self,
                    "Не найдено",
                    f"Гость с фамилией '{search_text}' не найден"
                )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка прокрутки к текущей дате: {e}")

    def scroll_to_cell(self, row, column):
        try:
            self.guest_table.horizontalScrollBar().setValue(column)

            self.guest_table.verticalScrollBar().setValue(row)

            self.guest_table.setCurrentCell(row, column)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка прокрутки к текущей дате: {e}")



    def highlight_found_cell(self, row, column):
        try:
            item = self.guest_table.item(row, column)
            if item:
                original_color = item.background()

                item.setBackground(QBrush(QColor("#FFD700")))

                QtCore.QTimer.singleShot(3000, lambda: item.setBackground(original_color))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка")

    def check_checkout_dates(self):
        try:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            today = datetime.now().strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT DISTINCT r.room_number
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                WHERE b.check_out_date = ?
            ''', (today,))

            today_checkouts = cursor.fetchall()
            created_tasks_count = 0

            for room_data in today_checkouts:
                room_number = room_data[0]

                cursor.execute('''
                    SELECT id FROM maintenance_tasks 
                    WHERE room_number = ? 
                    AND status IN ('в работе', 'в ожидании уборки')
                ''', (room_number,))

                existing_task = cursor.fetchone()

                if not existing_task:
                    try:
                        cleaning_task = TaskWindow(room_number, self.user_id)
                        cleaning_task.create_task(self.user_id)
                        created_tasks_count += 1
                    except Exception as e:
                        QMessageBox.critical(self, "Ошибка", f"Ошибка создания задания на уборку: {e}")
            conn.close()

            if created_tasks_count > 0:
                self.update_status_column()


        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка проверки дат выселения: {e}")

    def get_status_display_name(self, status):
        status_names = {
            'в работе': "⚡ В работе",
            'в ожидании уборки': "⏳ Ожидание уборки",
            'убрано': "✨ Убрано"
        }
        return status_names.get(status, f"📋 {status}")

    def apply_status_text_style(self, item, status):
        text_colors = {
            'в работе': '#2196F3',
            'в ожидании уборки': '#FF9800',
            'убрано': '#9C27B0'
        }

        color = text_colors.get(status, '#000000')

        item.setForeground(QBrush(QColor(color)))

        font = item.font()
        font.setBold(True)
        item.setFont(font)

    def update_status_column(self):
        try:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for row in range(self.guest_table.rowCount()):
                status_item = QTableWidgetItem("✨ Убрано")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.apply_status_text_style(status_item, "убрано")
                self.guest_table.setItem(row, 0, status_item)

            cursor.execute('''
                SELECT DISTINCT room_number, status 
                FROM maintenance_tasks 
                WHERE status != 'выполнена' 
                AND status != 'убрано'
                ORDER BY room_number
            ''')

            active_tasks = cursor.fetchall()

            for room_number, status in active_tasks:
                row = self.find_room_row(room_number)
                if row != -1:
                    status_display = self.get_status_display_name(status)
                    status_item = QTableWidgetItem(status_display)
                    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.apply_status_text_style(status_item, status)
                    self.guest_table.setItem(row, 0, status_item)

            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления статусов")

    def find_room_row(self, room_number):
        for row in range(self.guest_table.rowCount()):
            header_item = self.guest_table.verticalHeaderItem(row)
            if header_item and header_item.text() == str(room_number):
                return row
        return -1

    def upload_or_download(self):

        self.udwindow = UDWindow(on_data_updated=self.updating_guest_data)
        self.udwindow.show()

    def get_user_id(self, username):
        try:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM staff WHERE login = ?', (username,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 1
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка")
            return 1

    def closeEvent(self, event):
        if hasattr(self, 'notifications_manager'):
            self.notifications_manager.stop_updates()
        super().closeEvent(event)

    def get_guest_data(self, row, column):
        try:
            room_number = self.guest_table.verticalHeaderItem(row).text()
            guest_name = self.guest_table.item(row, column).text()

            header = self.guest_table.horizontalHeaderItem(column)
            date_info = header.text() if header else "неизвестная дата"

            try:
                day = int(date_info.split()[0])
                current_date = datetime(self.current_date.year, self.current_date.month, day)
                current_date_str = current_date.strftime('%Y-%m-%d')
            except:
                current_date_str = self.current_date.strftime('%Y-%m-%d')


            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

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
            QMessageBox.critical(self, "Ошибка", f"Ошибка получения данных о госте")
            return None

    def edit_guest(self, row, column):
        try:
            guest_data = self.get_guest_data(row, column)
            if guest_data:
                self.update_window = GuestUpdateWindow(self, guest_data)
                self.update_window.guest_updated.connect(self.updating_guest_data)
                self.update_window.show()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить данные гостя для редактирования")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно редактирования")

    def show_context_menu(self, position):
        index = self.guest_table.indexAt(position)

        if index.isValid():
            row = index.row()
            column = index.column()

            if column > 0:
                item = self.guest_table.item(row, column)

                if item and item.text().strip():

                    context_menu = QMenu(self)

                    task_action = QAction("🧹 Отправить номер на уброку", self)
                    edit_action = QAction("✏️ Изменить данные", self)
                    delete_action = QAction("🗑️ Удалить бронь", self)
                    info_action = QAction("ℹ️ Информация", self)

                    edit_action.triggered.connect(lambda: self.edit_guest(row, column))
                    delete_action.triggered.connect(lambda: self.delete_booking(row, column))
                    info_action.triggered.connect(lambda: self.show_guest_info(row, column))
                    task_action.triggered.connect(lambda: self.show_task_window(row))

                    context_menu.addAction(edit_action)
                    context_menu.addAction(delete_action)
                    context_menu.addAction(task_action)
                    context_menu.addSeparator()
                    context_menu.addAction(info_action)

                    context_menu.exec(self.guest_table.viewport().mapToGlobal(position))

    def show_task_window(self,row):
        try:
            self.room_number = self.guest_table.verticalHeaderItem(row).text()
            self.task_window = TaskWindow(self.room_number, self.user_id)
            self.task_window.task_created.connect(self.update_status_column)
            self.task_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка")


    def show_guest_info(self, row, column):
        try:
            room_number = self.guest_table.verticalHeaderItem(row).text()
            guest_name = self.guest_table.item(row, column).text()

            header = self.guest_table.horizontalHeaderItem(column)
            date_info = header.text() if header else "неизвестная дата"

            try:
                day = int(date_info.split()[0])
                current_date = datetime(self.current_date.year, self.current_date.month, day)
                current_date_str = current_date.strftime('%Y-%m-%d')
            except:
                current_date_str = self.current_date.strftime('%Y-%m-%d')

            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

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

                check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
                check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
                nights = (check_out - check_in).days

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
        try:
            room_number = self.guest_table.verticalHeaderItem(row).text()
            guest_name = self.guest_table.item(row, column).text()

            header = self.guest_table.horizontalHeaderItem(column)
            date_info = header.text() if header else "неизвестная дата"

            try:
                day = int(date_info.split()[0])
                current_date = datetime(self.current_date.year, self.current_date.month, day)
                current_date_str = current_date.strftime('%Y-%m-%d')
            except:
                current_date_str = self.current_date.strftime('%Y-%m-%d')

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
                db_path = get_database_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

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

                    cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
                    conn.commit()
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Бронь успешно удалена!\n\n"
                        f"Комната: {room_number}\n"
                        f"Постоялец: {guest_name}"
                    )
                    cleaning_after_delete = TaskWindow(room_number, self.user_id)
                    cleaning_after_delete.create_task(self.user_id)
                    self.update_status_column()

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
        self.guest_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # self.guest_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)

        self.guest_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        self.guest_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.guest_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)

        self.guest_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def clear_table_data(self):
        for row in range(self.guest_table.rowCount()):
            for column in range(1, self.guest_table.columnCount()):
                self.guest_table.setItem(row, column, None)

    def updating_guest_data(self):
        try:
            self.clear_table_data()
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
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
            today = datetime.now().date()

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

                first_day_set = False
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


                                if check_out_date < today:

                                    color = "#B0B0B0"
                                    status = "прошла"
                                elif check_in_date <= today <= check_out_date:

                                    color = "#74E868"
                                    status = "сейчас"
                                else:

                                    color = "#68B5E8"
                                    status = "будет"

                                item.setBackground(QBrush(QColor(color)))
                                if not first_day_set and header_date == check_in_date:
                                    first_day_set = True
                                    item.setForeground(QBrush(QColor("#000000")))
                                else:
                                    item.setForeground(QBrush(QColor(color)))

                                self.guest_table.setItem(row, column, item)

                        except (ValueError, IndexError):
                            continue

            conn.close()
            self.update_status_column()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))





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
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
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

        self.guest_table.setHorizontalHeaderItem(0, QTableWidgetItem("Статус"))

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
            QMessageBox.critical(self, "Ошибка", f"Ошибка прокрутки к текущей дате")
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



