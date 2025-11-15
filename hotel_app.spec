# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['login.py'],  # Главный файл приложения
    pathex=[],     # Пути для поиска модулей
    binaries=[],   # Внешние бинарные файлы
    datas=[
        # ВСЕ файлы из этих папок будут включены автоматически
        ('UI/', 'UI/'),
        ('admin/', 'admin/'),
        ('regist/', 'regist/'),
        ('staff/', 'staff/'),

        # Отдельные файлы
        ('Hotel_bd.db', '.'),
        ('sync_update.py', '.'),
        ('bd_manager.py', '.'),
        ('utils.py', '.'),
    ],
    hiddenimports=[
        # Стандартные библиотеки
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'sqlite3',
        'hashlib',
        'calendar',
        'datetime',
        'requests',
        'yadisk',

        # Ваши кастомные модули
        'regist.regist_exceptions',
        'admin.Add_Delete_sotrudnic',
        'admin.List_sotrudnic',
        'admin.Change_room',
        'admin.Download_Upload_data',
        'regist.guest_registration_window',
        'regist.massage_window',
        'staff.staff_script',
        'regist.guest_update_window',
    ],
    hookspath=[],      # Пути к кастомным хукам
    hooksconfig={},    # Конфигурация хуков
    runtime_hooks=[],  # Runtime хуки
    excludes=[],       # Исключаемые модули
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Создание PYZ архива
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Создание исполняемого файла
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HotelManagementSystem',  # Имя исполняемого файла
    debug=False,                   # Отладочная информация
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                      # Сжатие UPX (если установлен)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                 # Без консоли (оконное приложение)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                     # Можно добавить иконку: 'icon.ico'
)

# Сборка в один файл
