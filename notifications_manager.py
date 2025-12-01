# notifications_manager.py
import pickle
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QScrollArea, QWidget
from PyQt6.QtCore import QTimer, Qt, QObject, pyqtSignal
from view_message_dialog import ViewMessageDialog
from datetime import datetime, timezone


class SimpleNotificationWidget(QFrame):
    """Простой виджет уведомления"""

    clicked = pyqtSignal(dict)  # Сигнал при клике на уведомление

    def __init__(self, message_data, parent=None):
        super().__init__(parent)
        self.message_data = message_data
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)

        # ДЕЛАЕМ УВЕДОМЛЕНИЯ ЧУТЬ УЖЕ ШИРИНЫ ПАНЕЛИ
        self.setMaximumWidth(220)  # Было 230, делаем немного уже
        self.setMinimumWidth(210)  # Добавляем минимальную ширину

        # Разные стили только для непрочитанных сообщений
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

        # Текст сообщения
        message_text = self.message_data.get('text', '')
        self.message_label = QLabel(message_text)
        self.message_label.setStyleSheet("font-size: 10px; color: #5a6c7d;")
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(204)  # 220 - 16 (padding)

        # Информация об отправителе и времени
        sender_name = self.message_data.get('sender_name', 'Неизвестный')
        time_str = self.message_data.get('created_at', '')
        info_text = f"От: {sender_name} • {time_str}"

        self.info_label = QLabel(info_text)
        self.info_label.setStyleSheet("font-size: 9px; color: #8798a7;")
        self.info_label.setWordWrap(True)
        self.info_label.setMaximumWidth(204)  # 220 - 16 (padding)

        layout.addWidget(self.message_label)
        layout.addWidget(self.info_label)

        # Делаем виджет кликабельным только для непрочитанных
        if not self.message_data.get('is_read', False):
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """Обработка клика на виджете - только для непрочитанных"""
        if (event.button() == Qt.MouseButton.LeftButton and
                not self.message_data.get('is_read', False)):
            self.clicked.emit(self.message_data)
        super().mousePressEvent(event)




