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


if __name__ == "__main__":
    # y = YandexDiskUploader("y0__xD89tSJBBjblgMg1fC9ihUwhJeqlwgXFM-EwH6GAbo1cJ6dfjDG4_HR0g")
    # y.upload_db()
    # updating_guest_data()