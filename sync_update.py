# simple_auto_sync.py
import time
import threading
import os
from bd_manager import YandexDiskUploader


class SimpleAutoSync:
    def __init__(self, token):
        self.uploader = YandexDiskUploader(token)
        self.local_file = "Hotel_bd.db"
        self.is_running = False

    def need_download(self):
        """Нужно ли скачивать новую версию?"""
        # Если локального файла нет - скачиваем
        if not os.path.exists(self.local_file):
            return True

        try:
            # Проверяем есть ли файл на Яндекс Диске
            if not self.uploader.y.exists(self.uploader.remote_path):
                return False

            # Получаем информацию об удаленном файле
            remote_info = self.uploader.y.get_meta(self.uploader.remote_path)
            remote_modified = remote_info.modified.timestamp()
            remote_size = remote_info.size

            # Локальная информация
            local_modified = os.path.getmtime(self.local_file)
            local_size = os.path.getsize(self.local_file)

            # Скачиваем если удаленный файл новее или другого размера
            return (remote_modified > local_modified or
                    remote_size != local_size)

        except:
            return False

    def sync_loop(self):
        """Основной цикл синхронизации - только скачивание"""
        while self.is_running:
            try:
                # Проверяем нужно ли скачать с Яндекс Диска
                if self.need_download():
                    print("Обнаружены изменения на Яндекс Диске, скачиваем...")
                    self.uploader.download_db()  # Просто скачиваем

            except Exception as e:
                print(f"Ошибка синхронизации: {e}")

            time.sleep(5)  # Проверяем каждые 5 секунд

    def start(self):
        """Запустить автоматическую синхронизацию"""
        if not self.uploader.check_connection():
            print("Не удалось подключиться к Яндекс Диску")
            return False

        self.is_running = True
        thread = threading.Thread(target=self.sync_loop, daemon=True)
        thread.start()
        print("Автоскачивание запущено (проверка каждые 5 секунд)")
        return True

    def stop(self):
        """Остановить синхронизацию"""
        self.is_running = False
        print("Синхронизация остановлена")