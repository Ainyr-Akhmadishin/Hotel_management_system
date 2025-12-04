import sqlite3
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, QHeaderView, QPushButton, QMessageBox,
                             QHBoxLayout, QTabWidget, QMenu, QLabel, QDialog,
                             QDialogButtonBox, QFormLayout, QLineEdit, QComboBox, QInputDialog)
from PyQt6.QtCore import Qt
from datetime import datetime


class DeleteConfirmationDialog(QDialog):
    """Диалог подтверждения удаления с дополнительными опциями"""

    def __init__(self, table_name, records_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подтверждение удаления")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Информационное сообщение
        info_label = QLabel(
            f"Вы уверены, что хотите удалить {records_count} записей из таблицы '{table_name}'?"
        )
        layout.addWidget(info_label)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes |
            QDialogButtonBox.StandardButton.No |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)


class AdvancedDeleteDialog(QDialog):
    """Расширенный диалог для сложных условий удаления"""

    def __init__(self, table_name, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Расширенное удаление - {table_name}")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Поля для условий WHERE
        form_layout = QFormLayout()
        self.condition_widgets = {}

        for column in columns:
            if column.lower() not in ['id', 'created_at', 'updated_at']:  # Исключаем служебные поля
                condition_combo = QComboBox()
                condition_combo.addItems(["=", "!=", ">", "<", "LIKE", "IN", "IS NULL"])
                value_edit = QLineEdit()
                value_edit.setPlaceholderText(f"Значение для {column}")

                self.condition_widgets[column] = (condition_combo, value_edit)
                form_layout.addRow(f"{column}:", condition_combo)
                form_layout.addRow("Значение:", value_edit)

        layout.addLayout(form_layout)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def get_conditions(self):
        """Получить условия для WHERE"""
        conditions = []
        params = []

        for column, (combo, edit) in self.condition_widgets.items():
            operator = combo.currentText()
            value = edit.text().strip()

            if value:
                if operator == "LIKE":
                    conditions.append(f"{column} LIKE ?")
                    params.append(f"%{value}%")
                elif operator == "IN":
                    values = [v.strip() for v in value.split(',')]
                    placeholders = ','.join(['?' for _ in values])
                    conditions.append(f"{column} IN ({placeholders})")
                    params.extend(values)
                else:
                    conditions.append(f"{column} {operator} ?")
                    params.append(value)
            elif operator == "IS NULL":
                conditions.append(f"{column} IS NULL")

        return " AND ".join(conditions), params


class HotelManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление отелем - Просмотр всех таблиц")
        self.setGeometry(100, 100, 1400, 800)

        self.init_ui()
        self.load_all_tables()

    def init_ui(self):
        """Инициализация интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Заголовок с информацией о БД
        self.db_info_label = QLabel("База данных: Hotel_bd.db")
        self.db_info_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(self.db_info_label)

        # Создаем вкладки для каждой таблицы
        self.tabs = QTabWidget()

        # Создаем вкладки для всех таблиц
        self.tables_info = {
            'staff': "Сотрудники",
            'rooms': "Номера",
            'guests': "Гости",
            'bookings': "Бронирования",
            'messages': "Сообщения",
            'maintenance_tasks': "Задания на уборку"
        }

        self.table_widgets = {}

        for table_name, display_name in self.tables_info.items():
            tab = QWidget()
            layout_tab = QVBoxLayout(tab)

            # Создаем таблицу для этой вкладки
            table_widget = QTableWidget()
            table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table_widget.customContextMenuRequested.connect(
                lambda pos, tn=table_name: self.show_context_menu(pos, tn))
            layout_tab.addWidget(table_widget)

            self.tabs.addTab(tab, display_name)
            self.table_widgets[table_name] = table_widget

        # Панель кнопок УДАЛЕНИЯ
        delete_button_layout = QHBoxLayout()

        self.delete_selected_btn = QPushButton("🗑️ Удалить выбранные записи")
        self.delete_selected_btn.clicked.connect(self.delete_selected_rows)
        self.delete_selected_btn.setStyleSheet("background-color: #ff6b6b; color: white;")

        self.delete_advanced_btn = QPushButton("🔍 Расширенное удаление")
        self.delete_advanced_btn.clicked.connect(self.advanced_delete)
        self.delete_advanced_btn.setStyleSheet("background-color: #ff8e53; color: white;")

        self.delete_all_btn = QPushButton("💥 Очистить таблицу")
        self.delete_all_btn.clicked.connect(self.delete_all_records)
        self.delete_all_btn.setStyleSheet("background-color: #dc3545; color: white;")

        delete_button_layout.addWidget(self.delete_selected_btn)
        delete_button_layout.addWidget(self.delete_advanced_btn)
        delete_button_layout.addWidget(self.delete_all_btn)
        delete_button_layout.addStretch()

        # Панель остальных кнопок
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Обновить все таблицы")
        self.refresh_btn.clicked.connect(self.load_all_tables)

        self.structure_btn = QPushButton("📊 Показать структуру БД")
        self.structure_btn.clicked.connect(self.show_database_structure)

        self.tasks_stats_btn = QPushButton("📈 Статистика заданий")
        self.tasks_stats_btn.clicked.connect(self.show_tasks_statistics)
        self.tasks_stats_btn.setStyleSheet("background-color: #4CAF50; color: white;")

        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.structure_btn)
        button_layout.addWidget(self.tasks_stats_btn)
        button_layout.addStretch()

        layout.addWidget(self.tabs)
        layout.addLayout(button_layout)
        layout.addLayout(delete_button_layout)  # Кнопки удаления отдельно

        # Настраиваем таблицы
        self.setup_tables()

    def setup_tables(self):
        """Настройка всех таблиц"""
        for table_widget in self.table_widgets.values():
            table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table_widget.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
            table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def show_context_menu(self, position, table_name):
        """Показать контекстное меню для таблицы с доп. функциями удаления"""
        try:
            table_widget = self.table_widgets[table_name]
            selected_rows = table_widget.selectionModel().selectedRows()

            context_menu = QMenu(self)

            # Основные действия
            delete_action = context_menu.addAction("🗑️ Удалить выбранные записи")
            view_action = context_menu.addAction("👁️ Просмотреть запись")
            refresh_action = context_menu.addAction("🔄 Обновить таблицу")

            # Дополнительные действия удаления
            context_menu.addSeparator()
            advanced_delete_action = context_menu.addAction("🔍 Расширенное удаление...")
            delete_duplicates_action = context_menu.addAction("♻️ Удалить дубликаты")

            # Опасные действия
            context_menu.addSeparator()
            clear_table_action = context_menu.addAction("💥 Очистить всю таблицу")

            # Действия для таблицы заданий
            if table_name == 'maintenance_tasks':
                context_menu.addSeparator()
                change_status_action = context_menu.addAction("🔄 Изменить статус задания")
                assign_staff_action = context_menu.addAction("👨‍💼 Назначить сотрудника")

            action = context_menu.exec(table_widget.viewport().mapToGlobal(position))

            if action == delete_action:
                self.delete_selected_rows(table_name)
            elif action == view_action:
                self.view_selected_record(table_name)
            elif action == refresh_action:
                self.load_table_data_direct(table_name)
            elif action == advanced_delete_action:
                self.advanced_delete(table_name)
            elif action == delete_duplicates_action:
                self.delete_duplicates(table_name)
            elif action == clear_table_action:
                self.delete_all_records(table_name)
            elif table_name == 'maintenance_tasks' and action == change_status_action:
                self.change_task_status()
            elif table_name == 'maintenance_tasks' and action == assign_staff_action:
                self.assign_staff_to_task()

        except Exception as e:
            print(f"Ошибка в контекстном меню: {e}")

    def delete_selected_rows(self, table_name=None):
        """Удалить выбранные строки из таблицы"""
        try:
            # Если table_name не передан, используем текущую вкладку
            if table_name is None:
                current_tab_index = self.tabs.currentIndex()
                table_name = list(self.tables_info.keys())[current_tab_index]

            # Проверяем что table_name существует
            if table_name not in self.tables_info:
                QMessageBox.critical(self, "Ошибка", f"Неизвестная таблица: {table_name}")
                return

            table_widget = self.table_widgets[table_name]
            selected_rows = table_widget.selectionModel().selectedRows()

            if not selected_rows:
                QMessageBox.warning(self, "Внимание", "Выберите записи для удаления")
                return

            # Подтверждение удаления
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Вы уверены, что хотите удалить {len(selected_rows)} записей из таблицы '{self.tables_info[table_name]}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.perform_deletion(table_name, selected_rows, table_widget)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неожиданная ошибка:\n{str(e)}")
            print(f"Ошибка в delete_selected_rows: {e}")

    def perform_deletion(self, table_name, selected_rows, table_widget):
        """Выполнить удаление записей с улучшенной обработкой"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем информацию о внешних ключах
            cursor.execute("PRAGMA foreign_keys = ON")  # Включаем проверку внешних ключей

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            primary_keys = [col[1] for col in columns_info if col[5] > 0]

            deleted_count = 0
            errors = []
            skipped_due_constraints = []

            for model_index in selected_rows:
                row = model_index.row()

                # Формируем условие WHERE для удаления
                where_conditions = []
                params = []

                # Сначала пытаемся использовать первичные ключи
                for col in range(table_widget.columnCount()):
                    column_name = table_widget.horizontalHeaderItem(col).text()
                    item = table_widget.item(row, col)
                    if item and item.text() and column_name in primary_keys:
                        where_conditions.append(f"{column_name} = ?")
                        params.append(item.text())

                # Если первичных ключей нет, используем все колонки
                if not where_conditions:
                    for col in range(table_widget.columnCount()):
                        column_name = table_widget.horizontalHeaderItem(col).text()
                        item = table_widget.item(row, col)
                        if item and item.text():
                            where_conditions.append(f"{column_name} = ?")
                            params.append(item.text())

                if where_conditions:
                    where_clause = " AND ".join(where_conditions)
                    delete_query = f"DELETE FROM {table_name} WHERE {where_clause}"

                    try:
                        cursor.execute(delete_query, params)
                        if cursor.rowcount > 0:
                            deleted_count += 1
                        else:
                            errors.append(f"Строка {row + 1}: не найдена для удаления")
                    except sqlite3.IntegrityError as e:
                        if "FOREIGN KEY constraint failed" in str(e):
                            skipped_due_constraints.append(f"Строка {row + 1}: есть связанные записи")
                        else:
                            errors.append(f"Строка {row + 1}: {str(e)}")
                    except sqlite3.Error as e:
                        errors.append(f"Строка {row + 1}: {str(e)}")

            conn.commit()
            conn.close()

            # Обновляем таблицу
            self.load_table_data_direct(table_name)

            # Показываем результат
            message = f"Удалено {deleted_count} записей из таблицы '{self.tables_info[table_name]}'"

            if skipped_due_constraints:
                message += f"\n\nПропущено из-за ограничений целостности:\n" + "\n".join(skipped_due_constraints[:3])
                if len(skipped_due_constraints) > 3:
                    message += f"\n... и еще {len(skipped_due_constraints) - 3} записей"

            if errors:
                message += f"\n\nОшибки:\n" + "\n".join(errors[:3])
                if len(errors) > 3:
                    message += f"\n... и еще {len(errors) - 3} ошибок"

            QMessageBox.information(self, "Результат удаления", message)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось удалить записи:\n{str(e)}"
            )

    def view_selected_record(self, table_name):
        """Просмотреть детали выбранной записи"""
        table_widget = self.table_widgets[table_name]
        selected_rows = table_widget.selectionModel().selectedRows()

        if not selected_rows or len(selected_rows) > 1:
            QMessageBox.warning(self, "Внимание", "Выберите одну запись для просмотра")
            return

        row = selected_rows[0].row()

        # Формируем информацию о записи
        record_info = f"📋 Таблица: {self.tables_info[table_name]}\n\n"

        for col in range(table_widget.columnCount()):
            column_name = table_widget.horizontalHeaderItem(col).text()
            item = table_widget.item(row, col)
            value = item.text() if item else "NULL"
            record_info += f"{column_name}: {value}\n"

        QMessageBox.information(self, "Просмотр записи", record_info)

    def load_table_data_direct(self, table_name):
        """Прямая загрузка данных конкретной таблицы"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            self.load_table_data(cursor, table_name)
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить таблицу:\n{str(e)}")

    def advanced_delete(self, table_name=None):
        """Расширенное удаление по условиям"""
        try:
            if table_name is None:
                current_tab_index = self.tabs.currentIndex()
                table_name = list(self.tables_info.keys())[current_tab_index]

            # Получаем колонки таблицы
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            conn.close()

            # Показываем диалог для условий
            dialog = AdvancedDeleteDialog(self.tables_info[table_name], columns, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                conditions, params = dialog.get_conditions()

                if not conditions:
                    QMessageBox.warning(self, "Внимание", "Не заданы условия для удаления")
                    return

                # Подсчет записей для удаления
                conn = sqlite3.connect('Hotel_bd.db')
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {conditions}", params)
                count = cursor.fetchone()[0]
                conn.close()

                if count == 0:
                    QMessageBox.information(self, "Информация", "Нет записей, соответствующих условиям")
                    return

                # Подтверждение
                reply = QMessageBox.question(
                    self,
                    "Подтверждение расширенного удаления",
                    f"Будет удалено {count} записей из таблицы '{self.tables_info[table_name]}' по условиям.\nПродолжить?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.perform_advanced_deletion(table_name, conditions, params)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расширенного удаления:\n{str(e)}")

    def perform_advanced_deletion(self, table_name, conditions, params):
        """Выполнить расширенное удаление"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute(f"DELETE FROM {table_name} WHERE {conditions}", params)
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            # Обновляем таблицу
            self.load_table_data_direct(table_name)

            QMessageBox.information(
                self,
                "Успех",
                f"Удалено {deleted_count} записей из таблицы '{self.tables_info[table_name]}'"
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить удаление:\n{str(e)}")

    def delete_duplicates(self, table_name=None):
        """Удаление дубликатов записей"""
        try:
            if table_name is None:
                current_tab_index = self.tabs.currentIndex()
                table_name = list(self.tables_info.keys())[current_tab_index]

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем информацию о таблице
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            primary_key = [col[1] for col in columns_info if col[5] > 0]

            if not primary_key:
                QMessageBox.warning(
                    self,
                    "Внимание",
                    f"Таблица '{self.tables_info[table_name]}' не имеет первичного ключа. Удаление дубликатов невозможно."
                )
                return

            # Создаем временную таблицу без дубликатов
            temp_table = f"temp_{table_name}"
            columns_str = ", ".join(columns)

            # Создаем временную таблицу
            cursor.execute(f"CREATE TEMPORARY TABLE {temp_table} AS SELECT DISTINCT * FROM {table_name}")

            # Подсчет удаляемых записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_before = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM {temp_table}")
            total_after = cursor.fetchone()[0]
            duplicates_count = total_before - total_after

            if duplicates_count == 0:
                QMessageBox.information(self, "Информация", "Дубликаты не найдены")
                cursor.execute(f"DROP TABLE {temp_table}")
                conn.close()
                return

            # Подтверждение удаления
            reply = QMessageBox.question(
                self,
                "Удаление дубликатов",
                f"Найдено {duplicates_count} дубликатов в таблице '{self.tables_info[table_name]}'. Удалить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Удаляем оригинальную таблицу и переименовываем временную
                cursor.execute(f"DELETE FROM {table_name}")
                cursor.execute(f"INSERT INTO {table_name} SELECT * FROM {temp_table}")
                cursor.execute(f"DROP TABLE {temp_table}")

                conn.commit()
                conn.close()

                # Обновляем таблицу
                self.load_table_data_direct(table_name)

                QMessageBox.information(
                    self,
                    "Успех",
                    f"Удалено {duplicates_count} дубликатов из таблицы '{self.tables_info[table_name]}'"
                )
            else:
                cursor.execute(f"DROP TABLE {temp_table}")
                conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления дубликатов:\n{str(e)}")

    def delete_all_records(self, table_name=None):
        """Полная очистка таблицы"""
        try:
            if table_name is None:
                current_tab_index = self.tabs.currentIndex()
                table_name = list(self.tables_info.keys())[current_tab_index]

            # Подсчет записей
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()

            if count == 0:
                QMessageBox.information(self, "Информация", "Таблица уже пуста")
                return

            # Супер-подтверждение для опасной операции
            reply = QMessageBox.warning(
                self,
                "ОПАСНАЯ ОПЕРАЦИЯ",
                f"ВЫ УДАЛЯЕТЕ ВСЕ ДАННЫЕ ИЗ ТАБЛИЦЫ '{self.tables_info[table_name]}'!\n\n"
                f"Будет удалено {count} записей. Эту операцию нельзя отменить.\n\n"
                "Для подтверждения введите 'DELETE ALL' в поле ниже:",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Дополнительная проверка
                text, ok = QInputDialog.getText(
                    self,
                    "Подтверждение",
                    "Введите 'DELETE ALL' для подтверждения:"
                )

                if ok and text.strip().upper() == "DELETE ALL":
                    conn = sqlite3.connect('Hotel_bd.db')
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {table_name}")
                    deleted_count = cursor.rowcount
                    conn.commit()
                    conn.close()

                    # Обновляем таблицу
                    self.load_table_data_direct(table_name)

                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Таблица '{self.tables_info[table_name]}' полностью очищена. Удалено {deleted_count} записей."
                    )
                else:
                    QMessageBox.information(self, "Отмена", "Операция отменена")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка очистки таблицы:\n{str(e)}")

    def change_task_status(self):
        """Изменить статус выбранного задания"""
        try:
            table_widget = self.table_widgets['maintenance_tasks']
            selected_rows = table_widget.selectionModel().selectedRows()

            if not selected_rows or len(selected_rows) > 1:
                QMessageBox.warning(self, "Внимание", "Выберите одно задание для изменения статуса")
                return

            row = selected_rows[0].row()
            task_id_item = table_widget.item(row, 0)
            current_status_item = table_widget.item(row, 5)  # Статус обычно в колонке 5

            if not task_id_item:
                QMessageBox.warning(self, "Ошибка", "Не удалось определить ID задания")
                return

            task_id = task_id_item.text()
            current_status = current_status_item.text() if current_status_item else "новая"

            # Диалог для выбора нового статуса
            statuses = ["новая", "в работе", "выполнена", "отменена"]
            new_status, ok = QInputDialog.getItem(
                self, "Изменение статуса", "Выберите новый статус:",
                statuses, statuses.index(current_status) if current_status in statuses else 0, False
            )

            if ok and new_status:
                self.update_task_status(task_id, new_status, row)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить статус:\n{str(e)}")

    def update_task_status(self, task_id, new_status, row):
        """Обновить статус задания в базе данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            completed_at = "CURRENT_TIMESTAMP" if new_status == "выполнена" else "NULL"

            cursor.execute(f'''
                UPDATE maintenance_tasks 
                SET status = ?, completed_at = {completed_at}
                WHERE id = ?
            ''', (new_status, task_id))

            conn.commit()
            conn.close()

            # Обновляем отображение в таблице
            table_widget = self.table_widgets['maintenance_tasks']
            status_item = table_widget.item(row, 5)
            if status_item:
                status_item.setText(new_status)
                # Обновляем цвет в зависимости от статуса
                self.color_task_by_status(status_item, new_status)

            QMessageBox.information(self, "Успех", f"Статус задания обновлен на: {new_status}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить статус:\n{str(e)}")

    def assign_staff_to_task(self):
        """Назначить сотрудника на задание"""
        try:
            table_widget = self.table_widgets['maintenance_tasks']
            selected_rows = table_widget.selectionModel().selectedRows()

            if not selected_rows or len(selected_rows) > 1:
                QMessageBox.warning(self, "Внимание", "Выберите одно задание для назначения сотрудника")
                return

            row = selected_rows[0].row()
            task_id_item = table_widget.item(row, 0)

            if not task_id_item:
                QMessageBox.warning(self, "Ошибка", "Не удалось определить ID задания")
                return

            task_id = task_id_item.text()

            # Получаем список сотрудников
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, first_name || ' ' || last_name FROM staff WHERE position LIKE '%обслуживаю%' OR position LIKE '%персонал%'")
            staff_members = cursor.fetchall()
            conn.close()

            if not staff_members:
                QMessageBox.warning(self, "Внимание", "Нет доступных сотрудников")
                return

            staff_names = [f"{staff[0]} - {staff[1]}" for staff in staff_members]

            staff_choice, ok = QInputDialog.getItem(
                self, "Назначение сотрудника", "Выберите сотрудника:",
                staff_names, 0, False
            )

            if ok and staff_choice:
                staff_id = staff_choice.split(' - ')[0]
                self.update_task_staff(task_id, staff_id, row)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось назначить сотрудника:\n{str(e)}")

    def update_task_staff(self, task_id, staff_id, row):
        """Обновить назначенного сотрудника в базе данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE maintenance_tasks 
                SET assigned_to = ?
                WHERE id = ?
            ''', (staff_id, task_id))

            conn.commit()

            # Получаем имя сотрудника для отображения
            cursor.execute("SELECT first_name || ' ' || last_name FROM staff WHERE id = ?", (staff_id,))
            staff_name = cursor.fetchone()[0]
            conn.close()

            # Обновляем отображение в таблице
            table_widget = self.table_widgets['maintenance_tasks']
            assigned_item = table_widget.item(row, 3)  # Колонка assigned_to
            if assigned_item:
                assigned_item.setText(staff_name)

            QMessageBox.information(self, "Успех", f"Сотрудник назначен: {staff_name}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось назначить сотрудника:\n{str(e)}")

    def color_task_by_status(self, item, status):
        """Цветовое оформление задания по статусу"""
        color_map = {
            'новая': Qt.GlobalColor.yellow,
            'в работе': Qt.GlobalColor.blue,
            'выполнена': Qt.GlobalColor.green,
            'отменена': Qt.GlobalColor.gray
        }

        if status in color_map:
            item.setBackground(color_map[status])
            # Белый текст для синего фона
            if status == 'в работе':
                item.setForeground(Qt.GlobalColor.white)
            else:
                item.setForeground(Qt.GlobalColor.black)

    def load_all_tables(self):
        """Загрузка всех таблиц из базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            for table_name in self.tables_info.keys():
                self.load_table_data(cursor, table_name)

            conn.close()
            print("✅ Все таблицы загружены")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")

    def load_table_data(self, cursor, table_name):
        """Загрузка данных конкретной таблицы"""
        try:
            # Для таблицы заданий используем JOIN для получения имен сотрудников
            if table_name == 'maintenance_tasks':
                query = '''
                    SELECT 
                        mt.id,
                        mt.room_number,
                        mt.description,
                        s1.first_name || ' ' || s1.last_name as assigned_to,
                        s2.first_name || ' ' || s2.last_name as created_by,
                        mt.status,
                        mt.created_at,
                        mt.completed_at,
                        mt.notes
                    FROM maintenance_tasks mt
                    LEFT JOIN staff s1 ON mt.assigned_to = s1.id
                    LEFT JOIN staff s2 ON mt.created_by = s2.id
                    ORDER BY mt.created_at DESC
                '''
                cursor.execute(query)
            else:
                # Для остальных таблиц обычный SELECT
                cursor.execute(f"SELECT * FROM {table_name}")

            data = cursor.fetchall()

            # Получаем названия колонок
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            # Для таблицы заданий используем понятные названия колонок
            if table_name == 'maintenance_tasks':
                column_names = [
                    'ID', 'Комната', 'Описание', 'Назначено', 'Создал',
                    'Статус', 'Создано', 'Завершено', 'Примечания'
                ]

            # Настраиваем таблицу
            table_widget = self.table_widgets[table_name]
            table_widget.setColumnCount(len(column_names))
            table_widget.setHorizontalHeaderLabels(column_names)
            table_widget.setRowCount(len(data))

            # Заполняем данными
            for row, row_data in enumerate(data):
                for col, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value) if value is not None else "")

                    # Форматируем даты
                    if isinstance(value, str) and (
                            'date' in column_names[col].lower() or 'created' in column_names[
                        col].lower() or 'completed' in column_names[col].lower()):
                        try:
                            if ' ' in value:  # Дата и время
                                date_obj = datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
                                item.setText(date_obj.strftime('%d.%m.%Y %H:%M'))
                            else:  # Только дата
                                date_obj = datetime.strptime(str(value), '%Y-%m-%d')
                                item.setText(date_obj.strftime('%d.%m.%Y'))
                        except:
                            pass

                    # Цветовое оформление для статусов заданий
                    if table_name == 'maintenance_tasks' and col == 5:  # Колонка статуса
                        self.color_task_by_status(item, str(value).lower())

                    # Цветовое оформление для других статусов
                    elif 'status' in column_names[col].lower() or 'is_read' in column_names[col].lower():
                        if str(value).lower() in ['true', '1', 'активно', 'available', 'confirmed']:
                            item.setBackground(Qt.GlobalColor.lightGreen)
                        elif str(value).lower() in ['false', '0', 'неактивно', 'occupied']:
                            item.setBackground(Qt.GlobalColor.lightGray)

                    table_widget.setItem(row, col, item)

            # Автоматическое растягивание колонок
            table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

            print(f"✅ Таблица {table_name}: {len(data)} записей")

        except Exception as e:
            print(f"❌ Ошибка загрузки таблицы {table_name}: {e}")

    def show_database_structure(self):
        """Показать структуру базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Получаем список всех таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            structure_info = "📊 СТРУКТУРА БАЗЫ ДАННЫХ\n\n"

            for table in tables:
                table_name = table[0]
                structure_info += f"📋 ТАБЛИЦА: {table_name}\n"

                # Получаем информацию о колонках
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, pk = col
                    structure_info += f"  ├─ {col_name} ({col_type})"
                    if pk:
                        structure_info += " PRIMARY KEY"
                    if not_null:
                        structure_info += " NOT NULL"
                    if default_val:
                        structure_info += f" DEFAULT {default_val}"
                    structure_info += "\n"

                structure_info += "\n"

            conn.close()

            # Показываем информацию в диалоговом окне
            msg = QMessageBox(self)
            msg.setWindowTitle("Структура базы данных")
            msg.setText(structure_info)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить структуру БД:\n{str(e)}")

    def show_tasks_statistics(self):
        """Показать статистику по заданиям"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Статистика по статусам
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM maintenance_tasks 
                GROUP BY status 
                ORDER BY 
                    CASE status 
                        WHEN 'новая' THEN 1
                        WHEN 'в работе' THEN 2
                        WHEN 'выполнена' THEN 3
                        ELSE 4
                    END
            ''')
            status_stats = cursor.fetchall()

            # Статистика по комнатам
            cursor.execute('''
                SELECT room_number, COUNT(*) as task_count,
                       SUM(CASE WHEN status = 'выполнена' THEN 1 ELSE 0 END) as completed_count
                FROM maintenance_tasks 
                GROUP BY room_number
                ORDER BY task_count DESC
                LIMIT 10
            ''')
            room_stats = cursor.fetchall()

            # Статистика по сотрудникам
            cursor.execute('''
                SELECT s.first_name || ' ' || s.last_name as staff_name,
                       COUNT(mt.id) as task_count,
                       SUM(CASE WHEN mt.status = 'выполнена' THEN 1 ELSE 0 END) as completed_count
                FROM maintenance_tasks mt
                LEFT JOIN staff s ON mt.assigned_to = s.id
                GROUP BY mt.assigned_to
                ORDER BY task_count DESC
            ''')
            staff_stats = cursor.fetchall()

            conn.close()

            # Формируем отчет
            stats_text = "📊 СТАТИСТИКА ЗАДАНИЙ НА УБОРКУ\n\n"

            stats_text += "📋 ПО СТАТУСАМ:\n"
            for status, count in status_stats:
                stats_text += f"  {status:<12}: {count:>2} заданий\n"

            stats_text += "\n🏠 ПО КОМНАТАМ (ТОП-10):\n"
            for room, total, completed in room_stats:
                stats_text += f"  Комната {room}: {total} заданий ({completed} выполнено)\n"

            stats_text += "\n👨‍💼 ПО СОТРУДНИКАМ:\n"
            for staff_name, total, completed in staff_stats:
                if staff_name:
                    stats_text += f"  {staff_name}: {total} заданий ({completed} выполнено)\n"
                else:
                    stats_text += f"  Не назначено: {total} заданий\n"

            QMessageBox.information(self, "Статистика заданий", stats_text)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить статистику:\n{str(e)}")


def main():
    # Проверка наличия базы данных
    try:
        conn = sqlite3.connect('Hotel_bd.db')
        cursor = conn.cursor()

        # Проверяем существование таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]

        required_tables = ['messages', 'bookings', 'guests', 'rooms', 'staff', 'maintenance_tasks']
        missing_tables = [table for table in required_tables if table not in tables]

        if missing_tables:
            QMessageBox.warning(
                None,
                "Внимание",
                f"Отсутствуют таблицы: {', '.join(missing_tables)}\n"
                f"Создайте базу данных с помощью script_bd.py"
            )

        conn.close()

    except sqlite3.Error as e:
        QMessageBox.critical(
            None,
            "Ошибка базы данных",
            f"Не удалось подключиться к базе данных:\n{str(e)}"
        )
        return

    # Запуск приложения
    app = QApplication(sys.argv)
    window = HotelManager()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()