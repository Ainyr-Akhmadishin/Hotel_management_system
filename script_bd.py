from datetime import timedelta, datetime
import sqlite3
import hashlib


def create_database():
    """Создание базы данных Hotel_bd и добавление сотрудников"""
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()

    # Создаем таблицы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name VARCHAR(20) NOT NULL,
            last_name VARCHAR(20) NOT NULL,
            patronymic VARCHAR(20),
            login VARCHAR(20) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            position TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number VARCHAR(10) UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            patronymic VARCHAR(50),
            passport_number VARCHAR(20) NOT NULL,
            phone_number VARCHAR(20) NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            check_in_date DATE NOT NULL,
            check_out_date DATE NOT NULL,
            FOREIGN KEY (guest_id) REFERENCES guests (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')

    # Данные для добавления
    rooms_data = [("101",), ("102",), ("103",), ("104",), ("105",),
                  ("201",), ("202",), ("203",), ("204",),
                  ("301",), ("302",), ("303",), ("304",)]

    staff_members = [
        ("Арслан", "Хубетдинов", "Илгамович", "Ars", "Ars", "администратор"),
        ("Ольга", "Смирнова", "Владимировна", "olga_admin", "olga123", "администратор"),
        ("Айнур", "Ахмадишин", "Азатович", "Aynur", "Aynur", "регистратор"),
        ("Сергей", "Козлов", "Дмитриевич", "sergey", "sergey123", "регистратор"),
        ("Мария", "Николаева", "Андреевна", "maria", "maria123", "регистратор"),
        ("Степан", "Разин", "Дмитриевич", "Step", "Step", "обслуживающий персонал"),
        ("Елена", "Зайцева", "Викторовна", "elena", "elena123", "обслуживающий персонал"),
        ("Игорь", "Соколов", "Александрович", "igor", "igor123", "обслуживающий персонал")
    ]

    guests_data = [
        ("Иван", "Иванов", "Иванович", "4510123456", "+7-912-345-67-89"),
        ("Петр", "Петров", "Васильевич", "4510987654", "+7-923-456-78-90"),
        ("Мария", "Сидорова", "Александровна", "4510567890", "+7-934-567-89-01"),
        ("Анна", "Козлова", "Сергеевна", "4510234567", "+7-945-678-90-12"),
        ("Сергей", "Смирнов", "Олегович", "4510345678", "+7-956-789-01-23"),
    ]

    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    # Добавляем сотрудников
    for first_name, last_name, patronymic, login, password, position in staff_members:
        try:
            password_hash = hash_password(password)
            cursor.execute('''
                INSERT INTO staff (first_name, last_name, patronymic, login, password_hash, position)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (first_name, last_name, patronymic, login, password_hash, position))
            print(f"✅ Добавлен сотрудник: {last_name} {first_name}")
        except sqlite3.IntegrityError:
            print(f"⚠️ Сотрудник уже существует: {login}")

    # Добавляем номера
    for room_number in rooms_data:
        try:
            cursor.execute('INSERT INTO rooms (room_number) VALUES (?)', room_number)
            print(f"✅ Добавлен номер: {room_number[0]}")
        except sqlite3.IntegrityError:
            print(f"⚠️ Номер уже существует: {room_number[0]}")

    # Добавляем гостей
    for first_name, last_name, patronymic, passport, phone in guests_data:
        try:
            cursor.execute('''
                INSERT INTO guests (first_name, last_name, patronymic, passport_number, phone_number)
                VALUES (?, ?, ?, ?, ?)
            ''', (first_name, last_name, patronymic, passport, phone))
            print(f"✅ Добавлен гость: {last_name} {first_name}")
        except sqlite3.IntegrityError:
            print(f"⚠️ Гость уже существует: {passport}")

    # ТЕПЕРЬ добавляем бронирования
    today = datetime.now().date()

    # Получаем реальные ID номеров из базы
    cursor.execute("SELECT id, room_number FROM rooms")
    room_mapping = {room_number: room_id for room_id, room_number in cursor.fetchall()}

    # Получаем реальные ID гостей из базы
    cursor.execute("SELECT id FROM guests ORDER BY id")
    guest_ids = [row[0] for row in cursor.fetchall()]

    test_bookings = [
        # Используем реальные room_id и guest_id
        (guest_ids[0], room_mapping["101"], today, today + timedelta(days=3)),
        (guest_ids[1], room_mapping["103"], today, today + timedelta(days=5)),
        (guest_ids[2], room_mapping["105"], today + timedelta(days=2), today + timedelta(days=7)),
        (guest_ids[3], room_mapping["203"], today + timedelta(days=1), today + timedelta(days=4)),
        (guest_ids[4], room_mapping["301"], today - timedelta(days=5), today + timedelta(days=10)),
        (guest_ids[0], room_mapping["102"], today - timedelta(days=10), today - timedelta(days=2)),
        (guest_ids[1], room_mapping["104"], today - timedelta(days=7), today - timedelta(days=1)),
    ]

    # Добавляем тестовые бронирования
    for guest_id, room_id, check_in, check_out in test_bookings:
        try:
            cursor.execute('''
                INSERT INTO bookings (guest_id, room_id, check_in_date, check_out_date)
                VALUES (?, ?, ?, ?)
            ''', (guest_id, room_id, check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d")))
            print(f"✅ Добавлено бронирование: гость {guest_id}, номер {room_id}")
        except Exception as e:
            print(f"❌ Ошибка добавления бронирования: {e}")

    conn.commit()
    conn.close()
    print("🎉 База данных создана с тестовыми бронированиями!")


if __name__ == "__main__":
    create_database()