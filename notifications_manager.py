# notifications_manager.py
import pickle
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QScrollArea, QWidget, QMessageBox
from PyQt6.QtCore import QTimer, Qt, QObject, pyqtSignal

from utils import get_database_path
from view_message_dialog import ViewMessageDialog
from datetime import datetime, timezone


class SimpleNotificationWidget(QFrame):

    clicked = pyqtSignal(dict)

    def __init__(self, message_data, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)

        self.setMaximumWidth(220)
        self.setMinimumWidth(210)

        if not self.message_data.get('is_read', False):
            self.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 1px solid #4a6fa5;
                    border-radius: 6px;
                    padding: 8px;
                    margin: 2px 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #e1e5eb;
                    border-radius: 6px;
                    padding: 8px;
                    margin: 2px 0px;
                }
            """)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        message_text = self.message_data.get('text', '')
        self.message_label = QLabel(message_text)
        self.message_label.setStyleSheet("font-size: 10px; color: #5a6c7d;")
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(204)

        sender_name = self.message_data.get('sender_name', 'Неизвестный')
        time_str = self.message_data.get('created_at', '')
        info_text = f"От: {sender_name} • {time_str}"

        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("font-size: 9px; color: #8798a7;")
        self.info_label.setWordWrap(True)
        self.info_label.setMaximumWidth(204)

        layout.addWidget(self.message_label)
        layout.addWidget(self.info_label)

        if not self.message_data.get('is_read', False):
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton and
                not self.message_data.get('is_read', False)):
            self.clicked.emit(self.message_data)
        super().mousePressEvent(event)




class SimpleNotificationsManager(QObject):

    def __init__(self, user_id, notifications_frame, main_window=None):
        super().__init__()
        self.user_id = user_id
        self.notifications_frame = notifications_frame
        self.main_window = main_window
        self.is_active = True

        self.notification_widgets = {}

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.safe_load_notifications)

        self.setup_notifications_panel()
        self.safe_load_notifications()
        self.update_timer.start(15000)

    def setup_notifications_panel(self):
        if not self.is_widget_valid(self.notifications_frame):
            return

        layout = self.notifications_frame.layout()
        if layout:
            self.clear_layout(layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setMinimumHeight(200)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
                padding: 0px;  
                margin: 0px;
            }
        """)

        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: white; border: none; padding: 0px; margin: 0px;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.setContentsMargins(2, 2, 2, 2)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

    def is_widget_valid(self, widget):

        try:
            return widget is not None and widget.isWidgetType()
        except RuntimeError:
            return False

    def clear_layout(self, layout):
        try:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", str(e))

    def safe_load_notifications(self):
        if not self.is_active or not self.is_widget_valid(self.notifications_frame):
            return

        try:
            self.load_notifications()
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", str(e))

    def load_notifications(self):
        try:
            db_path = get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT m.id, m.text, m.created_at, m.from_user, 
                       s.first_name, s.last_name, s.position, m.is_read
                FROM messages m
                JOIN staff s ON m.from_user = s.id
                WHERE m.to_user = ? AND m.is_read = 0
                ORDER BY m.created_at DESC
                LIMIT 20
            ''', (self.user_id,))

            messages = cursor.fetchall()
            conn.close()

            self.display_notifications(messages)

        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", str(e))

    def display_notifications(self, messages):
        if not self.is_widget_valid(self.scroll_widget):
            return

        try:
            while self.scroll_layout.count() > 0:
                child = self.scroll_layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", str(e))
            return

        self.scroll_layout.addStretch()
        self.notification_widgets.clear()

        if not messages:
            return

        for msg_id, text, created_at, from_user, first_name, last_name, position, is_read in reversed(messages):
            if not self.is_active:
                break

            full_text = self.convert_to_full_text(text)

            message_data = {
                'id': msg_id,
                'text': self.convert_to_display_text(text),
                'full_text': full_text,
                'created_at': self.format_time(created_at),
                'sender_name': f"{self.convert_to_string(first_name)} {self.convert_to_string(last_name)}",
                'position': self.convert_to_string(position),
                'is_read': bool(is_read),
                'from_user': from_user,
                'to_user': self.user_id
            }

            try:
                notification_widget = SimpleNotificationWidget(message_data)
                notification_widget.clicked.connect(self.on_notification_clicked)

                self.scroll_layout.insertWidget(0, notification_widget)
                self.notification_widgets[msg_id] = notification_widget

            except Exception as e:
                QMessageBox.critical(self.main_window, "Ошибка", str(e))
                continue

    def convert_to_display_text(self, data):
        text = self.convert_to_string(data)
        if len(text) > 20:
            return text[:20] + "..."
        return text

    def convert_to_full_text(self, data):
        return self.convert_to_string(data)

    def convert_to_string(self, data):

        if data is None:
            return ""

        if isinstance(data, bytes):
            try:
                decoded_data = pickle.loads(data)
                if isinstance(decoded_data, bytes):
                    decoded_data = decoded_data.decode('utf-8', errors='ignore')
                decoded_data = str(decoded_data)
            except Exception as e:
                QMessageBox.critical(self.main_window, "Ошибка", str(e))
                try:
                    decoded_data = data.decode('utf-8', errors='ignore')
                except:
                    decoded_data = "Нечитаемые данные"
        else:
            decoded_data = str(data)

        return decoded_data

    def format_time(self, timestamp):
        if isinstance(timestamp, bytes):
            timestamp = timestamp.decode('utf-8', errors='ignore')

        if isinstance(timestamp, str):
            try:
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                    try:
                        timestamp = datetime.strptime(timestamp, fmt)
                        break
                    except ValueError:
                        continue
            except:
                return str(timestamp)

        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            local_timezone = datetime.now().astimezone().tzinfo
            local_time = timestamp.astimezone(local_timezone)

            return local_time.strftime("%H:%M %d.%m.%Y")

        return str(timestamp)

    def on_notification_clicked(self, message_data):
        try:
            dialog = ViewMessageDialog(message_data, self.main_window)
            dialog.finished.connect(lambda: self.immediately_remove_notification(message_data['id']))
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", str(e))

    def immediately_remove_notification(self, message_id):

        try:
            if message_id in self.notification_widgets:
                widget = self.notification_widgets[message_id]

                if (self.is_widget_valid(widget) and
                        self.is_widget_valid(self.scroll_widget) and
                        self.scroll_layout is not None):
                    self.scroll_layout.removeWidget(widget)
                    widget.deleteLater()
                    del self.notification_widgets[message_id]


        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", str(e))
            if message_id in self.notification_widgets:
                del self.notification_widgets[message_id]

    def on_message_read(self, message_id):
        self.immediately_remove_notification(message_id)

    def display_empty_message(self):

        if self.is_widget_valid(self.empty_label):

            for i in reversed(range(self.scroll_layout.count())):
                widget = self.scroll_layout.itemAt(i).widget()
                if widget and widget != self.empty_label:
                    self.scroll_layout.removeWidget(widget)
                    widget.deleteLater()


            self.scroll_layout.insertWidget(0, self.empty_label)

    def stop_updates(self):

        self.is_active = False
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

    def on_notification_clicked(self, message_data):

        try:

            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()

            dialog = ViewMessageDialog(message_data, self.main_window)

            def safe_remove():
                try:
                    self.immediately_remove_notification(message_data['id'])
                except Exception as e:
                    QMessageBox.critical(self.main_window, "Ошибка", str(e))
                finally:
                    if hasattr(self, 'update_timer') and not self.update_timer.isActive():
                        self.update_timer.start(30000)

            dialog.finished.connect(safe_remove)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", str(e))
            if hasattr(self, 'update_timer') and not self.update_timer.isActive():
                self.update_timer.start(30000)