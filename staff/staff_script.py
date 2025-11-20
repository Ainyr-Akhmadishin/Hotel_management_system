from PyQt6.QtWidgets import QMainWindow, QListWidgetItem, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6 import uic
import sqlite3

from massage_window import MassageWindow
from utils import get_resource_path
from staff.BD_staff import UploadCleaningWindow

from notifications_manager import SimpleNotificationsManager

class TaskAssignmentError(Exception):
    """Базовое исключение для ошибок назначения задач"""
    pass

class NoTaskSelectedError(Exception):
    """Исключение при отсутствии выбранных задач"""
    pass

class NoUnassignedTasksError(Exception):
    """Исключение когда список неназначенных задач пуст"""
    pass

class TaskAlreadyAssignedError(Exception):
    """Исключение когда задача уже назначена другому пользователю"""
    pass

class StaffWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(self, full_name, username):
        super().__init__()
        self.full_name = full_name
        self.username = username

        uic.loadUi('UI/Staff/Окно обслуживающего персонала.ui', self)
        self.setWindowTitle(f"Персонал - {self.full_name}")
        self.upload_button.clicked.connect(self.open_upload)
        self.current_user_id = None
        self.get_current_user_id()
        self.notifications_manager = SimpleNotificationsManager(
            self.current_user_id,
            self.notifications_frame,
            self  # передаем ссылку на главное окно
        )
        self.transfer_button.clicked.connect(self.assign_tasks_to_current_user)
        self.contact_button.clicked.connect(self.open_massage)

        # Получаем ID текущего пользователя и загружаем задачи
        self.load_unassigned_tasks()
        self.load_user_tasks()

    def open_massage(self):
        self.massage_window = MassageWindow(full_name=self.full_name)
        self.massage_window.show()

    def get_current_user_id(self):
        """Получаем ID текущего пользователя по username"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM staff WHERE login = ?', (self.username,))
            result = cursor.fetchone()
            if result:
                self.current_user_id = result[0]
                print(f"ID текущего пользователя: {self.current_user_id}")
            conn.close()
        except sqlite3.Error as e:
            print(f"Ошибка получения ID пользователя: {e}")

    def load_unassigned_tasks(self):
        """Загрузка неназначенных задач в список all_tasks_list с чекбоксами"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # SQL запрос для получения неназначенных задач
            cursor.execute('''
                SELECT id, room_number, description, status, created_at
                FROM maintenance_tasks 
                WHERE assigned_to IS NULL OR assigned_to = ''
                ORDER BY created_at DESC
            ''')

            unassigned_tasks = cursor.fetchall()

            # Очищаем список перед загрузкой новых данных
            self.all_tasks_list.clear()

            # Добавляем задачи в список с чекбоксами
            for task in unassigned_tasks:
                task_id, room_number, description, status, created_at = task

                # Форматируем текст для отображения
                task_text = f"Комната {room_number}: {description}"
                if len(task_text) > 80:  # Ограничиваем длину описания
                    task_text = task_text[:77] + "..."

                # Создаем элемент списка с чекбоксом
                list_item = QListWidgetItem(task_text)
                list_item.setCheckState(Qt.CheckState.Unchecked)  # По умолчанию не отмечено
                list_item.setData(1, task_id)  # Сохраняем ID задачи

                # Добавляем в список
                self.all_tasks_list.addItem(list_item)

            conn.close()

            print(f"Загружено неназначенных задач: {len(unassigned_tasks)}")

        except sqlite3.Error as e:
            print(f"Ошибка загрузки неназначенных задач: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке задач: {e}")

    def load_user_tasks(self):
        """Загрузка задач текущего пользователя в список accepted_tasks_list"""
        try:
            if not self.current_user_id:
                return

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # SQL запрос для получения задач текущего пользователя
            cursor.execute('''
                SELECT id, room_number, description, status, created_at
                FROM maintenance_tasks 
                WHERE assigned_to = ?
                ORDER BY created_at DESC
            ''', (self.current_user_id,))

            user_tasks = cursor.fetchall()

            # Очищаем список перед загрузкой новых данных
            self.accepted_tasks_list.clear()

            # Добавляем задачи в список
            for task in user_tasks:
                task_id, room_number, description, status, created_at = task

                # Форматируем текст для отображения
                task_text = f"Комната {room_number}: {description}"
                if len(task_text) > 80:  # Ограничиваем длину описания
                    task_text = task_text[:77] + "..."

                # Создаем элемент списка
                list_item = QListWidgetItem(task_text)
                list_item.setData(1, task_id)  # Сохраняем ID задачи

                # Добавляем в список
                self.accepted_tasks_list.addItem(list_item)

            conn.close()

            print(f"Загружено задач пользователя: {len(user_tasks)}")

        except sqlite3.Error as e:
            print(f"Ошибка загрузки задач пользователя: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке задач пользователя: {e}")

    def assign_tasks_to_current_user(self):
        """Назначение выбранных задач текущему пользователю с проверками"""
        try:
            if not self.current_user_id:
                raise TaskAssignmentError("ID пользователя не определен")

            # Проверяем есть ли вообще неназначенные задачи
            if self.all_tasks_list.count() == 0:
                raise NoUnassignedTasksError("Нет доступных задач для назначения")

            # Получаем выбранные задачи
            selected_tasks = []
            for i in range(self.all_tasks_list.count()):
                item = self.all_tasks_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    task_id = item.data(1)
                    selected_tasks.append(task_id)

            # Проверяем выбраны ли задачи
            if not selected_tasks:
                raise NoTaskSelectedError("Не выбрано ни одной задачи")

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Проверяем не заняты ли выбранные задачи другими пользователями
            for task_id in selected_tasks:
                cursor.execute('SELECT assigned_to FROM maintenance_tasks WHERE id = ?', (task_id,))
                result = cursor.fetchone()
                if result and result[0] is not None and result[0] != '':
                    raise TaskAlreadyAssignedError(f"Задача ID {task_id} уже назначена другому сотруднику")

            # Обновляем задачи в базе данных
            for task_id in selected_tasks:
                cursor.execute('''
                    UPDATE maintenance_tasks 
                    SET assigned_to = ?, status = 'в работе'
                    WHERE id = ?
                ''', (self.current_user_id, task_id))

            conn.commit()
            conn.close()

            print(f"Назначено задач пользователю: {len(selected_tasks)}")

            # Обновляем списки задач
            self.load_unassigned_tasks()
            self.load_user_tasks()

        except NoTaskSelectedError as e:
            QMessageBox.warning(self, "Ошибка выбора", str(e))
        except NoUnassignedTasksError as e:
            QMessageBox.information(self, "Нет задач", str(e))
        except TaskAlreadyAssignedError as e:
            QMessageBox.critical(self, "Задача занята", str(e))
        except TaskAssignmentError as e:
            QMessageBox.critical(self, "Ошибка назначения", str(e))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка базы данных: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Произошла непредвиденная ошибка: {str(e)}")

    def open_upload(self):

        self.upload_window = UploadCleaningWindow()
        self.upload_window.show()


    def closeEvent(self, event):
        self.closed.emit()
        event.accept()