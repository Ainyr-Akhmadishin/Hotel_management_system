# utils.py
import sys
import os


def get_resource_path(relative_path):
    """
    Получить абсолютный путь к ресурсу.
    Работает для разработки и для PyInstaller.
    """
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)