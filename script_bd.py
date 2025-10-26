import sqlite3
import hashlib


def create_database():
    """Создание базы данных Hotel_bd и добавление сотрудников"""

    # Подключаемся к базе данных (создаст файл Hotel_bd.db)
    conn = sqlite3.connect('Hotel_bd.db')
    cursor = conn.cursor()

    # Создаем таблицу сотрудников
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name VARCHAR(20) NOT NULL,
            last_name VARCHAR(20) NOT NULL,
            patronymic VARCHAR(20),
            login VARCHAR(20) UNIQUE NOT NULL,
            password_hash VARCHAR(20) NOT NULL,
            position TEXT NOT NULL
        )
    ''')

    # Функция для хеширования пароля
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    # Данные сотрудников для добавления
    staff_members = [
        # Администраторы
        ("Арслан", "Хубетдинов", "Илгамович", "Ars", "Ars", "администратор"),
        ("Ольга", "Смирнова", "Владимировна", "olga_admin", "olga123", "администратор"),

        # Регистраторы
        ("Айнур", "Ахмадишин", "Азатович", "Aynur", "Aynur", "регистратор"),
        ("Сергей", "Козлов", "Дмитриевич", "sergey", "sergey123", "регистратор"),
        ("Мария", "Николаева", "Андреевна", "maria", "maria123", "регистратор"),

        # Обслуживающий персонал
        ("Степан", "Разин", "Дмитриевич", "Step", "Step", "обслуживающий персонал"),
        ("Елена", "Зайцева", "Викторовна", "elena", "elena123", "обслуживающий персонал"),
        ("Игорь", "Соколов", "Александрович", "igor", "igor123", "обслуживающий персонал")
    ]

    # Добавляем сотрудников в базу данных
    for first_name, last_name, patronymic, login, password, position in staff_members:
        try:
            password_hash = hash_password(password)
            cursor.execute('''
                INSERT INTO staff (first_name, last_name, patronymic, login, password_hash, position)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (first_name, last_name, patronymic, login, password_hash, position))
            print(f"✅ Добавлен: {last_name} {first_name} {patronymic} - {position}")
        except sqlite3.IntegrityError:
            print(f"⚠️ Уже существует: {login}")

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

    print("\n🎉 База данных Hotel_bd.db успешно создана!")
    print("👥 Добавлено сотрудников: 8")
    print("📊 Распределение по должностям:")
    print("   - Администраторы: 2")
    print("   - Регистраторы: 3")
    print("   - Обслуживающий персонал: 3")


# Запускаем создание базы данных
if __name__ == "__main__":
    create_database()