# notifications_manager.py
import pickle
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QScrollArea, QWidget
from PyQt6.QtCore import QTimer, Qt, QObject


class SimpleNotificationWidget(QFrame):
    """Простой виджет уведомления"""

    def __init__(self, message_data, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.setup_ui()

    # def convert_to_string(self, data):
    #     """Преобразование данных в строку с обрезкой и декодированием pickle"""
    #     if data is None:
    #         return ""
    #
    #     print(f"DEBUG: Получены данные типа: {type(data)}")
    #     if isinstance(data, bytes):
    #         print(f"DEBUG: Байты для декодирования: {data[:50]}...")  # Первые 50 байт
    #
    #         try:
    #             # Декодируем из pickle
    #             decoded_data = pickle.loads(data)
    #             print(f"DEBUG: После pickle.loads: {type(decoded_data)} - {decoded_data}")
    #
    #             # Убеждаемся что это строка
    #             if isinstance(decoded_data, bytes):
    #                 decoded_data = decoded_data.decode('utf-8', errors='ignore')
    #                 print(f"DEBUG: После decode: {type(decoded_data)} - {decoded_data}")
    #
    #             decoded_data = str(decoded_data)
    #             print(f"DEBUG: Финальная строка: {decoded_data}")
    #
    #         except Exception as e:
    #             print(f"DEBUG: Ошибка pickle: {e}")
    #             # Если не pickle, пробуем как обычную строку
    #             try:
    #                 decoded_data = data.decode('utf-8', errors='ignore')
    #                 print(f"DEBUG: После прямого decode: {decoded_data}")
    #             except:
    #                 decoded_data = "Нечитаемые данные"
    #     else:
    #         decoded_data = str(data)
    #         print(f"DEBUG: Не байты, просто строка: {decoded_data}")
    #
    #     # Обрезаем до 20 символов и добавляем ...
    #     if len(decoded_data) > 20:
    #         result = decoded_data[:20] + "..."
    #     else:
    #         result = decoded_data
    #
    #     print(f"DEBUG: Итоговый результат: {result}")
    #     return result

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)

        # Разные стили для прочитанных и непрочитанных
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

        # Текст сообщения - используем convert_to_string
        message_text = self.message_data.get('text', '')
        self.message_label = QLabel(message_text)
        self.message_label.setStyleSheet("font-size: 10px; color: #5a6c7d;")
        self.message_label.setWordWrap(True)

        # Информация об отправителе и времени
        sender_name = self.message_data.get('sender_name', 'Неизвестный')
        time_str = self.format_time(self.message_data.get('created_at', ''))
        info_text = f"От: {sender_name} • {time_str}"

        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("font-size: 9px; color: #8798a7;")

        layout.addWidget(self.message_label)
        layout.addWidget(self.info_label)

    def format_time(self, timestamp):
        """Форматирование времени для отображения"""
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
            now = datetime.now()
            diff = now - timestamp

            if diff.days == 0:
                if diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f"{minutes} мин. назад"
                else:
                    hours = diff.seconds // 3600
                    return f"{hours} ч. назад"
            elif diff.days == 1:
                return "Вчера"
            else:
                return timestamp.strftime("%d.%m.%Y")

        return str(timestamp)


