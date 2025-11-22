from datetime import datetime

from PyQt6.QtWidgets import QMainWindow, QListWidgetItem, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6 import uic, QtCore
import sqlite3

from massage_window import MassageWindow
from utils import get_resource_path
from staff.BD_staff import UploadCleaningWindow

from notifications_manager import SimpleNotificationsManager

class TaskAssignmentError(Exception):
    pass

class NoTaskSelectedError(Exception):
    pass

class NoUnassignedTasksError(Exception):
    pass

class TaskAlreadyAssignedError(Exception):
    pass

class StaffWindow(QMainWindow):
    closed = pyqtSignal()
    task_completed = pyqtSignal()

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
            self
        )
        self.transfer_button.clicked.connect(self.assign_tasks_to_current_user)
        self.contact_button.clicked.connect(self.open_massage)
        self.complete_all_button.clicked.connect(self.task_completion)
        self.refresh_button.clicked.connect(self.load_unassigned_tasks)

        self.last_unassigned_count = 0
        self.setup_tasks_monitoring()

        self.showMaximized()
        self.load_unassigned_tasks()
        self.load_user_tasks()

    def setup_tasks_monitoring(self):
        """Настройка мониторинга изменений в задачах"""
        self.unassigned_tasks_timer = QtCore.QTimer()
        self.unassigned_tasks_timer.timeout.connect(self.check_unassigned_tasks_updates)
        self.unassigned_tasks_timer.start(15000)

    def check_unassigned_tasks_updates(self):
        """Проверяет, изменилось ли количество неназначенных задач"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) FROM maintenance_tasks 
                WHERE assigned_to IS NULL OR assigned_to = ''
            ''')

            current_count = cursor.fetchone()[0]
            conn.close()

            if current_count != self.last_unassigned_count:
                self.last_unassigned_count = current_count
                self.load_unassigned_tasks()

        except Exception as e:
            print(f"Ошибка проверки неназначенных задач: {e}")

    def open_massage(self):
        self.massage_window = MassageWindow(full_name=self.full_name)
        self.massage_window.show()

    def get_current_user_id(self):
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
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 
                    mt.id,
                    mt.room_number,
                    mt.description,
                    mt.status,
                    mt.created_at,
                    mt.notes,
                    creator.first_name || ' ' || creator.last_name as created_by_name,
                    creator.position as creator_position
                FROM maintenance_tasks mt
                LEFT JOIN staff creator ON mt.created_by = creator.id
                WHERE mt.assigned_to IS NULL OR mt.assigned_to = ''
                ORDER BY mt.created_at DESC
            ''')

            unassigned_tasks = cursor.fetchall()
            self.all_tasks_list.clear()

            for task in unassigned_tasks:
                task_id, room_number, description, status, created_at, notes, created_by_name, creator_position = task

                try:
                    if isinstance(created_at, str):
                        created_date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
                    else:
                        created_date = created_at.strftime('%d.%m.%Y %H:%M')
                except:
                    created_date = str(created_at)

                task_text = f"""🏠 Комната: {room_number}
    📋 Задача: {description}
    👤 Создал: {created_by_name} ({creator_position})
    📅 Создана: {created_date}
    🔄 Статус: {status}"""

                if notes and notes.strip() and notes != 'Нет примечаний':
                    task_text += f"\n💬 Примечания: {notes}"

                list_item = QListWidgetItem(task_text)
                list_item.setCheckState(Qt.CheckState.Unchecked)
                list_item.setData(1, task_id)
                list_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)

                self.all_tasks_list.addItem(list_item)

            conn.close()

            print(f"Загружено неназначенных задач: {len(unassigned_tasks)}")

        except sqlite3.Error as e:
            print(f"Ошибка загрузки неназначенных задач: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке задач: {e}")



    def load_user_tasks(self):
        try:
            if not self.current_user_id:
                return

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 
                    mt.id,
                    mt.room_number,
                    mt.description,
                    mt.status,
                    mt.created_at,
                    mt.notes,
                    creator.first_name || ' ' || creator.last_name as created_by_name,
                    creator.position as creator_position
                FROM maintenance_tasks mt
                LEFT JOIN staff creator ON mt.created_by = creator.id
                WHERE mt.assigned_to = ? AND status = 'в работе'
                ORDER BY mt.created_at DESC
            ''', (self.current_user_id,))

            user_tasks = cursor.fetchall()

            self.accepted_tasks_list.clear()

            for task in user_tasks:
                task_id, room_number, description, status, created_at, notes, created_by_name, creator_position = task

                try:
                    if isinstance(created_at, str):
                        created_date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
                    else:
                        created_date = created_at.strftime('%d.%m.%Y %H:%M')
                except:
                    created_date = str(created_at)

                task_text = f"""🏠 Комната: {room_number}
    📋 Задача: {description}
    👤 Создал: {created_by_name} ({creator_position})
    📅 Создана: {created_date}
    🔄 Статус: {status}"""


                if notes and notes.strip() and notes != 'Нет примечаний':
                    task_text += f"\n💬 Примечания: {notes}"

                list_item = QListWidgetItem(task_text)
                list_item.setCheckState(Qt.CheckState.Unchecked)
                list_item.setData(1, task_id)
                list_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
                self.accepted_tasks_list.addItem(list_item)

            conn.close()
            print(f"Загружено задач пользователя: {len(user_tasks)}")

        except sqlite3.Error as e:
            print(f"Ошибка загрузки задач пользователя: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке задач пользователя: {e}")

    def task_completion(self):
        try:
            if not self.current_user_id:
                raise TaskAssignmentError("ID пользователя не определен")

            if self.accepted_tasks_list.count() == 0:
                raise NoUnassignedTasksError("Нет доступных задач для выполнения")

            self.complete_tasks = []
            for i in range(self.accepted_tasks_list.count()):
                item = self.accepted_tasks_list.item(i)
                if (item.checkState() == Qt.CheckState.Checked):
                    task_id = item.data(1)
                    self.complete_tasks.append(task_id)

            if not self.complete_tasks:
                raise NoTaskSelectedError("Не выполнено ни одной задачи")

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            for task_id in self.complete_tasks:
                cursor.execute('''
                                    UPDATE maintenance_tasks 
                                    SET status = 'убрано'
                                    WHERE id = ?
                                ''', (task_id,))
            conn.commit()
            conn.close()

            self.task_completed.emit()

            self.load_unassigned_tasks()
            self.load_user_tasks()

            QMessageBox.information(self, "Успех", 'Задача успешно выполнена')

        except NoTaskSelectedError as e:
            QMessageBox.warning(self, "Ошибка выбора", str(e))

        except NoUnassignedTasksError as e:
            QMessageBox.information(self, "Нет задач", str(e))

        except TaskAlreadyAssignedError as e:
            QMessageBox.critical(self, "Задача занята", str(e))

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка базы данных")

        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Произошла непредвиденная ошибка: {str(e)}")


    def assign_tasks_to_current_user(self):
        try:
            if not self.current_user_id:
                raise TaskAssignmentError("ID пользователя не определен")

            if self.all_tasks_list.count() == 0:
                raise NoUnassignedTasksError("Нет доступных задач для назначения")

            selected_tasks = []
            for i in range(self.all_tasks_list.count()):
                item = self.all_tasks_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    task_id = item.data(1)
                    selected_tasks.append(task_id)

            if not selected_tasks:
                raise NoTaskSelectedError("Не выбрано ни одной задачи")

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()


            for task_id in selected_tasks:
                cursor.execute('SELECT assigned_to FROM maintenance_tasks WHERE id = ?', (task_id,))
                result = cursor.fetchone()
                if result and result[0] is not None and result[0] != '':
                    raise TaskAlreadyAssignedError(f"Задача ID {task_id} уже назначена другому сотруднику")


            for task_id in selected_tasks:
                cursor.execute('''
                    UPDATE maintenance_tasks 
                    SET assigned_to = ?, status = 'в работе'
                    WHERE id = ?
                ''', (self.current_user_id, task_id))

            conn.commit()
            conn.close()



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
            QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка базы данных")
        except Exception as e:
            QMessageBox.critical(self, "Неизвестная ошибка", f"Произошла непредвиденная ошибка: {str(e)}")

    def open_upload(self):

        self.upload_window = UploadCleaningWindow()
        self.upload_window.show()


    def closeEvent(self, event):
        """Останавливаем таймеры при закрытии окна"""
        if hasattr(self, 'unassigned_tasks_timer'):
            self.unassigned_tasks_timer.stop()
        if hasattr(self, 'notifications_manager'):
            self.notifications_manager.stop_updates()
        self.closed.emit()
        event.accept()