from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox, QMainWindow
from PyQt6.QtCore import QDate, pyqtSignal
import sqlite3
import sys

# Импортируем модули для каждого функционала
from admin.Add_Delete_sotrudnic import EmployeeManagementDialog
from admin.List_sotrudnic import EmployeeListDialog
from admin.Change_room import RoomManagementDialog
from admin.Download_Upload_data import DataExportDialog


class AdminWindow(QMainWindow):
    closed = pyqtSignal()
    def __init__(self, full_name, username):
        super().__init__()
        uic.loadUi('UI/Admin/Админ переделанный.ui', self)

        self.init_database()
        #
        # # Подключаем кнопки
        self.sort_registry_btn.clicked.connect(self.sort_registry)
        self.sort_staff_btn.clicked.connect(self.sort_staff)
        self.manage_employees_btn.clicked.connect(self.manage_employees)
        self.employees_list_btn.clicked.connect(self.show_employees_list)
        self.contact_registry_btn.clicked.connect(self.contact_registry)
        self.contact_staff_btn.clicked.connect(self.contact_staff)
        self.change_numbers_btn.clicked.connect(self.change_numbers)
        self.data_export_btn.clicked.connect(self.data_export_import)
        #
        # # Устанавливаем текущую дату
        self.current_date_label.setText(QDate.currentDate().toString("dd.MM.yyyy"))
        #
        # # Загружаем данные сотрудников
        self.load_employees_data()
        #
        # # Модель для списка сообщений
        # self.model = QtWidgets.QStringListModel()
        # self.listView.setModel(self.model)

    def init_database(self):
        """Инициализация базы данных"""
        try:
            self.conn = sqlite3.connect('Hotel_bd.db')
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось подключиться к базе данных: {str(e)}")

    def load_employees_data(self):
        """Загрузка данных сотрудников для отображения в главном окне"""
        try:
            # Загружаем администраторов и регистраторов
            self.cursor.execute("""
                SELECT first_name, last_name, patronymic 
                FROM staff 
                WHERE position IN ('администратор', 'регистратор')
                LIMIT 3
            """)
            registry_employees = self.cursor.fetchall()

            # Загружаем обслуживающий персонал
            self.cursor.execute("""
                SELECT first_name, last_name, patronymic 
                FROM staff 
                WHERE position = 'обслуживающий персонал'
                LIMIT 3
            """)
            staff_employees = self.cursor.fetchall()

            # Обновляем отображение регистратуры
            registry_labels = [self.label_5, self.label_7, self.label_10]
            for i, label in enumerate(registry_labels):
                if i < len(registry_employees):
                    first_name, last_name, patronymic = registry_employees[i]
                    full_name = f"{last_name} {first_name[0]}."
                    if patronymic:
                        full_name += f"{patronymic[0]}."
                    label.setText(full_name)
                else:
                    label.setText("")

            # Обновляем отображение персонала
            staff_labels = [self.label_6, self.label_8, self.label_9]
            for i, label in enumerate(staff_labels):
                if i < len(staff_employees):
                    first_name, last_name, patronymic = staff_employees[i]
                    full_name = f"{last_name} {first_name[0]}."
                    if patronymic:
                        full_name += f"{patronymic[0]}."
                    label.setText(full_name)
                else:
                    label.setText("")

        except sqlite3.Error as e:
            print(f"Ошибка загрузки данных сотрудников: {e}")

    def add_message(self, message):
        """Добавление сообщения в список"""
        current_list = self.model.stringList()
        current_list.append(f"{QDate.currentDate().toString('dd.MM.yyyy')} - {message}")
        self.model.setStringList(current_list)
        self.listView.scrollToBottom()

    def sort_registry(self):
        """Сортировка регистратуры"""
        try:
            self.add_message("✅ Регистратура отсортирована")
            QMessageBox.information(self, "Успех", "Регистратура успешно отсортирована!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сортировке: {str(e)}")

    def sort_staff(self):
        """Сортировка персонала"""
        try:
            self.add_message("✅ Персонал отсортирован")
            QMessageBox.information(self, "Успех", "Персонал успешно отсортирован!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сортировке: {str(e)}")

    def manage_employees(self):
        """Управление сотрудниками"""
        try:
            dialog = EmployeeManagementDialog(self)
            dialog.exec()
            # Обновляем данные после закрытия диалога
            self.load_employees_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия управления сотрудниками: {str(e)}")

    def show_employees_list(self):
        """Показать список работников"""
        try:
            dialog = EmployeeListDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия списка сотрудников: {str(e)}")

    def contact_registry(self):
        """Связь с регистратурой"""
        try:
            self.cursor.execute("""
                SELECT id, first_name, last_name 
                FROM staff 
                WHERE position IN ('администратор', 'регистратор')
            """)
            employees = self.cursor.fetchall()

            if not employees:
                QMessageBox.warning(self, "Ошибка", "Нет сотрудников в регистратуре!")
                return

            employee_names = [f"{last_name} {first_name}" for id, first_name, last_name in employees]
            employee, ok = QtWidgets.QInputDialog.getItem(
                self, "Связь с регистратурой", "Выберите сотрудника:", employee_names, 0, False
            )

            if ok and employee:
                # Добавляем сообщение в БД
                employee_id = next(id for id, first_name, last_name in employees
                                   if f"{last_name} {first_name}" == employee)
                self.cursor.execute('''
                    INSERT INTO messages (from_user, to_user, text, is_read)
                    VALUES (?, ?, ?, ?)
                ''', (1, employee_id, f"Связь с регистратурой: {employee}", 0))
                self.conn.commit()

                self.add_message(f"📞 Связь с регистратурой: {employee}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка связи с регистратурой: {str(e)}")

    def contact_staff(self):
        """Связь с персоналом"""
        try:
            self.cursor.execute("""
                SELECT id, first_name, last_name 
                FROM staff 
                WHERE position = 'обслуживающий персонал'
            """)
            employees = self.cursor.fetchall()

            if not employees:
                QMessageBox.warning(self, "Ошибка", "Нет сотрудников в персонале!")
                return

            employee_names = [f"{last_name} {first_name}" for id, first_name, last_name in employees]
            employee, ok = QtWidgets.QInputDialog.getItem(
                self, "Связь с персоналом", "Выберите сотрудника:", employee_names, 0, False
            )

            if ok and employee:
                # Добавляем сообщение в БД
                employee_id = next(id for id, first_name, last_name in employees
                                   if f"{last_name} {first_name}" == employee)
                self.cursor.execute('''
                    INSERT INTO messages (from_user, to_user, text, is_read)
                    VALUES (?, ?, ?, ?)
                ''', (1, employee_id, f"Связь с персоналом: {employee}", 0))
                self.conn.commit()

                self.add_message(f"📞 Связь с персоналом: {employee}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка связи с персоналом: {str(e)}")

    def change_numbers(self):
        """Изменение номеров"""
        try:
            dialog = RoomManagementDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия управления номерами: {str(e)}")

    def data_export_import(self):
        """Выгрузка/загрузка данных"""
        try:
            dialog = DataExportDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия экспорта данных: {str(e)}")

    def closeEvent(self, event):
        """Закрытие соединения с БД при закрытии приложения"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass
        event.accept()


# if __name__ == "__main__":
#     app = QtWidgets.QApplication(sys.argv)
#     window = AdminWindow("Ars","Admin")
#     window.show()
#     sys.exit(app.exec())