from PyQt6.QtWidgets import QApplication


class FIOException(Exception):
    pass

class LowerNameError(Exception):
    def __init__(self, first_name, last_name, third_name):
        # Преобразуем имя и фамилию к заглавным буквам
        self.first_name = first_name.title()
        self.last_name = last_name.title()
        self.third_name = third_name.title()
        super().__init__(f"Имя и фамилия должны быть с заглавной буквы. Исправлено: {self.first_name} {self.last_name} {self.third_name}")

class PassportError(Exception):
    pass

class DateError(Exception):
    pass

class PhoneError(Exception):
    pass