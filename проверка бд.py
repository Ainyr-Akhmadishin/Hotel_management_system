import sqlite3


def updating_guest_data():
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()

    # ИСПРАВЛЕННЫЙ ЗАПРОС - используем правильные названия столбцов
    cursor.execute('''SELECT room_id, last_name || ' ' || SUBSTR(first_name, 1, 1) || '. ' || SUBSTR(patronymic, 1, 1) || '.' as f, check_in_date, check_out_date FROM bookings JOIN guests ON bookings.guest_id = guests.id''')
    guests = cursor.fetchall()

    print("Данные о бронированиях:")
    for guest in guests:
        print(guest)

    conn.close()


if __name__ == "__main__":
    updating_guest_data()