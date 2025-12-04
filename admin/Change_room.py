from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox, QDialog, QInputDialog
from PyQt6.QtCore import QDate
import sqlite3
from datetime import datetime
from utils import get_resource_path, get_database_path


class EmptyFieldError(Exception):
    pass  # Исключение для пустых полей ввода


class InvalidRoomNumberError(Exception):
    pass  # Исключение для невалидного номера комнаты


class InvalidPriceError(Exception):
    pass  # Исключение для невалидной цены


class DatabaseConnectionError(Exception):
    pass  # Исключение для ошибок подключения к базе данных


class DatabaseQueryError(Exception):
    pass  # Исключение для ошибок выполнения запросов к БД


class RoomExistsError(Exception):
    pass  # Исключение когда номер уже существует


class RoomManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            uic.loadUi(get_resource_path('UI/Admin/Изменение номеров переделанная.ui'), self)

            self.setWindowTitle("Управление номерами")
            self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))

            # Инициализация БД
            db_path = get_database_path()
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()

            # Подключаем кнопки и элементы
            self.lineEdit.textChanged.connect(self.search_rooms)
            self.comboBox.currentTextChanged.connect(self.sort_rooms)
            self.verticalScrollBar.valueChanged.connect(self.scroll_rooms)

            # Подключаем кнопки добавления и удаления
            self.add_nomer.clicked.connect(self.add_room)
            self.fire_selected_btn.clicked.connect(self.delete_selected_room)

            # Список кнопок номеров
            self.room_buttons = [
                self.pushButton_2, self.pushButton_5, self.pushButton_6,
                self.pushButton_15, self.pushButton_13, self.pushButton_11,
                self.pushButton_8
            ]

            # Список меток статуса
            self.status_labels = [
                self.label_4, self.label_5, self.label_6, self.label_7,
                self.label_8, self.label_9, self.label_10
            ]

            # Подключаем обработчики для кнопок номеров
            for button in self.room_buttons:
                button.clicked.connect(self.create_room_button_handler(button))

            # Текущий выбранный номер
            self.selected_room_number = None

            # Переменные для управления данными
            self.all_rooms = []
            self.filtered_rooms = []
            self.current_start_index = 0

            # Загружаем данные номеров
            self.load_rooms()

            # Обновляем состояние кнопки удаления
            self.update_delete_button_state()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка инициализации: {str(e)}")
            self.close()

    def create_room_button_handler(self, button):
        """Создает обработчик для кнопки номера"""

        def handler():
            room_number = button.property("room_number")
            if room_number:
                self.selected_room_number = room_number
                self.update_delete_button_state()
                self.edit_room(room_number)

        return handler

    def update_delete_button_state(self):
        """Обновляет состояние кнопки удаления"""
        if self.selected_room_number:
            self.fire_selected_btn.setEnabled(True)
            self.fire_selected_btn.setToolTip(f"Удалить номер {self.selected_room_number}")
        else:
            self.fire_selected_btn.setEnabled(False)
            self.fire_selected_btn.setToolTip("Выберите номер для удаления")

    def load_rooms(self):
        """Загрузка номеров из БД"""
        try:
            # Сначала получим все комнаты с ценой
            self.cursor.execute("SELECT id, room_number, room_type, price_per_night FROM rooms ORDER BY room_number")
            all_rooms_data = self.cursor.fetchall()

            # Теперь для каждой комнаты проверим занятость
            self.all_rooms = []
            current_date = datetime.now().strftime('%Y-%m-%d')

            for room_id, room_number, room_type, price in all_rooms_data:
                # Проверяем есть ли активное бронирование на сегодня
                self.cursor.execute("""
                    SELECT COUNT(*) FROM bookings 
                    WHERE room_id = ? 
                    AND ? BETWEEN check_in_date AND check_out_date
                """, (room_id, current_date))

                is_occupied = self.cursor.fetchone()[0] > 0
                status = '+' if is_occupied else '-'

                self.all_rooms.append((room_id, room_number, status, room_type, price))

            self.filtered_rooms = self.all_rooms.copy()

            # Настраиваем прокрутку
            self.setup_scrollbar()

            # Отображаем комнаты
            self.display_rooms()

            # Сбрасываем выбранный номер
            self.selected_room_number = None
            self.update_delete_button_state()

        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Ошибка загрузки номеров: {str(e)}")

    def setup_scrollbar(self):
        """Настройка прокрутки"""
        try:
            total_rooms = len(self.filtered_rooms)
            visible_rooms = len(self.room_buttons)

            if total_rooms > visible_rooms:
                self.verticalScrollBar.setMaximum(total_rooms - visible_rooms)
                self.verticalScrollBar.setVisible(True)
            else:
                self.verticalScrollBar.setMaximum(0)
                self.verticalScrollBar.setVisible(False)
        except Exception as e:
            raise DatabaseQueryError(f"Ошибка настройки прокрутки: {str(e)}")

    def display_rooms(self):
        """Отображение номеров в интерфейсе"""
        try:
            # Очищаем кнопки и метки
            for button in self.room_buttons:
                button.setVisible(False)
                button.setText("")
                button.setProperty("room_number", "")
            for label in self.status_labels:
                label.setVisible(False)
                label.setText("")

            # Определяем диапазон отображаемых комнат
            end_index = min(self.current_start_index + len(self.room_buttons), len(self.filtered_rooms))
            rooms_to_display = self.filtered_rooms[self.current_start_index:end_index]

            # Заполняем данными
            for i, (room_id, room_number, status, room_type, price) in enumerate(rooms_to_display):
                if i >= len(self.room_buttons):
                    break

                # Устанавливаем номер с типом и ценой
                display_text = f"{room_number}\n({room_type})\n{price} руб."
                self.room_buttons[i].setText(display_text)
                self.room_buttons[i].setProperty("room_number", room_number)
                self.room_buttons[i].setVisible(True)

                # Выделяем выбранный номер
                if room_number == self.selected_room_number:
                    self.room_buttons[i].setStyleSheet(
                        "background-color: #e3f2fd; color: #1976d2; "
                        "border: 2px solid #1976d2; text-align: center; padding: 8px 12px; font-size: 10px;"
                    )
                else:
                    self.room_buttons[i].setStyleSheet(
                        "background-color: white; color: #2c3e50; "
                        "border: 1px solid #e1e5eb; text-align: center; padding: 8px 12px; font-size: 10px;"
                    )

                # Устанавливаем статус
                self.status_labels[i].setText(status)
                self.status_labels[i].setVisible(True)

                # Настраиваем цвет статуса
                if status == '+':
                    self.status_labels[i].setStyleSheet(
                        "font-size: 14px; font-weight: bold; color: #27ae60; text-align: center; "
                        "background-color: #e8f8ef; padding: 6px 10px; border-radius: 4px;"
                    )
                else:
                    self.status_labels[i].setStyleSheet(
                        "font-size: 14px; font-weight: bold; color: #e74c3c; text-align: center; "
                        "background-color: #ffeaea; padding: 6px 10px; border-radius: 4px;"
                    )
        except Exception as e:
            raise DatabaseQueryError(f"Ошибка отображения номеров: {str(e)}")

    def scroll_rooms(self, value):
        """Прокрутка списка номеров"""
        try:
            self.current_start_index = value
            self.display_rooms()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка прокрутки: {str(e)}")

    def search_rooms(self):
        """Поиск номеров"""
        try:
            search_text = self.lineEdit.text().strip()

            if not search_text:
                self.filtered_rooms = self.all_rooms.copy()
            else:
                self.filtered_rooms = []
                for room_id, room_number, status, room_type, price in self.all_rooms:
                    if (search_text.lower() in room_number.lower() or
                            search_text.lower() in room_type.lower() or
                            search_text in str(price)):
                        self.filtered_rooms.append((room_id, room_number, status, room_type, price))

            # Сбрасываем прокрутку
            self.current_start_index = 0
            self.verticalScrollBar.setValue(0)

            # Настраиваем прокрутку заново
            self.setup_scrollbar()
            self.display_rooms()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {str(e)}")

    def sort_rooms(self):
        """Сортировка номеров"""
        try:
            sort_option = self.comboBox.currentText()

            if not self.filtered_rooms:
                return

            # Используем текущий отфильтрованный список для сортировки
            rooms_to_sort = self.filtered_rooms.copy()

            if sort_option == "Сортировать по \"+\"":
                sorted_rooms = sorted(rooms_to_sort, key=lambda x: (x[2] != '+', x[1]))
            elif sort_option == "Сортировать по \"-\"":
                sorted_rooms = sorted(rooms_to_sort, key=lambda x: (x[2] != '-', x[1]))
            else:
                sorted_rooms = sorted(rooms_to_sort, key=lambda x: x[1])

            self.filtered_rooms = sorted_rooms

            # Сбрасываем прокрутку
            self.current_start_index = 0
            self.verticalScrollBar.setValue(0)

            # Настраиваем прокрутку заново
            self.setup_scrollbar()
            self.display_rooms()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сортировки: {str(e)}")

    def validate_room_number(self, room_number):
        """Проверка номера комнаты"""
        if not room_number:
            raise EmptyFieldError("Номер комнаты не может быть пустым")
        if not room_number.isdigit():
            raise InvalidRoomNumberError("Номер комнаты должен содержать только цифры")
        if len(room_number) < 1:
            raise InvalidRoomNumberError("Номер комнаты слишком короткий")
        return True

    def validate_price(self, price):
        """Проверка цены"""
        if not price:
            raise EmptyFieldError("Цена не может быть пустой")
        try:
            price_float = float(price)
            if price_float <= 0:
                raise InvalidPriceError("Цена должна быть больше 0")
            if price_float > 1000000:
                raise InvalidPriceError("Цена слишком большая")
            return price_float
        except ValueError:
            raise InvalidPriceError("Цена должна быть числом")

    def add_room(self):
        """Добавление нового номера"""
        try:
            # Запрашиваем номер комнаты
            room_number, ok = QInputDialog.getText(
                self,
                "Добавление номера",
                "Введите номер комнаты (только цифры):"
            )

            if not ok or not room_number.strip():
                return

            # Проверяем, не пустое ли поле
            if not room_number.strip():
                raise EmptyFieldError("Номер комнаты не может быть пустым")

            # Проверяем, содержит ли номер только цифры
            if not room_number.strip().isdigit():
                raise InvalidRoomNumberError("Номер комнаты должен содержать только цифры")

            # Проверяем, существует ли уже такой номер
            self.cursor.execute("SELECT id FROM rooms WHERE room_number = ?", (room_number.strip(),))
            if self.cursor.fetchone():
                raise RoomExistsError("Номер с таким названием уже существует!")

            # Запрашиваем тип комнаты
            room_types = ['стандарт', 'люкс', 'полулюкс', 'семейный']
            room_type, ok = QInputDialog.getItem(
                self,
                "Выбор типа номера",
                "Выберите тип номера:",
                room_types,
                0,  # индекс по умолчанию (стандарт)
                False  # не редактируемый
            )

            if not ok:
                return  # Пользователь отменил

            # Запрашиваем цену за ночь
            price, ok = QInputDialog.getText(
                self,
                "Цена за ночь",
                "Введите цену за ночь (руб.):",
                text="3000"  # значение по умолчанию
            )

            if not ok or not price.strip():
                return

            # Проверяем цену
            try:
                price_validated = self.validate_price(price.strip())
            except (EmptyFieldError, InvalidPriceError) as e:
                QMessageBox.warning(self, "Ошибка цены", str(e))
                return

            # Добавляем номер в БД
            self.cursor.execute(
                "INSERT INTO rooms (room_number, room_type, price_per_night) VALUES (?, ?, ?)",
                (room_number.strip(), room_type, price_validated)
            )

            self.conn.commit()

            QMessageBox.information(self, "Успех",
                                    f"Номер {room_number.strip()} ({room_type}) успешно добавлен!\n"
                                    f"Цена: {price_validated} руб./ночь")
            self.load_rooms()  # Перезагружаем данные

        except EmptyFieldError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except InvalidRoomNumberError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except RoomExistsError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка базы данных: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления номера: {str(e)}")

    def delete_selected_room(self):
        """Удаление выбранного номера"""
        try:
            if not self.selected_room_number:
                QMessageBox.warning(self, "Предупреждение", "Сначала выберите номер для удаления!")
                return

            # Получаем ID комнаты, тип и цену
            self.cursor.execute("SELECT id, room_type, price_per_night FROM rooms WHERE room_number = ?",
                                (self.selected_room_number,))
            room_data = self.cursor.fetchone()

            if not room_data:
                QMessageBox.warning(self, "Ошибка", "Выбранный номер не найден в базе данных!")
                return

            room_id, room_type, price = room_data

            # Проверяем, есть ли активные бронирования для этой комнаты
            current_date = datetime.now().strftime('%Y-%m-%d')
            self.cursor.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE room_id = ? 
                AND ? BETWEEN check_in_date AND check_out_date
            """, (room_id, current_date))

            active_bookings = self.cursor.fetchone()[0]

            if active_bookings > 0:
                QMessageBox.warning(self, "Ошибка",
                                    f"Нельзя удалить номер {self.selected_room_number}, так как в нем есть активные бронирования!")
                return

            # Запрашиваем подтверждение
            reply = QMessageBox.question(
                self, "Подтверждение удаления",
                f"Вы уверены, что хотите удалить номер {self.selected_room_number}?\n"
                f"Тип: {room_type}\n"
                f"Цена: {price} руб./ночь\n\n"
                f"ВНИМАНИЕ: Все связанные бронирования также будут удалены!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Удаляем все связанные бронирования
                self.cursor.execute("DELETE FROM bookings WHERE room_id = ?", (room_id,))

                # Удаляем комнату
                self.cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))

                self.conn.commit()

                QMessageBox.information(self, "Успех", f"Номер {self.selected_room_number} успешно удален!")

                # Сбрасываем выбранный номер
                self.selected_room_number = None
                self.update_delete_button_state()

                # Перезагружаем данные
                self.load_rooms()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка базы данных: {str(e)}")
            self.conn.rollback()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления номера: {str(e)}")

    def edit_room(self, room_number):
        """Редактирование номера"""
        try:
            # Получаем текущий номер, тип и цену
            current_room = room_number

            # Получаем текущую информацию о номере
            self.cursor.execute("SELECT room_type, price_per_night FROM rooms WHERE room_number = ?", (current_room,))
            room_info = self.cursor.fetchone()

            if not room_info:
                QMessageBox.critical(self, "Ошибка", "Не удалось получить информацию о номере!")
                return

            current_room_type, current_price = room_info

            # Создаем диалог с несколькими полями
            dialog = QDialog(self)
            dialog.setWindowTitle("Редактирование номера")
            dialog.setModal(True)
            dialog.setFixedSize(400, 250)

            layout = QtWidgets.QVBoxLayout(dialog)

            # Поле для номера комнаты
            room_layout = QtWidgets.QHBoxLayout()
            room_label = QtWidgets.QLabel("Номер комнаты:")
            self.room_edit = QtWidgets.QLineEdit()
            self.room_edit.setText(current_room)
            room_layout.addWidget(room_label)
            room_layout.addWidget(self.room_edit)

            # Поле для типа комнаты
            type_layout = QtWidgets.QHBoxLayout()
            type_label = QtWidgets.QLabel("Тип номера:")
            self.type_combo = QtWidgets.QComboBox()
            self.type_combo.addItems(['стандарт', 'люкс', 'полулюкс', 'семейный'])
            self.type_combo.setCurrentText(current_room_type)
            type_layout.addWidget(type_label)
            type_layout.addWidget(self.type_combo)

            # Поле для цены
            price_layout = QtWidgets.QHBoxLayout()
            price_label = QtWidgets.QLabel("Цена за ночь (руб.):")
            self.price_edit = QtWidgets.QLineEdit()
            self.price_edit.setText(str(current_price))
            price_layout.addWidget(price_label)
            price_layout.addWidget(self.price_edit)

            # Кнопки
            button_box = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.StandardButton.Ok |
                QtWidgets.QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)

            # Добавляем все в layout
            layout.addLayout(room_layout)
            layout.addLayout(type_layout)
            layout.addLayout(price_layout)
            layout.addWidget(button_box)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_room = self.room_edit.text().strip()
                new_type = self.type_combo.currentText()
                new_price = self.price_edit.text().strip()

                # Проверяем, не пустые ли поля
                if not new_room:
                    raise EmptyFieldError("Номер комнаты не может быть пустым")

                if not new_price:
                    raise EmptyFieldError("Цена не может быть пустой")

                # Проверяем номер комнаты
                if not new_room.isdigit():
                    raise InvalidRoomNumberError("Номер комнаты должен содержать только цифры")

                # Проверяем цену
                try:
                    price_validated = self.validate_price(new_price)
                except (EmptyFieldError, InvalidPriceError) as e:
                    QMessageBox.warning(self, "Ошибка цены", str(e))
                    return

                # Проверяем, изменился ли номер
                room_changed = new_room != current_room

                # Если номер изменился, проверяем на существование
                if room_changed:
                    self.cursor.execute("SELECT id FROM rooms WHERE room_number = ?", (new_room,))
                    if self.cursor.fetchone():
                        raise RoomExistsError("Номер с таким названием уже существует!")

                # Проверяем, что хотя бы что-то изменилось
                if (new_room == current_room and
                        new_type == current_room_type and
                        float(new_price) == current_price):
                    QMessageBox.information(self, "Информация", "Данные номера не изменены")
                    return

                # Обновляем номер в БД
                self.cursor.execute(
                    """UPDATE rooms 
                       SET room_number = ?, room_type = ?, price_per_night = ?
                       WHERE room_number = ?""",
                    (new_room, new_type, price_validated, current_room)
                )

                self.conn.commit()

                changes = []
                if room_changed:
                    changes.append(f"Номер: {current_room} → {new_room}")
                if new_type != current_room_type:
                    changes.append(f"Тип: {current_room_type} → {new_type}")
                if float(new_price) != current_price:
                    changes.append(f"Цена: {current_price} → {price_validated} руб.")

                QMessageBox.information(self, "Успех", f"Данные номера обновлены:\n" + "\n".join(changes))

                # Обновляем выбранный номер
                self.selected_room_number = new_room
                self.update_delete_button_state()

                self.load_rooms()  # Перезагружаем данные

        except EmptyFieldError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except InvalidRoomNumberError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except InvalidPriceError as e:
            QMessageBox.warning(self, "Ошибка цены", str(e))
        except RoomExistsError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        except DatabaseConnectionError as e:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка подключения к базе данных: {str(e)}")
        except DatabaseQueryError as e:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка выполнения запроса: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка изменения номера: {str(e)}")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        try:
            self.conn.close()
        except:
            pass
        event.accept()