class SimpleNotificationsManager(QObject):
    """Менеджер уведомлений, использующий существующие сообщения из БД"""

    def __init__(self, user_id, notifications_frame):
        super().__init__()
        self.user_id = user_id
        self.notifications_frame = notifications_frame
        self.is_active = True

        # Таймер для автообновления
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.safe_load_notifications)

        self.setup_notifications_panel()
        self.safe_load_notifications()
        self.update_timer.start(30000)  # 30 секунд

    def setup_notifications_panel(self):
        """Настройка панели уведомлений с прокруткой"""
        if not self.is_widget_valid(self.notifications_frame):
            return
        self.notifications_frame.setMaximumWidth(250)  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
        self.notifications_frame.setStyleSheet("""
                QFrame {
                    background-color: white; 
                    border-radius: 6px; 
                    padding: 8px;
                    border: 1px solid #e1e8ed;
                    max-width: 250px;  /* ← ДОБАВЬТЕ ЭТО */
                }
            """)
        layout = self.notifications_frame.layout()
        if layout:
            self.clear_layout(layout)

        # Область прокрутки для уведомлений
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setMinimumHeight(200)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 10px;
                background-color: #f1f3f4;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c7d0;
                border-radius: 5px;
            }
        """)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.setContentsMargins(2, 2, 2, 2)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        # Сообщение когда уведомлений нет
        self.empty_label = QLabel("Нет сообщений")
        self.empty_label.setStyleSheet("font-size: 10px; color: #8798a7; text-align: center; padding: 20px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def is_widget_valid(self, widget):
        """Проверка что виджет еще существует"""
        try:
            return widget is not None and widget.isWidgetType()
        except RuntimeError:
            return False

    def clear_layout(self, layout):
        """Безопасная очистка layout"""
        try:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            print(f"Ошибка очистки layout: {e}")

    def safe_load_notifications(self):
        """Безопасная загрузка уведомлений с проверкой"""
        if not self.is_active or not self.is_widget_valid(self.notifications_frame):
            return

        try:
            self.load_notifications()
        except Exception as e:
            print(f"Ошибка загрузки уведомлений: {e}")

    def load_notifications(self):
        """Загрузка существующих сообщений из базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            # Загружаем сообщения для текущего пользователя, сначала самые новые
            cursor.execute('''
                SELECT m.id, m.text, m.created_at, m.from_user, 
                       s.first_name, s.last_name, s.position, m.is_read
                FROM messages m
                JOIN staff s ON m.from_user = s.id
                WHERE m.to_user = ?
                ORDER BY m.created_at DESC
                LIMIT 20
            ''', (self.user_id,))

            messages = cursor.fetchall()
            conn.close()

            self.display_notifications(messages)

        except Exception as e:
            print(f"Ошибка загрузки сообщений из БД: {e}")
            self.display_empty_message()

    def display_notifications(self, messages):
        """Отображение сообщений в панели"""
        if not self.is_widget_valid(self.scroll_widget):
            return

        # Безопасная очистка
        try:
            while self.scroll_layout.count() > 0:
                child = self.scroll_layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()
        except Exception as e:
            print(f"Ошибка очистки уведомлений: {e}")
            return

        # Добавляем растягивающийся элемент в конец
        self.scroll_layout.addStretch()

        if not messages:
            self.display_empty_message()
            return

        # Добавляем сообщения В ОБРАТНОМ ПОРЯДКЕ (новые сверху)
        for msg_id, text, created_at, from_user, first_name, last_name, position, is_read in reversed(messages):
            if not self.is_active:
                break

            # Преобразуем данные в правильный формат
            message_data = {
                'id': msg_id,
                'text': self.convert_to_string(text),
                'created_at': self.convert_to_string(created_at),
                'sender_name': f"{self.convert_to_string(first_name)} {self.convert_to_string(last_name)}",
                'position': self.convert_to_string(position),
                'is_read': bool(is_read)
            }

            try:
                notification_widget = SimpleNotificationWidget(message_data)
                # Вставляем в начало (сверху)
                self.scroll_layout.insertWidget(0, notification_widget)

            except Exception as e:
                print(f"Ошибка создания виджета уведомления: {e}")
                continue

    def convert_to_string(self, data):
        """Преобразование данных в строку с декодированием pickle"""
        if data is None:
            return ""

        if isinstance(data, bytes):
            try:
                # Декодируем из pickle
                decoded_data = pickle.loads(data)
                # Убеждаемся что это строка
                if isinstance(decoded_data, bytes):
                    decoded_data = decoded_data.decode('utf-8', errors='ignore')
                decoded_data = str(decoded_data)
            except Exception as e:
                print(f"Ошибка декодирования: {e}")
                try:
                    decoded_data = data.decode('utf-8', errors='ignore')
                except:
                    decoded_data = "Нечитаемые данные"
        else:
            decoded_data = str(data)

        # Обрезаем до 20 символов
        if len(decoded_data) > 20:
            return decoded_data[:20] + "..."
        else:
            return decoded_data

    def display_empty_message(self):
        """Показать сообщение об отсутствии уведомлений"""
        if self.is_widget_valid(self.empty_label):
            self.scroll_layout.insertWidget(0, self.empty_label)

    def stop_updates(self):
        """Остановка автообновления уведомлений"""
        self.is_active = False
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()