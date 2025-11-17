import sqlite3
from bd_manager import YandexDiskUploader

def updating_guest_data():
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()

    # ИСПРАВЛЕННЫЙ ЗАПРОС - используем правильные названия столбцов
    cursor.execute('''SELECT * FROM messages''')
    guests = cursor.fetchall()

    print("Данные о бронированиях:")
    for guest in guests:
        print(guest)

    conn.close()


import sqlite3


def delete_tables_only():
    # Подключаемся к базе данных
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()

    try:

        # Удаляем таблицу rooms
        cursor.execute('DROP TABLE IF EXISTS rooms')
        print("Таблица rooms удалена")

        # Сохраняем изменения
        conn.commit()
        print("Таблицы удалены")

    except sqlite3.Error as e:
        print(f"Ошибка: {e}")

    finally:
        # Закрываем соединение
        conn.close()
        print("Соединение с базой данных закрыто")
from datetime import datetime, timedelta
def print_data():


    # Текущая дата
    today = datetime.now().date()

    # Граничные даты для периодов
    period = 'month'
    if period == 'month':
        start_date = today - timedelta(days=30)
    elif period == '6months':
        start_date = today - timedelta(days=180)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)

    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT 
                             room_number, 
                             last_name || '.' || SUBSTR(first_name,1,1) || '.' || SUBSTR(patronymic,1,1) as guest_initials, 
                             check_in_date, 
                             check_out_date,
                             CAST(JULIANDAY(check_out_date) - JULIANDAY(check_in_date) AS INTEGER) as nights,
                             room_type, 
                             price_per_night, 
                             (CAST(JULIANDAY(check_out_date) - JULIANDAY(check_in_date) AS INTEGER) * price_per_night) as total_cost,
                             CASE 
                               WHEN date(check_out_date) < date('now') THEN 'Завершено'
                               WHEN date(check_in_date) <= date('now') THEN 'Активно'
                               ELSE 'Ожидается'
                             END as booking_status
                    FROM rooms JOIN bookings ON rooms.id = bookings.room_id 
                    JOIN guests ON bookings.guest_id = guests.id
                    WHERE check_in_date BETWEEN date(?) AND date('now')
                    ORDER BY check_in_date, room_number''',(start_date.strftime('%Y-%m-%d'),))

    rooms = cursor.fetchall()
    return rooms

if __name__ == "__main__":
    # delete_tables_only()
    # y = YandexDiskUploader("y0__xD89tSJBBjblgMg1fC9ihUwhJeqlwgXFM-EwH6GAbo1cJ6dfjDG4_HR0g")
    # y.upload_db()
    for i in print_data():
        print(i)
    # updating_guest_data()