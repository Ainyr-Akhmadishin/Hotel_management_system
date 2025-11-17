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
            room_number VARCHAR(10) UNIQUE NOT NULL,
            room_type VARCHAR(50) NOT NULL,
            price_per_night DECIMAL(10,2) NOT NULL
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER NOT NULL,
            to_user INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (from_user) REFERENCES staff(id) ON DELETE RESTRICT,
            FOREIGN KEY (to_user) REFERENCES staff(id) ON DELETE RESTRICT
        )
    ''')

    # Данные для добавления
    rooms_data = [
        ("101", "Стандарт", 3500.00),
        ("102", "Стандарт", 3500.00),
        ("103", "Стандарт", 3500.00),
        ("104", "Стандарт", 3500.00),
        ("105", "Стандарт", 3500.00),
        ("201", "Бизнес", 4500.00),
        ("202", "Бизнес", 4500.00),
        ("203", "Бизнес", 4500.00),
        ("204", "Бизнес", 4500.00),
        ("301", "Люкс", 5500.00),
        ("302", "Люкс", 5500.00),
        ("303", "Люкс", 5500.00),
        ("304", "Люкс", 5500.00)
    ]

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
    for room_data in rooms_data:
        try:
            cursor.execute('INSERT INTO rooms (room_number, room_type, price_per_night) VALUES (?, ?, ?)', room_data)
            print(f"✅ Добавлен номер: {room_data[0]} ({room_data[1]}) - {room_data[2]} руб.")
        except sqlite3.IntegrityError:
            print(f"⚠️ Номер уже существует: {room_data[0]}")

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

    # КОММИТ после добавления основных данных
    conn.commit()
    print("✅ Основные данные добавлены")

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
        (guest_ids[0], room_mapping["101"], today, today + timedelta(days=3)),
        (guest_ids[1], room_mapping["103"], today, today + timedelta(days=5)),
        (guest_ids[2], room_mapping["105"], today + timedelta(days=2), today + timedelta(days=7)),
        (guest_ids[3], room_mapping["203"], today + timedelta(days=1), today + timedelta(days=4)),

        # Долгосрочное бронирование (уже началось)
        (guest_ids[4], room_mapping["301"], today - timedelta(days=5), today + timedelta(days=10)),

        # Завершенные брони (выезд в прошлом)
        (guest_ids[0], room_mapping["102"], today - timedelta(days=10), today - timedelta(days=2)),
        (guest_ids[1], room_mapping["104"], today - timedelta(days=7), today - timedelta(days=1)),

        # ДОБАВЛЕННЫЕ БРОНИ ДЛЯ ПРОВЕРКИ ПЕРИОДОВ:

        # Брони за последний месяц (30 дней)
        (guest_ids[2], room_mapping["201"], today - timedelta(days=15), today - timedelta(days=10)),
        (guest_ids[3], room_mapping["302"], today - timedelta(days=25), today - timedelta(days=20)),

        # Брони за последние 6 месяцев (но больше месяца)
        (guest_ids[4], room_mapping["202"], today - timedelta(days=90), today - timedelta(days=85)),
        (guest_ids[0], room_mapping["304"], today - timedelta(days=120), today - timedelta(days=115)),

        # Брони за последний год (но больше 6 месяцев)
        (guest_ids[1], room_mapping["102"], today - timedelta(days=200), today - timedelta(days=195)),
        (guest_ids[2], room_mapping["204"], today - timedelta(days=300), today - timedelta(days=295)),

        # Будущие брони (ожидаются)
        (guest_ids[3], room_mapping["201"], today + timedelta(days=5), today + timedelta(days=8)),
        (guest_ids[4], room_mapping["302"], today + timedelta(days=10), today + timedelta(days=15)),
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

    # КОММИТ после бронирований
    conn.commit()
    print("✅ Бронирования добавлены")

    # Добавляем тестовые сообщения между сотрудниками
    # ИСПРАВЛЕНИЕ: используем числа 0 и 1 вместо False и True
    # test_messages = [
    #     (1, 2, "Добро пожаловать в систему! Проверьте новые бронирования.", 0),
    #     (2, 1, "Спасибо! Уже проверяю. Всё в порядке.", 1),
    #     (1, 3, "Подготовьте номер 101 к заселению. Гость приедет через 2 часа.", 0),
    #     (3, 1, "Номер 101 готов. Постельное белье заменено, уборка завершена.", 1),
    #     (1, 6, "Срочно! В номере 205 протекает кран. Нужно срочно починить.", 0),
    #     (6, 1, "Принято. Отправляюсь в номер 205 для ремонта.", 0),
    #     (2, 4, "Не забудьте проверить документы у гостя в номере 301.", 0),
    #     (4, 2, "Документы проверены, всё в порядке. Гость заселился.", 1),
    #     (1, 5, "Завтра плановая проверка номеров. Будьте готовы.", 0),
    #     (5, 7, "Помогите с уборкой в номерах 201-204. Спасибо!", 0)
    # ]
    #
    # # Добавляем тестовые сообщения
    # for from_user, to_user, text, is_read in test_messages:
    #     try:
    #         cursor.execute('''
    #             INSERT INTO messages (from_user, to_user, text, is_read)
    #             VALUES (?, ?, ?, ?)
    #         ''', (from_user, to_user, text, is_read))
    #         print(f"✅ Добавлено сообщение: {from_user} -> {to_user}")
    #     except Exception as e:
    #         print(f"❌ Ошибка добавления сообщения: {e}")

    # ФИНАЛЬНЫЙ КОММИТ
    conn.execute('DELETE FROM messages')
    conn.commit()
    conn.close()

    # Проверяем что сообщения добавились
    # cursor.execute("SELECT COUNT(*) FROM messages")
    # message_count = cursor.fetchone()[0]
    # print(f"📊 Добавлено сообщений: {message_count}")

    conn.close()
    print("🎉 База данных создана с тестовыми бронированиями и сообщениями!")


if __name__ == "__main__":
    create_database()