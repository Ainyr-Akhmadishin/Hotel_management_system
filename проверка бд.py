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
def delete_maintenance_tasks_table():
    """Удаление таблицы maintenance_tasks"""
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()

    try:
        # Удаляем таблицу maintenance_tasks
        cursor.execute('DROP TABLE IF EXISTS maintenance_tasks')
        print("✅ Таблица maintenance_tasks удалена")

        # Сохраняем изменения
        conn.commit()
        print("✅ Изменения сохранены")

    except sqlite3.Error as e:
        print(f"❌ Ошибка: {e}")
    finally:
        # Закрываем соединение
        conn.close()
        print("✅ Соединение с базой данных закрыто")

def crate_table():
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE maintenance_tasks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            room_number VARCHAR(10) NOT NULL,
                            description TEXT NOT NULL,        -- описание задачи
                            assigned_to INTEGER,              -- кому назначена задача (staff.id)
                            created_by INTEGER NOT NULL,      -- кто создал задачу (staff.id)
                            status VARCHAR(20) DEFAULT 'в ожидании уборки', -- статус: новая, в работе, выполнена, отменена
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            completed_at TIMESTAMP,           -- когда выполнена
                            notes TEXT,
                            FOREIGN KEY (assigned_to) REFERENCES staff(id) ON DELETE SET NULL,
                            FOREIGN KEY (created_by) REFERENCES staff(id) ON DELETE RESTRICT
                        );''')


    conn.commit()
    conn.close()

def fill_task_table():
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()

    cursor.execute('''INSERT INTO maintenance_tasks 
                      (room_number, description, assigned_to, created_by, status, created_at, notes) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   ('101',
                    'Полная уборка номера: помыть полы, протереть пыль, сменить постельное белье',
                    6, 3, 'новая',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Особое внимание уделить ванной комнате'))

    # 2 задания (две задачи)
    cursor.execute('''INSERT INTO maintenance_tasks 
                      (room_number, description, assigned_to, created_by, status, created_at) 
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   ('205', 'Ежедневная уборка: убрать мусор, пополнить средства гигиены',
                    6, 3, 'в работе',
                    (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')))

    cursor.execute('''INSERT INTO maintenance_tasks 
                      (room_number, description, assigned_to, created_by, status, created_at, completed_at) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   ('308', 'Замена перегоревшей лампочки в ванной комнате',
                    7, 3, 'выполнена',
                    (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()

    # Проверяем что добавили
    cursor.execute('''SELECT COUNT(*) FROM maintenance_tasks''')
    task_count = cursor.fetchone()[0]

    print(f"Создано заданий: {task_count}")

    # Показываем созданные данные
    cursor.execute('''SELECT * FROM maintenance_tasks''')
    tasks = cursor.fetchall()

    print(tasks)
    # for task in tasks:
    #     print(f"ID: {task[0]}, Комната: {task[1]}, Статус: {task[5]}, Описание: {task[2][:30]}...")

    conn.close()
    
    
def select_staff():
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT staff.id,first_name, COUNT(*) from staff LEFT JOIN maintenance_tasks ON staff.id = maintenance_tasks.assigned_to WHERE position = "обслуживающий персонал" group by staff.id ''')
    print(cursor.fetchall())


import sqlite3


def clear_maintenance_tasks():
    """Полная очистка таблицы maintenance_tasks"""
    try:
        conn = sqlite3.connect('Hotel_bd.db')
        cursor = conn.cursor()

        # Получаем количество записей перед удалением
        cursor.execute("SELECT COUNT(*) FROM maintenance_tasks")
        count_before = cursor.fetchone()[0]

        # Очищаем таблицу
        cursor.execute("DELETE FROM maintenance_tasks")


        conn.commit()
        conn.close()

        print(f"✅ Таблица maintenance_tasks очищена")
        print(f"📊 Удалено записей: {count_before}")

        return True

    except Exception as e:
        print(f"❌ Ошибка очистки таблицы: {e}")
        return False

def update_staff():
    # Проверяем существование колонки shift_date и добавляем если нет
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT shift_date FROM staff LIMIT 1")
    except sqlite3.OperationalError:
        # Колонки нет, добавляем
        cursor.execute('ALTER TABLE staff ADD COLUMN shift_date DATE')
        print("✅ Добавлена колонка shift_date в таблицу staff")

        # Обновляем существующие записи с датами смен
        update_dates = [
            ("2024-01-15", 1),
            ("2024-01-20", 2),
            ("2024-01-10", 3),
            ("2024-01-25", 4),
            ("2024-01-18", 5),
            ("2024-01-22", 6),
            ("2024-01-12", 7),
            ("2024-01-28", 8)
        ]

        for shift_date, staff_id in update_dates:
            cursor.execute('UPDATE staff SET shift_date = ? WHERE id = ?', (shift_date, staff_id))
        print("✅ Обновлены даты смен для существующих сотрудников")

# Использование
# clear_maintenance_tasks()
# if __name__ == "__main__":
#     update_staff()
    # delete_tables_only()
    # y = YandexDiskUploader("y0__xD89tSJBBjblgMg1fC9ihUwhJeqlwgXFM-EwH6GAbo1cJ6dfjDG4_HR0g")
    # y.upload_db()
    # for i in print_data():
    #     print(i)
    # updating_guest_data()
    # delete_maintenance_tasks_table()
    # crate_table()
    # select_staff()
    # fill_task_table()
    # clear_maintenance_tasks()