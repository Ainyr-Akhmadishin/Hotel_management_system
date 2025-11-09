# yandex_uploader.py
import yadisk
import os
from datetime import datetime


class YandexDiskUploader:
    def __init__(self, token):
        self.y = yadisk.YaDisk(token=token)
        self.remote_path = "/HotelApp/Hotel_bd.db"
        self.local_file = "Hotel_bd.db"

    def check_connection(self):
        """Проверить подключение к Яндекс Диску"""
        try:
            if self.y.check_token():
                print("✅ Подключение к Яндекс Диску установлено")
                return True
            else:
                print("❌ Не удалось подключиться к Яндекс Диску")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def upload_db(self):
        """Загрузить БД на Яндекс Диск"""
        try:
            # Проверяем есть ли локальный файл
            if not os.path.exists(self.local_file):
                print(f"❌ Файл {self.local_file} не найден")
                return False

            # Создаем папку на Яндекс Диске если нужно
            if not self.y.exists("/HotelApp"):
                self.y.mkdir("/HotelApp")
                print("✅ Создана папка /HotelApp на Яндекс Диске")

            # Загружаем файл
            print("🔄 Загрузка файла на Яндекс Диск...")
            self.y.upload(self.local_file, self.remote_path, overwrite=True)

            print("✅ Файл успешно загружен на Яндекс Диск!")
            print(f"📁 Путь: {self.remote_path}")
            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False

    def download_db(self):
        """Скачать БД с Яндекс Диска"""
        try:
            # Проверяем есть ли файл на Яндекс Диске
            if not self.y.exists(self.remote_path):
                print("❌ Файл не найден на Яндекс Диске")
                return False

            # Создаем резервную копию если файл уже существует
            if os.path.exists(self.local_file):
                backup_name = f"Hotel_bd_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                os.rename(self.local_file, backup_name)
                print(f"✅ Создана резервная копия: {backup_name}")

            # Скачиваем файл
            print("🔄 Скачивание файла с Яндекс Диска...")
            self.y.download(self.remote_path, self.local_file)

            # Проверяем что файл скачался
            if os.path.exists(self.local_file):
                file_size = os.path.getsize(self.local_file)
                print("✅ Файл успешно скачан с Яндекс Диска!")
                print(f"📊 Размер: {file_size} байт")
                return True
            else:
                print("❌ Файл не скачался")
                return False

        except Exception as e:
            print(f"❌ Ошибка скачивания: {e}")
            return False

    def check_remote_file(self):
        """Проверить информацию о файле на Яндекс Диске"""
        try:
            if self.y.exists(self.remote_path):
                file_info = self.y.get_meta(self.remote_path)
                print("✅ Файл найден на Яндекс Диске:")
                print(f"📁 Путь: {self.remote_path}")
                print(f"📊 Размер: {file_info.size} байт")
                print(f"📅 Изменен: {file_info.modified}")
                return True
            else:
                print("❌ Файл не найден на Яндекс Диске")
                return False
        except Exception as e:
            print(f"❌ Ошибка проверки: {e}")
            return False


# Использование
if __name__ == "__main__":
    # Вставьте ваш токен сюда
    YOUR_TOKEN = "y0__xD89tSJBBjblgMg1fC9ihUwhJeqlwgXFM-EwH6GAbo1cJ6dfjDG4_HR0g"  # ← ВСТАВЬТЕ СКОПИРОВАННЫЙ ТОКЕН

    uploader = YandexDiskUploader(YOUR_TOKEN)

    # Проверяем подключение
    if uploader.check_connection():
        print("\n1. Проверить файл на Яндекс Диске")
        print("2. Загрузить файл на Яндекс Диск")
        print("3. Скачать файл с Яндекс Диска")

        choice = input("\nВыберите действие (1/2/3): ")

        if choice == "1":
            uploader.check_remote_file()
        elif choice == "2":
            uploader.upload_db()
        elif choice == "3":
            uploader.download_db()
        else:
            print("❌ Неверный выбор")