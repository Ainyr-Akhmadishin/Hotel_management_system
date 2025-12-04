# utils.py
import os
import sys
import shutil


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    full_path = os.path.join(base_path, relative_path)

    return full_path


def get_database_path():

    if not getattr(sys, 'frozen', False):
        return 'Hotel_bd.db'

    app_data_dir = os.path.join(os.environ['APPDATA'], 'HotelSystem')
    os.makedirs(app_data_dir, exist_ok=True)

    user_db_path = os.path.join(app_data_dir, 'Hotel_bd.db')

    if os.path.exists(user_db_path):
        return user_db_path

    try:
        source_db = os.path.join(sys._MEIPASS, 'Hotel_bd.db')
        if os.path.exists(source_db):
            shutil.copy2(source_db, user_db_path)
            print(f"Database copied to: {user_db_path}")
        else:
            import sqlite3
            conn = sqlite3.connect(user_db_path)
            conn.close()
            print(f"New database created at: {user_db_path}")
    except Exception as e:
        print(f"Error setting up database: {e}")

    return user_db_path