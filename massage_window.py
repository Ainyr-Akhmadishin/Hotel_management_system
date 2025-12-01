import pickle
import sqlite3

from PyQt6.QtWidgets import QDialog, QMainWindow, QMessageBox
from PyQt6 import uic


from bd_manager import YandexDiskUploader
from utils import get_resource_path


class EmptyRecipientError(Exception):
    pass


class EmptyMassageError(Exception):
    pass


class MassageWindow(QDialog):
    def __init__(self,full_name, parent=None):
        super().__init__(parent)
        uic.loadUi(get_resource_path('UI/Reg/Окно отправки сообщений.ui'), self)
        self.setWindowTitle("Отправка сообщений")

        self.full_name = full_name
        self.load_staff('')
        self.search_recipient_input.textChanged.connect(lambda: self.load_staff(self.search_recipient_input.text().title()))
        self.recipients_list.itemClicked.connect(self.selected_recipient)

        self.send_button.clicked.connect(self.send_message)
        self.cancel_button.clicked.connect(self.close)

    def selected_recipient(self, item):
        self.recipient = item.text()
        self.selected_recipient_label.setText("Отправить: " + self.recipient)

    def send_message(self):
        try:
            binary_message = pickle.dumps(self.message_text_edit.toPlainText())

            con = sqlite3.connect('Hotel_bd.db')
            cur = con.cursor()


            if not hasattr(self, 'recipient') or not self.recipient:
                raise EmptyRecipientError("Не выбран получатель")

            if not self.message_text_edit.toPlainText().strip():
                raise EmptyMassageError("Введите текст сообщения")

            recipient_parts = self.recipient.split()
            # if len(recipient_parts) < 2:
            #     raise ValueError("Некорректное имя получателя")
            #
            sender_parts = self.full_name.split()
            # if len(sender_parts) < 2:
            #     raise ValueError("Некорректное имя отправителя")


            cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                        (recipient_parts[0], recipient_parts[1]))
            recipient_result = cur.fetchone()
            if not recipient_result:
                raise sqlite3.Error("Получатель не найден в базе данных")
            self.id_recipient = recipient_result[0]


            cur.execute('''SELECT id FROM staff WHERE last_name = ? AND first_name = ?''',
                        (sender_parts[1], sender_parts[0]))
            sender_result = cur.fetchone()
            if not sender_result:
                raise ValueError("Отправитель не найден в базе данных")
            self.id_sender = sender_result[0]


            cur.execute('''INSERT INTO messages (from_user, to_user, text)
                            VALUES (?, ?, ?)''',
                        (self.id_sender, self.id_recipient, binary_message))

            con.commit()
            con.close()
            QMessageBox.information(self, "Успех",
                                    f"Сообщение отправлено")
            self.close()
            # uploader = YandexDiskUploader("y0__xD89tSJBBjblgMg1fC9ihUwhJeqlwgXFM-EwH6GAbo1cJ6dfjDG4_HR0g")
            # if uploader.upload_db():
            #     print("Изменения загружены на Яндекс Диск")
            # else:
            #     print("Не удалось загрузить изменения")

        except EmptyRecipientError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except EmptyMassageError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except IndexError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if 'con' in locals():
                con.close()


    def load_staff(self, name):
        try:
            conn =sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()
            if name and name.strip():
                search_pattern = f'{name}%'
                cursor.execute('''
                                    SELECT last_name || ' ' || first_name || ' (' || position || ')' as staff_name 
                                    FROM staff WHERE first_name LIKE ? OR last_name LIKE ? 
                                    ORDER BY last_name, first_name
                                    ''', (search_pattern, search_pattern))
            else:
                cursor.execute('''
                                    SELECT last_name || ' ' || first_name || ' (' || position || ')' as staff_name 
                                    FROM staff 
                                    ORDER BY last_name, first_name
                                    ''')
            self.recipients_list.clear()
            self.recipients_list.addItems(row[0] for row in cursor.fetchall())
            conn.close()


        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка загрузки сотрудников", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))




