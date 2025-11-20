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
from regist.task_script import TaskWindow

from utils import get_resource_path
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

        # Таймер для автоматической проверки выселений раз в 24 часа
        self.checkout_timer = QtCore.QTimer()
        self.checkout_timer.timeout.connect(self.check_checkout_dates)
        self.checkout_timer.start(86400000)
        QtCore.QTimer.singleShot(5000, self.check_checkout_dates)

        QtCore.QTimer.singleShot(500, self.updating_guest_data)

        QtCore.QTimer.singleShot(50, self.scroll_to_current_date)


        self.current_month_label.mousePressEvent = self.on_month_label_click

        self.book_button.clicked.connect(self.guest_registration)
        self.staff_button.clicked.connect(self.open_massage)

        self.prev_month_button.clicked.connect(self.previous_month)
        self.next_month_button.clicked.connect(self.next_month)

        self.Button.clicked.connect(self.updating_guest_data)
        self.data_button.clicked.connect(self.upload_or_download)

        self.search_button.clicked.connect(self.search_guest)
        self.search_input.returnPressed.connect(self.search_guest)  # Поиск по Enter

    def scroll_to_current_date(self):
        """Прокручивает таблицу к текущей дате + 8 дней или к последнему дню месяца"""
        try:
            today = datetime.now()
            target_day = today.day + 8

            # Получаем количество дней в текущем месяце
            _, days_in_month = monthrange(today.year, today.month)

            # Если целевой день превышает количество дней в месяце, берем последний день
            if target_day > days_in_month:
                target_day = days_in_month

            print(f"🎯 Целевой день для прокрутки: {target_day} (текущий: {today.day} + 8 дней)")

            # Если текущий месяц отображается в таблице
            if today.year == self.current_date.year and today.month == self.current_date.month:
                # Ищем колонку с целевой датой
                for column in range(1, self.guest_table.columnCount()):
                    header = self.guest_table.horizontalHeaderItem(column)
                    if header:
                        header_text = header.text()
                        try:
                            # Извлекаем день из заголовка
                            day = int(header_text.split()[0])
                            if day == target_day:
                                # Прокручиваем к этой колонке
                                self.guest_table.horizontalScrollBar().setValue(column)

                                # Выделяем ячейку для визуального акцента
                                if self.guest_table.rowCount() > 0:
                                    self.guest_table.setCurrentCell(0, column)

                                # Прокручиваем вертикально к верху
                                self.guest_table.verticalScrollBar().setValue(0)

                                print(f"✅ Прокрутка к дате: {target_day}.{today.month}.{today.year} (колонка {column})")
                                break
                        except (ValueError, IndexError):
                            continue
                else:
                    print(f"⚠️ Целевой день {target_day} не найден в таблице")
            else:
                print("ℹ️ Текущая дата не в отображаемом месяце")

        except Exception as e:
            print(f"❌ Ошибка прокрутки к текущей дате: {e}")


    def search_guest(self):
        """Поиск гостя по фамилии и прокрутка к нему"""
        try:
            search_text = self.search_input.text().strip()
            if not search_text:
                QMessageBox.information(self, "Поиск", "Введите фамилию для поиска")
                return

            # Ищем гостя в таблице
            found_cells = []

            for row in range(self.guest_table.rowCount()):
                for column in range(1, self.guest_table.columnCount()):  # Пропускаем столбец статусов
                    item = self.guest_table.item(row, column)
                    if item and item.text():
                        # Проверяем содержит ли текст фамилию (игнорируем регистр)
                        if search_text.lower() in item.text().lower():
                            found_cells.append((row, column, item.text()))

            if found_cells:
                # Берем первую найденную ячейку
                row, column, guest_name = found_cells[0]

                # Прокручиваем таблицу к найденной ячейке (слева)
                self.scroll_to_cell(row, column)

                # Подсвечиваем найденную ячейку
                self.highlight_found_cell(row, column)

                # Простое сообщение о найденном госте
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
            QMessageBox.critical(self, "Ошибка поиска", f"Не удалось выполнить поиск: {str(e)}")

    def scroll_to_cell(self, row, column):
        """Прокручивает таблицу так, чтобы найденная ячейка была слева"""
        try:
            # Устанавливаем скроллбар так, чтобы колонка была первой видимой
            self.guest_table.horizontalScrollBar().setValue(column)

            # Прокручиваем вертикально к строке
            self.guest_table.verticalScrollBar().setValue(row)

            # Выделяем найденную ячейку
            self.guest_table.setCurrentCell(row, column)

        except Exception as e:
            print(f"Ошибка прокрутки: {e}")



    def highlight_found_cell(self, row, column):
        """Временно подсвечивает найденную ячейку"""
        try:
            item = self.guest_table.item(row, column)
            if item:
                # Сохраняем оригинальный цвет
                original_color = item.background()

                # Устанавливаем желтый цвет для выделения
                item.setBackground(QBrush(QColor("#FFD700")))

                # Через 3 секунды возвращаем оригинальный цвет
                QtCore.QTimer.singleShot(3000, lambda: item.setBackground(original_color))

        except Exception as e:
            print(f"Ошибка подсветки: {e}")

    def check_checkout_dates(self):
        """Проверяет даты выселения и создает задания на уборку"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Сегодняшняя дата
            today = datetime.now().strftime('%Y-%m-%d')

            # Находим бронирования, где сегодня дата выселения
            cursor.execute('''
                SELECT DISTINCT r.room_number
                FROM bookings b
                JOIN rooms r ON b.room_id = r.id
                LEFT JOIN maintenance_tasks mt ON r.room_number = mt.room_number 
                    AND DATE(mt.created_at) = ?
                    AND mt.description LIKE '%выезда%'
                WHERE b.check_out_date = ?
                AND mt.id IS NULL
            ''', (today, today))

            today_checkouts = cursor.fetchall()

            for room_data in today_checkouts:
                room_number = room_data[0]
                # СОЗДАЕМ ЗАДАНИЕ НА УБОРКУ ПРЯМО ЗДЕСЬ
                try:
                    cleaning_task = TaskWindow(room_number, self.user_id)
                    cleaning_task.create_task(self.user_id)
                    print(f"✅ Создано задание на уборку комнаты {room_number} после выселения")
                except Exception as e:
                    print(f"❌ Ошибка создания задания для комнаты {room_number}: {e}")

            conn.close()

            if today_checkouts:
                print(f"✅ Создано {len(today_checkouts)} заданий на уборку для выселений сегодня")
                self.update_status_column()
            else:
                print("ℹ️ На сегодня нет выселений для создания заданий")

        except Exception as e:
            print(f"❌ Ошибка проверки дат выселения: {e}")

    def get_status_display_name(self, status):
        """Возвращает красивое отображаемое имя для статуса"""
        status_names = {
            'в работе': "⚡ В работе",
            'в ожидании уборки': "⏳ Ожидание уборки",
            'убрано': "✨ Убрано"
        }
        return status_names.get(status, f"📋 {status}")

    def apply_status_text_style(self, item, status):
        """Применяет цвет только к тексту статуса"""
        # Цвета текста для разных статусов
        text_colors = {
            'в работе': '#2196F3',  # Синий текст
            'в ожидании уборки': '#FF9800',  # Оранжевый текст
            'убрано': '#9C27B0'  # Фиолетовый текст
        }

        color = text_colors.get(status, '#000000')  # По умолчанию черный

        # Применяем цвет только к тексту
        item.setForeground(QBrush(QColor(color)))

        # Делаем текст жирным
        font = item.font()
        font.setBold(True)
        item.setFont(font)

    def update_status_column(self):
        """Обновление столбца 'Статус' для всех комнат"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Сначала устанавливаем всем комнатам статус "убрано"
            for row in range(self.guest_table.rowCount()):
                status_item = QTableWidgetItem("✨ Убрано")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.apply_status_text_style(status_item, "убрано")
                self.guest_table.setItem(row, 0, status_item)

            # Теперь получаем актуальные статусы из базы данных
            cursor.execute('''
                SELECT DISTINCT room_number, status 
                FROM maintenance_tasks 
                WHERE status != 'выполнена' 
                AND status != 'убрано'
                ORDER BY room_number
            ''')

            active_tasks = cursor.fetchall()

            # Обновляем статусы для комнат с активными заданиями
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
            print(f"Ошибка обновления столбца статусов: {e}")

    def find_room_row(self, room_number):
        """Найти строку таблицы по номеру комнаты"""
        for row in range(self.guest_table.rowCount()):
            header_item = self.guest_table.verticalHeaderItem(row)
            if header_item and header_item.text() == str(room_number):
                return row
        return -1

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
                    task_action = QAction("🧹 Отправить на уброку", self)
                    edit_action = QAction("✏️ Изменить данные", self)
                    delete_action = QAction("🗑️ Удалить бронь", self)
                    info_action = QAction("ℹ️ Информация", self)

                    # Подключаем все функции
                    edit_action.triggered.connect(lambda: self.edit_guest(row, column))
                    delete_action.triggered.connect(lambda: self.delete_booking(row, column))
                    info_action.triggered.connect(lambda: self.show_guest_info(row, column))
                    task_action.triggered.connect(lambda: self.show_task_window(row))

                    # Добавляем действия в меню
                    context_menu.addAction(edit_action)
                    context_menu.addAction(delete_action)
                    context_menu.addAction(task_action)
                    context_menu.addSeparator()  # Разделитель
                    context_menu.addAction(info_action)

                    # Показываем меню в позиции клика
                    context_menu.exec(self.guest_table.viewport().mapToGlobal(position))

    def show_task_window(self,row):
        try:
            self.room_number = self.guest_table.verticalHeaderItem(row).text()
            self.task_window = TaskWindow(self.room_number, self.user_id)
            self.task_window.task_created.connect(self.update_status_column)
            self.task_window.show()
        except Exception as e:
            print(str(e))


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
                    cleaning_after_delete = TaskWindow(room_number, self.user_id)
                    cleaning_after_delete.create_task(self.user_id)
                    self.update_status_column()
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

                first_day_set = False  # Флаг для отслеживания первой ячейки
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

                                # Делаем текст видимым только в первой ячейке заезда
                                if not first_day_set and header_date == check_in_date:
                                    # Первая ячейка - видимый текст
                                    first_day_set = True
                                else:
                                    # Остальные ячейки - невидимый текст (но данные есть!)
                                    item.setForeground(QBrush(QColor("#74E868")))  # Тот же цвет что и фон

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



