import sqlite3
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, QHeaderView, QPushButton, QMessageBox,
                             QHBoxLayout, QDialog, QTextEdit, QMenu, QInputDialog)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta


class GuestDetailsDialog(QDialog):
    """Диалог для отображения полной информации о госте"""

    def __init__(self, guest_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Полная информация о госте")
        self.setGeometry(200, 200, 500, 400)

        self.setup_ui()
        self.display_guest_data(guest_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("font-family: Arial; font-size: 12px;")

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)

        layout.addWidget(self.text_edit)
        layout.addWidget(close_btn)

    def display_guest_data(self, guest_data):
        """Отображает полную информацию о госте"""
        # Форматируем даты для красивого отображения
        check_in = guest_data.get('check_in_date', '')
        check_out = guest_data.get('check_out_date', '')

        if check_in:
            try:
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d').strftime('%d.%m.%Y')
            except:
                check_in_date = check_in
        else:
            check_in_date = 'Не указано'

        if check_out:
            try:
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d').strftime('%d.%m.%Y')
            except:
                check_out_date = check_out
        else:
            check_out_date = 'Не указано'

        # Рассчитываем продолжительность проживания
        duration = "Не указано"
        if check_in and check_out:
            try:
                check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
                check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
                days = (check_out_dt - check_in_dt).days
                if days > 0:
                    duration = f"{days} {self.get_days_text(days)}"
                else:
                    duration = "Даты некорректны"
            except:
                duration = "Ошибка расчета"

        # Определяем статус проживания
        status = self.get_booking_status(check_in, check_out)

        text = f"""
╔═══════════════════════════════════════╗
║           ИНФОРМАЦИЯ О ГОСТЕ          ║
╚═══════════════════════════════════════╝

📋 ЛИЧНЫЕ ДАННЫЕ:
├─ Фамилия: {guest_data.get('last_name', 'Не указано')}
├─ Имя: {guest_data.get('first_name', 'Не указано')}
├─ Отчество: {guest_data.get('patronymic', 'Не указано')}
├─ Паспорт: {guest_data.get('passport_number', 'Не указано')}
├─ Телефон: {guest_data.get('phone_number', 'Не указано')}

🏨 ИНФОРМАЦИЯ О БРОНИРОВАНИИ:
├─ Номер комнаты: {guest_data.get('room_number', 'Не указано')}
├─ Дата заселения: {check_in_date}
├─ Дата выселения: {check_out_date}
├─ Продолжительность: {duration}
├─ Статус: {status}

📊 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:
├─ ID бронирования: {guest_data.get('booking_id', 'Не указано')}
├─ ID гостя: {guest_data.get('guest_id', 'Не указано')}
        """
        self.text_edit.setText(text)

    def get_days_text(self, days):
        """Возвращает правильную форму слова 'день'"""
        if days % 10 == 1 and days % 100 != 11:
            return "день"
        elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
            return "дня"
        else:
            return "дней"

    def get_booking_status(self, check_in, check_out):
        """Определяет статус бронирования"""
        if not check_in or not check_out:
            return "❓ Не определен"

        try:
            today = datetime.now().date()
            check_in_dt = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_dt = datetime.strptime(check_out, '%Y-%m-%d').date()

            if check_out_dt < today:
                return "✅ Завершено"
            elif check_in_dt <= today <= check_out_dt:
                return "🟢 Активно"
            elif check_in_dt > today:
                days_until = (check_in_dt - today).days
                return f"⏳ Ожидается (через {days_until} дн.)"
            else:
                return "❓ Не определен"
        except:
            return "❓ Ошибка дат"


class BookingsViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Просмотр бронирований и постояльцев")
        self.setGeometry(100, 100, 1200, 700)

        self.setup_ui()
        self.load_bookings()

    def setup_ui(self):
        """Создание интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Создаем таблицу
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Фамилия", "Имя", "Отчество", "Паспорт", "Телефон", "Номер", "Заселение", "Выезд"
        ])

        # Настройка таблицы
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self.show_guest_details)

        # Включаем контекстное меню
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Панель кнопок
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.load_bookings)

        self.details_btn = QPushButton("👤 Подробнее о госте")
        self.details_btn.clicked.connect(self.show_selected_guest_details)

        self.delete_btn = QPushButton("🗑️ Удалить бронирование")
        self.delete_btn.clicked.connect(self.delete_selected_booking)

        self.check_db_btn = QPushButton("🔍 Проверить БД")
        self.check_db_btn.clicked.connect(self.check_database_structure)

        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.details_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.check_db_btn)
        button_layout.addStretch()

        layout.addWidget(self.table)
        layout.addLayout(button_layout)

    def show_context_menu(self, position):
        """Показывает контекстное меню для таблицы"""
        menu = QMenu(self)

        details_action = menu.addAction("👤 Подробнее")
        delete_action = menu.addAction("🗑️ Удалить бронирование")
        early_checkout_action = menu.addAction("🏃 Досрочное выселение")

        action = menu.exec(self.table.mapToGlobal(position))

        current_row = self.table.currentRow()
        if current_row >= 0:
            guest_data = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

            if action == details_action:
                self.open_guest_details_dialog(guest_data)
            elif action == delete_action:
                self.delete_booking(guest_data)
            elif action == early_checkout_action:
                self.early_checkout(guest_data)

    def delete_selected_booking(self):
        """Удаляет выбранное бронирование"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            guest_data = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            self.delete_booking(guest_data)
        else:
            QMessageBox.warning(self, "Внимание", "Выберите бронирование для удаления")

    def delete_booking(self, guest_data):
        """Удаляет бронирование и при необходимости гостя"""
        try:
            booking_id = guest_data.get('booking_id')
            guest_id = guest_data.get('guest_id')
            guest_name = f"{guest_data.get('last_name')} {guest_data.get('first_name')}"
            room_number = guest_data.get('room_number')

            # Подтверждение удаления
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Вы уверены, что хотите удалить бронирование?\n"
                f"Гость: {guest_name}\n"
                f"Номер: {room_number}\n\n"
                f"Это действие нельзя отменить!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                conn = sqlite3.connect('Hotel_bd.db')
                cursor = conn.cursor()

                # Удаляем бронирование
                cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))

                # Проверяем, есть ли у гостя другие бронирования
                cursor.execute('SELECT COUNT(*) FROM bookings WHERE guest_id = ?', (guest_id,))
                remaining_bookings = cursor.fetchone()[0]

                # Если других бронирований нет - удаляем гостя
                if remaining_bookings == 0:
                    cursor.execute('DELETE FROM guests WHERE id = ?', (guest_id,))
                    message = f"Бронирование и данные гостя {guest_name} удалены"
                else:
                    message = f"Бронирование удалено, но гость {guest_name} сохранен (есть другие бронирования)"

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Успех", message)
                self.load_bookings()  # Обновляем таблицу

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить бронирование: {str(e)}")

    def early_checkout(self, guest_data):
        """Выполняет досрочное выселение гостя"""
        try:
            booking_id = guest_data.get('booking_id')
            guest_name = f"{guest_data.get('last_name')} {guest_data.get('first_name')}"
            room_number = guest_data.get('room_number')

            # Запрашиваем новую дату выселения
            new_date, ok = QInputDialog.getText(
                self,
                "Досрочное выселение",
                f"Введите новую дату выселения для {guest_name} (номер {room_number}):\n"
                f"Формат: ГГГГ-ММ-ДД",
                text=datetime.now().strftime('%Y-%m-%d')
            )

            if ok and new_date:
                # Проверяем формат даты
                try:
                    check_date = datetime.strptime(new_date, '%Y-%m-%d')

                    conn = sqlite3.connect('Hotel_bd.db')
                    cursor = conn.cursor()

                    # Обновляем дату выселения
                    cursor.execute(
                        'UPDATE bookings SET check_out_date = ? WHERE id = ?',
                        (new_date, booking_id)
                    )

                    conn.commit()
                    conn.close()

                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Гость {guest_name} выселен досрочно.\nНовая дата выселения: {new_date}"
                    )
                    self.load_bookings()  # Обновляем таблицу

                except ValueError:
                    QMessageBox.warning(self, "Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить выселение: {str(e)}")

    def check_database_structure(self):
        """Проверяет структуру базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем список всех таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            table_info = "📊 СТРУКТУРА БАЗЫ ДАННЫХ:\n\n"

            for table in tables:
                table_name = table[0]
                table_info += f"📋 Таблица: {table_name}\n"

                # Получаем структуру таблицы
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                for col in columns:
                    table_info += f"   ├─ {col[1]} ({col[2]})\n"
                table_info += "\n"

            conn.close()

            QMessageBox.information(self, "Структура БД", table_info)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось проверить структуру БД: {str(e)}")

    def load_bookings(self):
        """Загрузка бронирований из базы данных с информацией о периоде проживания"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Запрос для получения полной информации о бронированиях
            cursor.execute('''
                SELECT 
                    g.last_name,
                    g.first_name,
                    g.patronymic,
                    g.passport_number,
                    g.phone_number,
                    r.room_number,
                    b.check_in_date,
                    b.check_out_date,
                    b.id as booking_id,
                    g.id as guest_id
                FROM bookings b
                JOIN guests g ON b.guest_id = g.id
                JOIN rooms r ON b.room_id = r.id
                ORDER BY b.check_in_date DESC
            ''')
            bookings = cursor.fetchall()

            # Заполняем таблицу
            self.table.setRowCount(len(bookings))
            self.table.setColumnCount(8)
            self.table.setHorizontalHeaderLabels([
                "Фамилия", "Имя", "Отчество", "Паспорт", "Телефон", "Номер", "Заселение", "Выезд"
            ])

            for row, booking in enumerate(bookings):
                for col, value in enumerate(booking[:8]):  # Первые 8 колонок
                    item = QTableWidgetItem(str(value) if value is not None else "")

                    # Форматируем даты для лучшего отображения
                    if col in [6, 7] and value:  # Колонки с датами
                        try:
                            date_obj = datetime.strptime(value, '%Y-%m-%d')
                            item.setText(date_obj.strftime('%d.%m.%Y'))

                            # Подсвечиваем активные бронирования
                            today = datetime.now().date()
                            check_in = datetime.strptime(booking[6], '%Y-%m-%d').date()
                            check_out = datetime.strptime(booking[7], '%Y-%m-%d').date()

                            if check_in <= today <= check_out:
                                item.setBackground(Qt.GlobalColor.green)
                                item.setToolTip("Активное бронирование")
                            elif check_out < today:
                                item.setBackground(Qt.GlobalColor.lightGray)
                                item.setToolTip("Завершенное бронирование")
                            else:
                                item.setBackground(Qt.GlobalColor.yellow)
                                item.setToolTip("Предстоящее бронирование")

                        except:
                            pass

                    self.table.setItem(row, col, item)

                # Сохраняем полные данные гостя для диалога
                guest_data = {
                    'last_name': booking[0],
                    'first_name': booking[1],
                    'patronymic': booking[2],
                    'passport_number': booking[3],
                    'phone_number': booking[4],
                    'room_number': booking[5],
                    'check_in_date': booking[6],
                    'check_out_date': booking[7],
                    'booking_id': booking[8],
                    'guest_id': booking[9]
                }
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, guest_data)

            print(f"✅ Загружено бронирований: {len(bookings)}")

            conn.close()

        except sqlite3.Error as e:
            QMessageBox.warning(self, "Внимание",
                                f"Не удалось загрузить бронирования: {str(e)}\n"
                                f"Проверьте структуру базы данных.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось подключиться к базе данных: {str(e)}\n"
                                 f"Убедитесь что файл Hotel_bd.db существует.")

    def show_guest_details(self, index):
        """Показывает детали гостя при двойном клике"""
        row = index.row()
        guest_data = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.open_guest_details_dialog(guest_data)

    def show_selected_guest_details(self):
        """Показывает детали выбранного гостя"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            guest_data = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            self.open_guest_details_dialog(guest_data)
        else:
            QMessageBox.warning(self, "Внимание", "Выберите гостя из таблицы")

    def open_guest_details_dialog(self, guest_data):
        """Открывает диалог с детальной информацией о госте"""
        dialog = GuestDetailsDialog(guest_data, self)
        dialog.exec()


def main():
    app = QApplication(sys.argv)

    window = BookingsViewer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()