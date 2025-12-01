from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox, QDialog, QFileDialog
from PyQt6.QtCore import QDate
import sqlite3
import csv
import json
from datetime import datetime
from utils import get_resource_path


class ExportDataError(Exception):
    pass  # Исключение для ошибок экспорта данных

class ImportDataError(Exception):
    pass  # Исключение для ошибок импорта данных

class InvalidDateError(Exception):
    pass  # Исключение для невалидных дат

class DatabaseConnectionError(Exception):
    pass  # Исключение для ошибок подключения к базе данных

class DataExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(get_resource_path('UI/Admin/загрузка и выгрузка переделенная.ui'), self)

        self.setWindowTitle("Аналитика отеля")
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))

        # Инициализация БД
        self.conn = sqlite3.connect('Hotel_bd.db')
        self.cursor = self.conn.cursor()

        # Устанавливаем даты по умолчанию
        today = QDate.currentDate()
        self.start_date_edit.setDate(today.addDays(-30))  # Последние 30 дней
        self.end_date_edit.setDate(today)

        # Подключаем кнопки
        self.export_data_btn.clicked.connect(self.export_data)
        self.load_data_btn.clicked.connect(self.load_data)
        self.start_date_edit.dateChanged.connect(self.update_stats)
        self.end_date_edit.dateChanged.connect(self.update_stats)

        # Загружаем статистику
        self.update_stats()

    def validate_dates(self):
        """Проверка корректности дат"""
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        today = QDate.currentDate()

        if start_date > end_date:
            raise InvalidDateError("Начальная дата не может быть больше конечной!")

        if end_date > today:
            raise InvalidDateError("Невозможно выгрузить будущие данные!")

    def update_stats(self):
        """Обновление статистики"""
        try:
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

            # Проверяем корректность дат
            try:
                self.validate_dates()
                self.date_error_label.setText("")
            except InvalidDateError as e:
                self.date_error_label.setText(f"❌ {str(e)}")
                self.attendance_value.setText("0")
                self.profit_value.setText("0 ₽")
                return

            # Статистика по бронированиям
            self.cursor.execute("""
                SELECT COUNT(*) as booking_count,
                       COUNT(*) * 2500 as estimated_profit
                FROM bookings 
                WHERE check_in_date BETWEEN ? AND ?
            """, (start_date, end_date))

            stats = self.cursor.fetchone()
            booking_count = stats[0] if stats else 0
            estimated_profit = stats[1] if stats else 0

            self.attendance_value.setText(str(booking_count))
            self.profit_value.setText(f"{estimated_profit:,} ₽".replace(",", " "))

        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Ошибка загрузки статистики")

    def export_data(self):
        """Экспорт данных за период"""
        try:
            # Проверяем корректность дат перед экспортом
            try:
                self.validate_dates()
            except InvalidDateError as e:
                QMessageBox.warning(self, "Ошибка в датах", str(e))
                return

            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

            # Выбор формата экспорта
            format_choice, ok = QtWidgets.QInputDialog.getItem(
                self, "Экспорт данных", "Выберите формат экспорта:",
                ["CSV", "JSON"], 0, False
            )

            if not ok:
                return

            # Выбор типа данных
            data_choice, ok = QtWidgets.QInputDialog.getItem(
                self, "Экспорт данных", "Выберите данные для экспорта:",
                ["Статистика отеля", "Бронирования", "Сотрудники", "Номера", "Все данные"], 0, False
            )

            if not ok:
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Экспорт данных",
                f"hotel_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_choice.lower()}",
                f"{format_choice} Files (*.{format_choice.lower()})"
            )

            if file_path:
                if format_choice == "CSV":
                    self.export_to_csv(file_path, data_choice, start_date, end_date)
                else:
                    self.export_to_json(file_path, data_choice, start_date, end_date)

                QMessageBox.information(self, "Успех", f"Данные экспортированы в {file_path}")

        except ExportDataError as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта данных")

    def export_to_csv(self, file_path, data_type, start_date, end_date):
        """Экспорт в CSV с правильной кодировкой UTF-8"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:  # Используем utf-8-sig для Excel
                writer = csv.writer(file, delimiter=';')  # Используем точку с запятой как разделитель

                if data_type == "Статистика отеля":
                    # Получаем статистику за период
                    self.cursor.execute("""
                        SELECT COUNT(*) as booking_count,
                               COUNT(*) * 2500 as total_profit
                        FROM bookings 
                        WHERE check_in_date BETWEEN ? AND ?
                    """, (start_date, end_date))

                    stats = self.cursor.fetchone()
                    booking_count = stats[0] if stats else 0
                    total_profit = stats[1] if stats else 0

                    # Записываем только чистую статистику
                    writer.writerow(['Показатель', 'Значение'])
                    writer.writerow(['Период', f'{start_date} - {end_date}'])
                    writer.writerow(['Дата экспорта', datetime.now().strftime('%d.%m.%Y %H:%M:%S')])
                    writer.writerow(['Посещаемость (бронирования)', booking_count])
                    writer.writerow(['Общая прибыль', f'{total_profit} ₽'])
                    writer.writerow(['Средняя стоимость номера', '2500 ₽'])

                elif data_type == "Бронирования":
                    writer.writerow(['ID', 'Гость', 'Номер', 'Заезд', 'Выезд', 'Статус', 'Стоимость'])
                    self.cursor.execute("""
                        SELECT b.id, g.first_name || ' ' || g.last_name as guest_name,
                               r.room_number, b.check_in_date, b.check_out_date,
                               CASE WHEN date('now') BETWEEN b.check_in_date AND b.check_out_date 
                                    THEN 'Активно' ELSE 'Завершено' END as status,
                               2500 as price
                        FROM bookings b
                        JOIN guests g ON b.guest_id = g.id
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.check_in_date BETWEEN ? AND ?
                        ORDER BY b.check_in_date
                    """, (start_date, end_date))
                    data = self.cursor.fetchall()
                    for row in data:
                        writer.writerow(row)

                elif data_type == "Сотрудники":
                    writer.writerow(['Фамилия', 'Имя', 'Отчество', 'Должность', 'Логин'])
                    self.cursor.execute("SELECT last_name, first_name, patronymic, position, login FROM staff")
                    data = self.cursor.fetchall()
                    for row in data:
                        writer.writerow(row)

                elif data_type == "Номера":
                    writer.writerow(['Номер', 'Статус', 'Гость', 'Период проживания', 'Стоимость за ночь'])
                    self.cursor.execute("""
                        SELECT r.room_number,
                               CASE WHEN EXISTS (
                                   SELECT 1 FROM bookings b 
                                   WHERE b.room_id = r.id 
                                   AND date('now') BETWEEN b.check_in_date AND b.check_out_date
                               ) THEN 'Занят' ELSE 'Свободен' END as status,
                               COALESCE(g.first_name || ' ' || g.last_name, 'Нет') as guest_name,
                               CASE WHEN b.check_in_date IS NOT NULL 
                                    THEN b.check_in_date || ' - ' || b.check_out_date 
                                    ELSE 'Нет' END as period,
                               2500 as price
                        FROM rooms r
                        LEFT JOIN bookings b ON r.id = b.room_id AND date('now') BETWEEN b.check_in_date AND b.check_out_date
                        LEFT JOIN guests g ON b.guest_id = g.id
                        ORDER BY r.room_number
                    """)
                    data = self.cursor.fetchall()
                    for row in data:
                        writer.writerow(row)

                else:  # Все данные
                    # Статистика
                    self.cursor.execute("""
                        SELECT COUNT(*) as booking_count,
                               COUNT(*) * 2500 as total_profit
                        FROM bookings 
                        WHERE check_in_date BETWEEN ? AND ?
                    """, (start_date, end_date))
                    stats = self.cursor.fetchone()

                    writer.writerow(['СТАТИСТИКА ОТЕЛЯ'])
                    writer.writerow(['Период', f'{start_date} - {end_date}'])
                    writer.writerow(['Дата экспорта', datetime.now().strftime('%d.%m.%Y %H:%M:%S')])
                    writer.writerow(['Посещаемость', stats[0] if stats else 0])
                    writer.writerow(['Прибыль', f'{stats[1] if stats else 0} ₽'])
                    writer.writerow([])

                    # Бронирования
                    writer.writerow(['БРОНИРОВАНИЯ'])
                    writer.writerow(['Гость', 'Номер', 'Заезд', 'Выезд', 'Стоимость'])
                    self.cursor.execute("""
                        SELECT g.first_name || ' ' || g.last_name, r.room_number, 
                               b.check_in_date, b.check_out_date, 2500
                        FROM bookings b
                        JOIN guests g ON b.guest_id = g.id
                        JOIN rooms r ON b.room_id = r.id
                        WHERE b.check_in_date BETWEEN ? AND ?
                        ORDER BY b.check_in_date
                    """, (start_date, end_date))
                    data = self.cursor.fetchall()
                    for row in data:
                        writer.writerow(row)

        except IOError as e:
            raise ExportDataError(f"Ошибка записи файла: {str(e)}")
        except Exception as e:
            raise ExportDataError(f"Ошибка при экспорте в CSV")

    def export_to_json(self, file_path, data_type, start_date, end_date):
        """Экспорт в JSON с правильной кодировкой"""
        try:
            data = {}

            if data_type == "Статистика отеля":
                # Получаем статистику
                self.cursor.execute("""
                    SELECT COUNT(*) as booking_count,
                           COUNT(*) * 2500 as total_profit
                    FROM bookings 
                    WHERE check_in_date BETWEEN ? AND ?
                """, (start_date, end_date))

                stats = self.cursor.fetchone()

                data = {
                    'hotel_statistics': {
                        'period': {
                            'start_date': start_date,
                            'end_date': end_date
                        },
                        'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'attendance': stats[0] if stats else 0,
                        'total_profit': stats[1] if stats else 0,
                        'average_room_price': 2500,
                        'currency': 'RUB'
                    }
                }

            elif data_type == "Бронирования":
                self.cursor.execute("""
                    SELECT b.id, g.first_name, g.last_name, r.room_number, 
                           b.check_in_date, b.check_out_date
                    FROM bookings b
                    JOIN guests g ON b.guest_id = g.id
                    JOIN rooms r ON b.room_id = r.id
                    WHERE b.check_in_date BETWEEN ? AND ?
                    ORDER BY b.check_in_date
                """, (start_date, end_date))

                bookings = []
                for row in self.cursor.fetchall():
                    bookings.append({
                        'id': row[0],
                        'guest': f"{row[1]} {row[2]}",
                        'room': row[3],
                        'check_in': row[4],
                        'check_out': row[5],
                        'price': 2500
                    })
                data['bookings'] = bookings

            elif data_type == "Сотрудники":
                self.cursor.execute("SELECT first_name, last_name, patronymic, position, login FROM staff")
                employees = []
                for row in self.cursor.fetchall():
                    employees.append({
                        'first_name': row[0],
                        'last_name': row[1],
                        'patronymic': row[2],
                        'position': row[3],
                        'login': row[4]
                    })
                data['employees'] = employees

            elif data_type == "Номера":
                self.cursor.execute("""
                    SELECT r.room_number,
                           CASE WHEN EXISTS (
                               SELECT 1 FROM bookings b 
                               WHERE b.room_id = r.id 
                               AND date('now') BETWEEN b.check_in_date AND b.check_out_date
                           ) THEN 'occupied' ELSE 'available' END as status
                    FROM rooms r
                    ORDER BY r.room_number
                """)
                rooms = []
                for row in self.cursor.fetchall():
                    rooms.append({
                        'room_number': row[0],
                        'status': row[1],
                        'price_per_night': 2500
                    })
                data['rooms'] = rooms

            else:  # Все данные
                # Статистика
                self.cursor.execute("""
                    SELECT COUNT(*) as booking_count,
                           COUNT(*) * 2500 as total_profit
                    FROM bookings 
                    WHERE check_in_date BETWEEN ? AND ?
                """, (start_date, end_date))
                stats = self.cursor.fetchone()

                data = {
                    'export_info': {
                        'period': {
                            'start_date': start_date,
                            'end_date': end_date
                        },
                        'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'statistics': {
                        'attendance': stats[0] if stats else 0,
                        'total_profit': stats[1] if stats else 0
                    }
                }

            # Сохраняем с правильной кодировкой
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

        except IOError as e:
            raise ExportDataError(f"Ошибка записи файла: {str(e)}")
        except Exception as e:
            raise ExportDataError(f"Ошибка при экспорте в JSON: {str(e)}")

    def load_data(self):
        """Загрузка данных из файла"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Загрузка данных", "",
                "All Files (*.csv *.json);;CSV Files (*.csv);;JSON Files (*.json)"
            )

            if file_path:
                if file_path.endswith('.csv'):
                    self.import_from_csv(file_path)
                elif file_path.endswith('.json'):
                    self.import_from_json(file_path)

                QMessageBox.information(self, "Успех", "Данные успешно загружены!")
                self.update_stats()  # Обновляем статистику

        except ImportDataError as e:
            QMessageBox.critical(self, "Ошибка импорта", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных")

    def import_from_csv(self, file_path):
        """Импорт из CSV с правильной кодировкой"""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.reader(file, delimiter=';')
                for row in reader:
                    print(row)  # Для отладки - посмотреть что импортируется
            QMessageBox.information(self, "Информация", "Данные CSV успешно прочитаны")
        except FileNotFoundError:
            raise ImportDataError("Файл не найден")
        except Exception as e:
            raise ImportDataError(f"Ошибка чтения CSV файла")

    def import_from_json(self, file_path):
        """Импорт из JSON с правильной кодировкой"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                print(data)  # Для отладки - посмотреть что импортируется
            QMessageBox.information(self, "Информация", "Данные JSON успешно прочитаны")
        except FileNotFoundError:
            raise ImportDataError("Файл не найден")
        except Exception as e:
            raise ImportDataError(f"Ошибка чтения JSON файла")

    def closeEvent(self, event):
        """Закрытие соединения с БД"""
        try:
            self.conn.close()
        except:
            pass
        event.accept()