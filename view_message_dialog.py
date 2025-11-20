# view_message_dialog.py
import pickle
import sqlite3
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic

from bd_manager import YandexDiskUploader
from utils import get_resource_path


class ViewMessageDialog(QDialog):
    message_read = pyqtSignal(int)  # Сигнал при прочтении сообщения

    def __init__(self, message_data, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.full_name = parent.full_name  # Получаем имя текущего пользователя

        try:
            # Загрузка UI файла как в вашей программе
            uic.loadUi(get_resource_path('UI/Reg/Окно ответа.ui'), self)

            self.setup_connections()
            self.populate_data()
            self.mark_as_read()

        except Exception as e:
            print(f"Ошибка инициализации диалога: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить диалог: {e}")

    def setup_connections(self):
        """Настройка соединений сигналов"""
        try:
            self.send_reply_button.clicked.connect(self.send_reply)
            self.close_button.clicked.connect(self.close_dialog)
        except Exception as e:
            print(f"Ошибка настройки соединений: {e}")

    def populate_data(self):
        """Заполнение данных сообщения"""
        try:
            self.sender_label.setText(f"От: {self.message_data['sender_name']}")
            self.position_label.setText(f"Должность: {self.message_data['position']}")
            self.time_label.setText(f"Время: {self.message_data['created_at']}")
            self.message_text.setPlainText(self.message_data['full_text'])
        except Exception as e:
            print(f"Ошибка заполнения данных: {e}")

    def mark_as_read(self):
        """Пометить сообщение как прочитанное в БД"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE messages 
                SET is_read = 1 
                WHERE id = ?
            ''', (self.message_data['id'],))

            conn.commit()
            conn.close()

            # Отправляем сигнал что сообщение прочитано
            self.message_read.emit(self.message_data['id'])

        except Exception as e:
            print(f"Ошибка при обновлении статуса сообщения: {e}")

    def send_reply(self):
        """Отправка ответа на сообщение"""
        try:
            reply_text = self.reply_text.toPlainText().strip()

            if not reply_text:
                QMessageBox.warning(self, "Ошибка", "Введите текст сообщения")
                return

            binary_message = pickle.dumps(reply_text)

            con = sqlite3.connect('Hotel_bd.db')
            cur = con.cursor()

            # Получатель - автор исходного сообщения
            recipient_name = self.message_data['sender_name']

            # Отладочная информация
            print(f"Отправка ответа:")
            print(f"Получатель: {recipient_name}")
            print(f"Отправитель: {self.full_name}")
            print(f"Текст: {reply_text}")

            # Разбираем имя получателя
            recipient_parts = recipient_name.split()
            if len(recipient_parts) < 2:
                raise ValueError("Некорректное имя получателя")

            # Пробуем разные варианты поиска получателя
            recipient_found = False
            id_recipient = None

            # Вариант 1: как есть
            cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                        (recipient_parts[0], recipient_parts[1]))
            result = cur.fetchone()
            if result:
                recipient_found = True
                id_recipient = result[0]
                print(f"Получатель найден (вариант 1): {recipient_parts[0]} {recipient_parts[1]}")

            # Вариант 2: обратный порядок
            if not recipient_found and len(recipient_parts) >= 2:
                cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                            (recipient_parts[1], recipient_parts[0]))
                result = cur.fetchone()
                if result:
                    recipient_found = True
                    id_recipient = result[0]
                    print(f"Получатель найден (вариант 2): {recipient_parts[1]} {recipient_parts[0]}")

            if not recipient_found:
                raise ValueError(f"Получатель '{recipient_name}' не найден в базе данных")

            # Поиск отправителя
            sender_parts = self.full_name.split()
            if len(sender_parts) < 2:
                raise ValueError("Некорректное имя отправителя")

            sender_found = False
            id_sender = None

            # Вариант 1: как есть
            cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                        (sender_parts[0], sender_parts[1]))
            result = cur.fetchone()
            if result:
                sender_found = True
                id_sender = result[0]
                print(f"Отправитель найден (вариант 1): {sender_parts[0]} {sender_parts[1]}")

            # Вариант 2: обратный порядок
            if not sender_found and len(sender_parts) >= 2:
                cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                            (sender_parts[1], sender_parts[0]))
                result = cur.fetchone()
                if result:
                    sender_found = True
                    id_sender = result[0]
                    print(f"Отправитель найден (вариант 2): {sender_parts[1]} {sender_parts[0]}")

            if not sender_found:
                raise ValueError("Отправитель не найден в базе данных")

            # Вставляем сообщение
            cur.execute('''INSERT INTO messages (from_user, to_user, text)
                            VALUES (?, ?, ?)''',
                        (id_sender, id_recipient, binary_message))

            con.commit()
            con.close()


            # # Очищаем поле ответа и показываем подтверждение
            # self.reply_text.clear()
            # self.send_reply_button.setText("✓ Отправлено!")
            # self.send_reply_button.setStyleSheet("""
            #     QPushButton {
            #         background-color: #28a745;
            #         color: white;
            #         border: none;
            #         padding: 8px 16px;
            #         border-radius: 6px;
            #         font-weight: bold;
            #     }
            # """)

            QMessageBox.information(self, "Успех", "Ответ отправлен")
            self.close()
            uploader = YandexDiskUploader("y0__xD89tSJBBjblgMg1fC9ihUwhJeqlwgXFM-EwH6GAbo1cJ6dfjDG4_HR0g")
            if uploader.upload_db():
                print("Изменения загружены на Яндекс Диск")
            else:
                print("Не удалось загрузить изменения")

        except Exception as e:
            print(f"Ошибка отправки ответа: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить ответ: {str(e)}")
        finally:
            if 'con' in locals():
                con.close()

    def close_dialog(self):
        """Закрытие диалога - БЕЗОПАСНАЯ ВЕРСИЯ"""
        try:
            print("Закрытие диалога просмотра сообщения")
            self.accept()
        except Exception as e:
            print(f"Ошибка при закрытии диалога: {e}")
            self.reject()  # Альтернативный способ закрытия

    def closeEvent(self, event):
        """Обработчик события закрытия окна"""
        try:
            print("Событие закрытия диалога")
            self.close_dialog()
            event.accept()
        except Exception as e:
            print(f"Ошибка в closeEvent: {e}")
            event.accept()  # Все равно принимаем событие закрытия