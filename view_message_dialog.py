# view_message_dialog.py
import pickle
import sqlite3
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic

from bd_manager import YandexDiskUploader
from utils import get_resource_path


class ViewMessageDialog(QDialog):
    message_read = pyqtSignal(int)

    def __init__(self, message_data, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.full_name = parent.full_name
        self.is_marked_as_read = False

        uic.loadUi(get_resource_path('UI/Reg/Окно ответа.ui'), self)

        self.setup_connections()
        self.populate_data()


    def setup_connections(self):
        try:
            self.send_reply_button.clicked.connect(self.send_reply)
            self.close_button.clicked.connect(self.close_dialog)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def populate_data(self):
        try:
            self.sender_label.setText(f"От: {self.message_data['sender_name']}")
            self.position_label.setText(f"Должность: {self.message_data['position']}")
            self.time_label.setText(f"Время: {self.message_data['created_at']}")
            self.message_text.setPlainText(self.message_data['full_text'])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def mark_as_read(self):
        try:
            if self.is_marked_as_read:
                return

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE messages 
                SET is_read = 1 
                WHERE id = ?
            ''', (self.message_data['id'],))

            conn.commit()
            conn.close()

            self.is_marked_as_read = True

            self.message_read.emit(self.message_data['id'])


        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def send_reply(self):
        try:
            reply_text = self.reply_text.toPlainText().strip()

            if not reply_text:
                QMessageBox.warning(self, "Ошибка", "Введите текст сообщения")
                return

            binary_message = pickle.dumps(reply_text)

            con = sqlite3.connect('Hotel_bd.db')
            cur = con.cursor()

            recipient_name = self.message_data['sender_name']


            recipient_parts = recipient_name.split()
            if len(recipient_parts) < 2:
                raise ValueError("Некорректное имя получателя")

            recipient_found = False
            id_recipient = None

            cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                        (recipient_parts[0], recipient_parts[1]))
            result = cur.fetchone()
            if result:
                recipient_found = True
                id_recipient = result[0]

            if not recipient_found and len(recipient_parts) >= 2:
                cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                            (recipient_parts[1], recipient_parts[0]))
                result = cur.fetchone()
                if result:
                    recipient_found = True
                    id_recipient = result[0]

            if not recipient_found:
                raise ValueError(f"Получатель '{recipient_name}' не найден в базе данных")

            sender_parts = self.full_name.split()
            if len(sender_parts) < 2:
                raise ValueError("Некорректное имя отправителя")

            sender_found = False
            id_sender = None

            cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                        (sender_parts[0], sender_parts[1]))
            result = cur.fetchone()
            if result:
                sender_found = True
                id_sender = result[0]

            if not sender_found and len(sender_parts) >= 2:
                cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                            (sender_parts[1], sender_parts[0]))
                result = cur.fetchone()
                if result:
                    sender_found = True
                    id_sender = result[0]

            if not sender_found:
                raise ValueError("Отправитель не найден в базе данных")

            cur.execute('''INSERT INTO messages (from_user, to_user, text)
                            VALUES (?, ?, ?)''',
                        (id_sender, id_recipient, binary_message))

            con.commit()
            con.close()

            QMessageBox.information(self, "Успех", "Ответ отправлен")

            self.mark_as_read()

            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить ответ")
        finally:
            if 'con' in locals():
                con.close()

    def close_dialog(self):
        try:
            self.mark_as_read()

            try:
                self.send_reply_button.clicked.disconnect()
            except:
                pass
            try:
                self.close_button.clicked.disconnect()
            except:
                pass

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            try:
                self.reject()
            except:
                pass

    def closeEvent(self, event):
        try:

            self.mark_as_read()

            self.close_dialog()
            event.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            event.accept()