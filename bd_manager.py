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

        try:
            if self.y.check_token():
                print("Подключение к Яндекс Диску установлено")
                return True
            else:
                print("Не удалось подключиться к Яндекс Диску")
                return False
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def upload_db(self):

        try:

            if not os.path.exists(self.local_file):
                print(f"Файл {self.local_file} не найден")
                return False


            if not self.y.exists("/HotelApp"):
                self.y.mkdir("/HotelApp")
                print("Создана папка /HotelApp на Яндекс Диске")


            print("Загрузка файла на Яндекс Диск...")
            self.y.upload(self.local_file, self.remote_path, overwrite=True)

            print("Файл успешно загружен на Яндекс Диск!")
            print(f"Путь: {self.remote_path}")
            return True

        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return False

    def download_db(self):
        try:

            if not self.y.exists(self.remote_path):
                print("Файл не найден на Яндекс Диске")
                return False

            # Скачиваем файл (работает в любом случае)
            print("Скачивание файла с Яндекс Диска...")
            self.y.download(self.remote_path, self.local_file, overwrite=True)


            if os.path.exists(self.local_file):
                file_size = os.path.getsize(self.local_file)
                print("Файл успешно скачан с Яндекс Диска!")
                print(f"Размер: {file_size} байт")
                return True
            else:
                print("Файл не скачался")
                return False


        except Exception as e:
            print(f"Ошибка скачивания: {e}")
            return False

    def check_remote_file(self):

        try:
            if self.y.exists(self.remote_path):
                file_info = self.y.get_meta(self.remote_path)
                print("Файл найден на Яндекс Диске:")
                print(f"Путь: {self.remote_path}")
                print(f"Размер: {file_info.size} байт")
                print(f"Изменен: {file_info.modified}")
                return True
            else:
                print("Файл не найден на Яндекс Диске")
                return False
        except Exception as e:
            print(f"Ошибка проверки: {e}")
            return False


# # Использование
# if __name__ == "__main__":
#     # Вставьте ваш токен сюда
#     YOUR_TOKEN = "y0__xD89tSJBBjblgMg1fC9ihUwhJeqlwgXFM-EwH6GAbo1cJ6dfjDG4_HR0g"  # ← ВСТАВЬТЕ СКОПИРОВАННЫЙ ТОКЕН
#
#     uploader = YandexDiskUploader(YOUR_TOKEN)
#
#     # Проверяем подключение
#     if uploader.check_connection():
#         print("\n1. Проверить файл на Яндекс Диске")
#         print("2. Загрузить файл на Яндекс Диск")
#         print("3. Скачать файл с Яндекс Диска")
#
#         choice = input("\nВыберите действие (1/2/3): ")
#
#         if choice == "1":
#             uploader.check_remote_file()
#         elif choice == "2":
#             uploader.upload_db()
#         elif choice == "3":
#             uploader.download_db()
#         else:
#             print("❌ Неверный выбор")

# # simple_auto_sync.py
# import yadisk
# import os
# import hashlib
# import time
# import threading
#
#
# class SimpleAutoSync:
#     def __init__(self, token):
#         self.y = yadisk.YaDisk(token=token)
#         self.remote_path = "/HotelApp/Hotel_bd.db"
#         self.local_file = "Hotel_bd.db"
#         self.is_running = False
#
#     def get_file_hash(self, filepath):
#         if not os.path.exists(filepath):
#             return None
#         with open(filepath, 'rb') as f:
#             return hashlib.md5(f.read()).hexdigest()
#
#     def sync_loop(self):
#         """Основной цикл синхронизации"""
#         last_local_hash = self.get_file_hash(self.local_file)
#
#         while self.is_running:
#             try:
#                 # Проверяем локальные изменения
#                 current_hash = self.get_file_hash(self.local_file)
#                 if current_hash and current_hash != last_local_hash:
#                     print("🔄 Обнаружены изменения, загружаем на Яндекс Диск...")
#                     self.y.upload(self.local_file, self.remote_path, overwrite=True)
#                     print("✅ Загружено на Яндекс Диск")
#                     last_local_hash = current_hash
#
#             except Exception as e:
#                 print(f"❌ Ошибка синхронизации: {e}")
#
#             time.sleep(5)  # Ждем 5 секунд
#
#     def start(self):
#         """Запустить автоматическую синхронизацию"""
#         self.is_running = True
#         thread = threading.Thread(target=self.sync_loop, daemon=True)
#         thread.start()
#         print("🔁 Автосинхронизация запущена (каждые 5 секунд)")
#
#     def stop(self):
#         """Остановить синхронизацию"""
#         self.is_running = False
#         print("⏹️  Синхронизация остановлена")
#
#
# # Использование в вашем приложении
# if __name__ == "__main__":
#     YOUR_TOKEN = "ваш_токен_здесь"
#
#     # Создаем синхронизатор
#     auto_sync = SimpleAutoSync(YOUR_TOKEN)
#
#     # Запускаем фоновую синхронизацию
#     auto_sync.start()
#
#     # Ваш основной код приложения продолжает работать
#     print("📊 Ваше приложение работает...")
#
#     # Для демонстрации - ждем некоторое время
#     input("Нажмите Enter чтобы остановить синхронизацию...")
#     auto_sync.stop()