class SimpleNotificationsManager(QObject):
    """Менеджер уведомлений, использующий существующие сообщения из БД"""

    def __init__(self, user_id, notifications_frame, main_window=None):
        super().__init__()
        self.user_id = user_id
        self.notifications_frame = notifications_frame
        self.main_window = main_window  # Ссылка на главное окно
        self.is_active = True

        # Словарь для хранения виджетов уведомлений
        self.notification_widgets = {}

        # Таймер для автообновления
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.safe_load_notifications)

        self.setup_notifications_panel()
        self.safe_load_notifications()
        self.update_timer.start(15000)  # 30 секунд

    def setup_notifications_panel(self):
        """Настройка панели уведомлений с прокруткой"""
        if not self.is_widget_valid(self.notifications_frame):
            return

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
                padding: 0px;  /* УБИРАЕМ ВНУТРЕННИЕ ОТСТУПЫ */
                margin: 0px;
            }
        """)

        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: white; border: none; padding: 0px; margin: 0px;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(4)
        # УМЕНЬШАЕМ ОТСТУПЫ ДО МИНИМУМА
        self.scroll_layout.setContentsMargins(2, 2, 2, 2)  # Минимальные отступы
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

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
        """Загрузка ТОЛЬКО НЕПРОЧИТАННЫХ сообщений из базы данных"""
        try:
            conn = sqlite3.connect('Hotel_bd.db')
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
            print(f"Ошибка загрузки сообщений из БД: {e}")
            # При ошибке тоже не показываем сообщение

    def display_notifications(self, messages):
        """Отображение ТОЛЬКО НЕПРОЧИТАННЫХ сообщений в панели"""
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

        self.scroll_layout.addStretch()  # Добавляем растяжку
        self.notification_widgets.clear()

        if not messages:
            # Если сообщений нет - просто оставляем пустую панель с растяжкой
            return

        # Добавляем только непрочитанные сообщения
        for msg_id, text, created_at, from_user, first_name, last_name, position, is_read in reversed(messages):
            if not self.is_active:
                break

            # Полный текст для диалога (без обрезки)
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

                # Вставляем в начало (сверху)
                self.scroll_layout.insertWidget(0, notification_widget)
                self.notification_widgets[msg_id] = notification_widget

            except Exception as e:
                print(f"Ошибка создания виджета уведомления: {e}")
                continue

    def convert_to_display_text(self, data):
        """Конвертация для отображения в списке (укороченный текст)"""
        text = self.convert_to_string(data)
        if len(text) > 20:  # УМЕНЬШАЕМ ДЛИНУ ДЛЯ УЗКОЙ ПАНЕЛИ
            return text[:20] + "..."
        return text

    def convert_to_full_text(self, data):
        """Конвертация полного текста без обрезки"""
        return self.convert_to_string(data)

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

        return decoded_data

    def format_time(self, timestamp):
        """Форматирование времени для отображения в формате ЧЧ:ММ ДД.ММ.ГГ с автоматической коррекцией часового пояса"""
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
            # Если время не имеет информации о часовом поясе, считаем его UTC
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            # Конвертируем в локальный часовой пояс системы
            local_timezone = datetime.now().astimezone().tzinfo
            local_time = timestamp.astimezone(local_timezone)

            return local_time.strftime("%H:%M %d.%m.%Y")

        return str(timestamp)

    def on_notification_clicked(self, message_data):
        """Обработка клика на уведомлении"""
        try:
            dialog = ViewMessageDialog(message_data, self.main_window)
            # Подключаем сигнал к слоту который сразу удалит уведомление
            dialog.finished.connect(lambda: self.immediately_remove_notification(message_data['id']))
            dialog.exec()

        except Exception as e:
            print(f"Ошибка открытия диалога сообщения: {e}")

    def immediately_remove_notification(self, message_id):
        """Немедленное удаление уведомления при закрытии диалога"""
        print(f"Немедленное удаление уведомления: {message_id}")

        try:
            if message_id in self.notification_widgets:
                widget = self.notification_widgets[message_id]

                if (self.is_widget_valid(widget) and
                        self.is_widget_valid(self.scroll_widget) and
                        self.scroll_layout is not None):
                    self.scroll_layout.removeWidget(widget)
                    widget.deleteLater()
                    del self.notification_widgets[message_id]
                    print(f"Уведомление {message_id} удалено")

            # УБИРАЕМ вызов display_empty_message
            # Если уведомлений не осталось - просто оставляем пустую панель

        except Exception as e:
            print(f"Ошибка при удалении уведомления {message_id}: {e}")
            if message_id in self.notification_widgets:
                del self.notification_widgets[message_id]

    def on_message_read(self, message_id):
        """Обработка прочтения сообщения (оставлено для обратной совместимости)"""
        # Этот метод теперь не используется для немедленного удаления,
        # но оставлен если где-то еще используется
        self.immediately_remove_notification(message_id)

    def display_empty_message(self):
        """Показать сообщение об отсутствии уведомлений"""
        if self.is_widget_valid(self.empty_label):
            # Удаляем все существующие виджеты кроме empty_label
            for i in reversed(range(self.scroll_layout.count())):
                widget = self.scroll_layout.itemAt(i).widget()
                if widget and widget != self.empty_label:
                    self.scroll_layout.removeWidget(widget)
                    widget.deleteLater()

            # Добавляем сообщение об отсутствии уведомлений
            self.scroll_layout.insertWidget(0, self.empty_label)

    def stop_updates(self):
        """Остановка автообновления уведомлений"""
        self.is_active = False
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

    def on_notification_clicked(self, message_data):
        """Обработка клика на уведомлении"""
        try:
            print(f"Открытие диалога для сообщения {message_data['id']}")

            # ОСТАНАВЛИВАЕМ ТАЙМЕР при открытии диалога
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()
                print("Таймер автообновления остановлен")

            dialog = ViewMessageDialog(message_data, self.main_window)

            def safe_remove():
                try:
                    self.immediately_remove_notification(message_data['id'])
                except Exception as e:
                    print(f"Ошибка при удалении уведомления из safe_remove: {e}")
                finally:
                    # ЗАПУСКАЕМ ТАЙМЕР снова при закрытии диалога
                    if hasattr(self, 'update_timer') and not self.update_timer.isActive():
                        self.update_timer.start(30000)
                        print("Таймер автообновления запущен")

            dialog.finished.connect(safe_remove)
            dialog.exec()

        except Exception as e:
            print(f"Ошибка открытия диалога сообщения: {e}")
            # Если произошла ошибка, все равно запускаем таймер
            if hasattr(self, 'update_timer') and not self.update_timer.isActive():
                self.update_timer.start(30000)