from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QPushButton,
                             QLabel, QListWidgetItem, QHBoxLayout,
                             QWidget, QSpacerItem, QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6 import uic
import os
from regist.correction_dialog import CorrectionDialog


class DataValidationDialog(QDialog):
    def __init__(self, errors_data, parent=None):
        super().__init__(parent)
        self.errors_data = errors_data.copy()  # Делаем копию чтобы не менять оригинал
        self.cancelled_rows = set()
        self.corrected_rows = set()

        # Загружаем UI
        uic.loadUi('UI/Reg/Окно ошибок.ui', self)

        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Заполняем список ошибок
        self.populate_errors_list()

        # Подключаем кнопку
        self.cancelLoadBtn.clicked.connect(self.cancel_all)

    def reject(self):
        """Обработка закрытия окна через крестик - просто закрываем"""
        super().reject()

    def populate_errors_list(self):
        """Заполнение списка ошибок"""
        self.errorsList.clear()

        # НЕ закрываем автоматически когда список пустой
        # Просто показываем сообщение что все ошибки обработаны

        # Заполняем список оставшимися ошибками
        for i, (row_num, row_data, error) in enumerate(self.errors_data):
            if i in self.cancelled_rows or i in self.corrected_rows:
                continue

            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(15, 10, 15, 10)
            item_layout.setSpacing(15)

            # Информация об ошибке
            error_info = QLabel(f"<b>Строка {row_num}:</b> {error}<br>"
                                f"<i>Данные:</i> {', '.join(map(str, row_data))}")
            error_info.setWordWrap(True)
            error_info.setStyleSheet("""
                QLabel {
                    font-size: 11px; 
                    color: #2c3e50;
                    padding: 8px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                    border: 1px solid #dee2e6;
                }
            """)
            error_info.setMinimumWidth(400)
            error_info.setMaximumWidth(500)
            error_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            item_layout.addWidget(error_info, 1)

            # Контейнер для кнопок
            button_container = QWidget()
            button_layout = QVBoxLayout(button_container)
            button_layout.setSpacing(8)
            button_layout.setContentsMargins(0, 0, 0, 0)

            # Кнопка исправить
            fix_btn = QPushButton("Исправить")
            fix_btn.setFixedSize(100, 35)
            fix_btn.setEnabled(True)
            fix_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #219a52;
                }
            """)
            fix_btn.clicked.connect(lambda checked, idx=i, rd=row_data, rn=row_num: self.correct_row(idx, rd, rn))
            button_layout.addWidget(fix_btn)

            # Кнопка отменить
            cancel_btn = QPushButton("Отменить")
            cancel_btn.setObjectName("cancelBtn")
            cancel_btn.setFixedSize(100, 35)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            cancel_btn.clicked.connect(lambda checked, idx=i: self.cancel_row(idx))
            button_layout.addWidget(cancel_btn)

            button_layout.addStretch()
            item_layout.addWidget(button_container)

            # Создаем элемент списка
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(100, 120))

            self.errorsList.addItem(list_item)
            self.errorsList.setItemWidget(list_item, item_widget)

        # Если все ошибки обработаны, показываем сообщение
        visible_errors_count = len([i for i in range(len(self.errors_data))
                                    if i not in self.cancelled_rows and i not in self.corrected_rows])
        if visible_errors_count == 0:
            # Показываем сообщение но НЕ закрываем автоматически
            self.errorsList.clear()
            empty_label = QLabel("Все ошибки обработаны. Вы можете закрыть окно.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("font-size: 14px; color: #27ae60; padding: 20px;")
            self.errorsList.addItem(QListWidgetItem())
            self.errorsList.setItemWidget(self.errorsList.item(0), empty_label)

    def correct_row(self, index, row_data, row_number):
        """Исправить одну строку"""
        try:
            from regist.correction_dialog import CorrectionDialog

            row_data = list(row_data) if not isinstance(row_data, list) else row_data
            dialog = CorrectionDialog(row_data, row_number, self)
            dialog.correction_finished.connect(lambda cd, rn: self.on_correction_finished(cd, rn, index))
            dialog.show()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при исправлении: {str(e)}")

    def on_correction_finished(self, corrected_data, row_number, error_index):
        """Обработчик завершения исправления"""
        if corrected_data:
            # Находим актуальный индекс в данных (может измениться после предыдущих удалений)
            actual_data_index = -1
            for i, row in enumerate(self.parent().data):
                # Сравниваем с исходными данными ошибки
                if (len(row) >= 8 and len(self.errors_data[error_index][1]) >= 8 and
                        row[0] == self.errors_data[error_index][1][0] and  # имя
                        row[1] == self.errors_data[error_index][1][1] and  # фамилия
                        row[3] == self.errors_data[error_index][1][3]):  # паспорт
                    actual_data_index = i
                    break

            if actual_data_index >= 0:
                # Обновляем данные
                self.parent().data[actual_data_index] = corrected_data

                if hasattr(self.parent(), 'update_preview_after_correction'):
                    self.parent().update_preview_after_correction()

            # Помечаем как исправленную
            self.corrected_rows.add(error_index)

            # Обновляем список
            self.populate_errors_list()

            QMessageBox.information(self, "Успех", "Данные успешно исправлены!")

    def cancel_row(self, index):
        """Отменить одну строку"""
        # Находим актуальный индекс в данных
        row_data = self.errors_data[index][1]
        actual_data_index = -1

        for i, row in enumerate(self.parent().data):
            if (len(row) >= 8 and len(row_data) >= 8 and
                    row[0] == row_data[0] and  # имя
                    row[1] == row_data[1] and  # фамилия
                    row[3] == row_data[3]):  # паспорт
                actual_data_index = i
                break

        if actual_data_index >= 0:
            # Удаляем строку из данных
            del self.parent().data[actual_data_index]

            if hasattr(self.parent(), 'update_preview_after_correction'):
                self.parent().update_preview_after_correction()

        self.cancelled_rows.add(index)
        self.populate_errors_list()

    def cancel_all(self):
        """Отменить все ошибочные строки"""
        # Находим все строки для удаления
        rows_to_remove = []
        for i in range(len(self.errors_data)):
            if i not in self.corrected_rows:  # Не удаляем исправленные
                row_data = self.errors_data[i][1]
                for j, row in enumerate(self.parent().data):
                    if (len(row) >= 8 and len(row_data) >= 8 and
                            row[0] == row_data[0] and
                            row[1] == row_data[1] and
                            row[3] == row_data[3]):
                        if j not in rows_to_remove:  # избегаем дубликатов
                            rows_to_remove.append(j)
                        break
                self.cancelled_rows.add(i)

        # Удаляем строки из данных (в обратном порядке)
        for index in sorted(rows_to_remove, reverse=True):
            if index < len(self.parent().data):
                del self.parent().data[index]

        if hasattr(self.parent(), 'update_preview_after_correction'):
            self.parent().update_preview_after_correction()

        self.populate_errors_list()

    def get_cancelled_rows(self):
        """Возвращает индексы отмененных строк"""
        return self.cancelled_rows

    def get_corrected_rows(self):
        """Возвращает индексы исправленных строк"""
        return self.corrected_rows