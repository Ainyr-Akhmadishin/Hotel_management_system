from PyQt6.QtWidgets import QDialog, QMessageBox, QMainWindow
from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6 import uic
import sqlite3
import os
from regist.regist_exceptions import FIOException, LowerNameError, PassportError, DateError, PhoneError


class CorrectionDialog(QMainWindow):
    correction_finished = pyqtSignal(list, int)

    def __init__(self, row_data, row_number, parent=None):
        super().__init__(parent)
        self.row_data = row_data
        self.row_number = row_number
        self.corrected_data = None

        try:
            # Загружаем UI
            ui_path = 'UI/Reg/Окно заселения гостя итог.ui'
            if not os.path.exists(ui_path):
                ui_path = '../UI/Reg/Окно заселения гостя итог.ui'

            uic.loadUi(ui_path, self)

            # Изменяем заголовок и название кнопки
            self.setWindowTitle(f"Исправление данных - Строка {row_number}")
            self.pushButton.setText("Сохранить исправления")
            self.label.setText(f"Исправление строки {row_number}")

            # Настраиваем маску телефона
            self.phone.setInputMask("+7(000)000-00-00")

            # ЗАПОЛНЯЕМ ПОЛЯ ПЕРВЫМИ
            self.populate_fields()

            # Настраиваем обработчики
            self.setup_star_handlers()
            self.setup_enter_handlers()

            self.remove_initial_stars()

            # Подключаем кнопку
            self.pushButton.clicked.connect(self.validate_and_save)

            # ОБНОВЛЯЕМ НОМЕРА ПОСЛЕ ЗАПОЛНЕНИЯ ПОЛЕЙ
            self.update_available_rooms()

            # Подключаем сигналы изменений дат
            self.dateIn.dateChanged.connect(self.update_available_rooms)
            self.dateOut.dateChanged.connect(self.update_available_rooms)

            # Устанавливаем размеры
            self.setMinimumWidth(400)
            self.setMinimumHeight(550)

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось загрузить окно исправления: {str(e)}")
            raise

    def remove_initial_stars(self):
        """Удаляет звездочки при начальном заполнении полей"""
        try:
            # Проверяем все поля и удаляем звездочки если они заполнены
            self.removeStar(self.label_2, self.name.text())
            self.removeStar(self.label_3, self.fam.text())
            self.removeStar(self.label_5, self.pas.text())
            self.removeStar(self.label_8, self.phone.text())
            self.removeStar(self.label_9, self.number.currentText())

            # ТАКЖЕ ДЛЯ ДАТ
            self.removeStar(self.label_6, self.dateIn.date().toString("yyyy-MM-dd"))
            self.removeStar(self.label_7, self.dateOut.date().toString("yyyy-MM-dd"))

        except Exception as e:
            print(f"Ошибка в remove_initial_stars: {e}")
    def setup_enter_handlers(self):
        """Обработчики нажатия Enter"""
        try:
            self.name.returnPressed.connect(lambda: self.fam.setFocus())
            self.fam.returnPressed.connect(lambda: self.otch.setFocus())
            self.otch.returnPressed.connect(lambda: self.pas.setFocus())
            self.pas.returnPressed.connect(lambda: self.phone.setFocus())
        except Exception as e:
            print(f"Ошибка в setup_enter_handlers: {e}")

    def setup_star_handlers(self):
        """Обработчики для удаления звездочек при заполнении"""
        try:
            self.name.textChanged.connect(lambda: self.removeStar(self.label_2, self.name.text()))
            self.fam.textChanged.connect(lambda: self.removeStar(self.label_3, self.fam.text()))
            self.pas.textChanged.connect(lambda: self.removeStar(self.label_5, self.pas.text()))
            self.phone.textChanged.connect(lambda: self.removeStar(self.label_8, self.phone.text()))
            self.number.currentTextChanged.connect(lambda: self.removeStar(self.label_9, self.number.currentText()))

            # ДОБАВЛЯЕМ ОБРАБОТЧИКИ ДЛЯ ДАТ
            self.dateIn.dateChanged.connect(
                lambda: self.removeStar(self.label_6, self.dateIn.date().toString("yyyy-MM-dd")))
            self.dateOut.dateChanged.connect(
                lambda: self.removeStar(self.label_7, self.dateOut.date().toString("yyyy-MM-dd")))

            # УДАЛЯЕМ ЗВЕЗДОЧКИ СРАЗУ ПОСЛЕ ЗАПОЛНЕНИЯ ПОЛЕЙ
            self.remove_initial_stars()

        except Exception as e:
            print(f"Ошибка в setup_star_handlers: {e}")

    def removeStar(self, label, filled):
        """Удаляет звездочку из label при заполнении поля"""
        try:
            if not hasattr(label, 'text'):
                return

            current_text = label.text()
            base_text = current_text.replace(' *', '')

            # Если поле заполнено и есть звездочка - убираем
            if filled and ' *' in current_text:
                label.setText(base_text)
            # Если поле пустое и нет звездочки - добавляем
            elif not filled and ' *' not in current_text:
                label.setText(f"{base_text} *")

        except Exception as e:
            print(f"Ошибка в removeStar: {e}")

    def populate_fields(self):
        """Заполнение полей данными из строки"""
        try:
            if len(self.row_data) >= 8:
                # Заполняем текстовые поля
                self.name.setText(str(self.row_data[0]) if self.row_data[0] else "")
                self.fam.setText(str(self.row_data[1]) if self.row_data[1] else "")
                self.otch.setText(str(self.row_data[2]) if self.row_data[2] else "")
                self.pas.setText(str(self.row_data[3]) if self.row_data[3] else "")

                # Телефон
                phone_text = str(self.row_data[4]) if self.row_data[4] else ""
                if phone_text and not phone_text.startswith('+7('):
                    digits = ''.join(filter(str.isdigit, phone_text))
                    if len(digits) >= 10:
                        phone_text = f"+7({digits[-10:-7]}){digits[-7:-4]}-{digits[-4:-2]}-{digits[-2:]}"
                self.phone.setText(phone_text)

                # Заполняем даты
                try:
                    check_in_str = str(self.row_data[5]) if self.row_data[5] else QDate.currentDate().toString(
                        "yyyy-MM-dd")
                    check_in = QDate.fromString(check_in_str, 'yyyy-MM-dd')
                    if check_in.isValid():
                        self.dateIn.setDate(check_in)
                    else:
                        self.dateIn.setDate(QDate.currentDate())
                except:
                    self.dateIn.setDate(QDate.currentDate())

                try:
                    check_out_str = str(self.row_data[6]) if self.row_data[6] else QDate.currentDate().addDays(
                        1).toString("yyyy-MM-dd")
                    check_out = QDate.fromString(check_out_str, 'yyyy-MM-dd')
                    if check_out.isValid():
                        self.dateOut.setDate(check_out)
                    else:
                        self.dateOut.setDate(QDate.currentDate().addDays(1))
                except:
                    self.dateOut.setDate(QDate.currentDate().addDays(1))

        except Exception as e:
            print(f"Ошибка в populate_fields: {e}")

    def update_available_rooms(self):
        """Обновление списка доступных номеров"""
        try:
            # Проверяем что даты инициализированы
            if not hasattr(self, 'dateIn') or not hasattr(self, 'dateOut') or not hasattr(self, 'number'):
                return

            check_in = self.dateIn.date().toString("yyyy-MM-dd")
            check_out = self.dateOut.date().toString("yyyy-MM-dd")

            conn = sqlite3.connect('Hotel_bd.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT r.room_number 
                FROM rooms r
                WHERE r.id NOT IN (
                    SELECT b.room_id 
                    FROM bookings b
                    WHERE b.check_out_date > ? AND b.check_in_date < ?
                )
                ORDER BY r.room_number
            ''', (check_in, check_out))

            available_rooms = [str(row[0]) for row in cursor.fetchall()]
            conn.close()

            current_room = self.number.currentText()
            self.number.clear()
            self.number.addItems(available_rooms)

            # УЛУЧШЕННАЯ ЛОГИКА ВЫБОРА НОМЕРА
            room_set = False

            # 1. Пытаемся установить исходный номер комнаты из данных
            if len(self.row_data) >= 8 and self.row_data[7]:
                original_room = str(self.row_data[7])
                if original_room in available_rooms:
                    self.number.setCurrentText(original_room)
                    room_set = True
                    print(f"Установлен исходный номер: {original_room}")

            # 2. Если исходный номер недоступен, пробуем текущий выбранный
            if not room_set and current_room and current_room in available_rooms:
                self.number.setCurrentText(current_room)
                room_set = True
                print(f"Установлен текущий номер: {current_room}")

            # 3. Если ничего не выбрано, выбираем первый доступный
            if not room_set and available_rooms:
                self.number.setCurrentText(available_rooms[0])
                print(f"Установлен первый доступный номер: {available_rooms[0]}")

            print(f"Доступные номера: {available_rooms}")
            print(f"Исходный номер из данных: {self.row_data[7] if len(self.row_data) >= 8 else 'N/A'}")

        except Exception as e:
            print(f"Ошибка в update_available_rooms: {e}")
            import traceback
            traceback.print_exc()

    def FIOCheck(self, field, field_name, required=True):
        """Проверка ФИО"""
        text = field.text().strip()
        field.setStyleSheet("")

        if not text:
            if required:
                field.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
                raise FIOException(f"Поле '{field_name}' не заполнено")
            else:
                return True

        if not text.isalpha():
            field.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise FIOException(f"Поле '{field_name}' должно содержать только буквы")

        if len(text) < 2:
            field.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise FIOException(f"Поле '{field_name}' должно быть не менее 2 символов")

    def FIOLowerCheck(self, field_name, field_fam, field_otchestvo):
        """Проверка регистра ФИО"""
        text_name = field_name.text().strip()
        text_fam = field_fam.text().strip()
        text_otch = field_otchestvo.text().strip()

        if not text_name.istitle() or not text_fam.istitle() or (text_otch and not text_otch.istitle()):
            raise LowerNameError(text_name, text_fam, text_otch)

    def PassportCheck(self, field_pas):
        """Проверка паспорта"""
        text_pas = field_pas.text().strip()

        if not text_pas:
            field_pas.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise PassportError("Паспорт не заполнен")

        if not text_pas.isdigit():
            field_pas.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise PassportError("Паспорт должен содержать только цифры")

    def PhoneCheck(self, field_phone):
        """Проверка телефона"""
        text_phone = field_phone.text().strip()

        if len(text_phone) < 16:
            field_phone.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise PhoneError("Номер должен быть заполнен полностью")

    def DateCheck(self, field_dateIn, field_dateOut):
        """Проверка дат"""
        date_in = field_dateIn.date()
        date_out = field_dateOut.date()

        field_dateIn.setStyleSheet("")
        field_dateOut.setStyleSheet("")

        if date_in > date_out:
            field_dateIn.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            field_dateOut.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise DateError("Дата заселения должна быть до даты выселения")

        if date_in < QDate.currentDate():
            field_dateIn.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
            raise DateError("Дата заселения не может быть в прошлом")

    def validate_and_save(self):
        """Проверка данных и сохранение исправлений"""
        try:
            # Проверяем данные
            self.FIOCheck(self.name, "Имя")
            self.FIOCheck(self.fam, "Фамилия")
            self.FIOCheck(self.otch, "Отчество", required=False)
            self.FIOLowerCheck(self.name, self.fam, self.otch)
            self.PassportCheck(self.pas)
            self.PhoneCheck(self.phone)
            self.DateCheck(self.dateIn, self.dateOut)

            # Проверяем что номер выбран
            if not self.number.currentText():
                self.number.setStyleSheet("border: 2px solid red; background-color: #FFE6E6;")
                raise Exception("Необходимо выбрать номер")

            # Собираем исправленные данные
            self.corrected_data = [
                self.name.text().strip(),
                self.fam.text().strip(),
                self.otch.text().strip(),
                self.pas.text().strip(),
                self.phone.text().strip(),
                self.dateIn.date().toString("yyyy-MM-dd"),
                self.dateOut.date().toString("yyyy-MM-dd"),
                self.number.currentText()
            ]

            # Отправляем сигнал и закрываем окно
            self.correction_finished.emit(self.corrected_data, self.row_number)
            self.close()

        except LowerNameError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.name.setText(e.first_name)
            self.fam.setText(e.last_name)
            self.otch.setText(e.third_name)

        except (PassportError, FIOException, DateError, PhoneError, Exception) as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def get_corrected_data(self):
        """Возвращает исправленные данные"""
        return self.corrected_data