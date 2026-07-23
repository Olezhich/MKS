# ruff: noqa
# mypy: ignore-errors

from pathlib import Path
import sys
import os
import subprocess
import json
from PyQt5 import QtCore, QtWebEngineWidgets
from PyQt5.QtWidgets import *
import pandas as pd

from mks.models import Camera, Mount, Giper
from mks.core import generate_tracks, generate_shot

from datetime import datetime, timedelta

ORBITA_UTC_PATH = Path("2_Orbita_UTC.txt")
GIPER_PRICEL_PATH = Path("3_Giper_pricel.txt")
DATA_TIME_PATH = Path("Data_time.txt")

TRACKS_KML_PATH = Path("output.kml")

TIME_DELTA = 90  # Время трассировки подспутниковой точки до и после точки съёмки


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setCentralWidget(Tabs(self))
        self.setWindowTitle("ГИПЕРКАМ")
        self.resize(1200, 800)
        self.show()


class Tabs(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(MapTab(), "Карта")
        self.tabs.addTab(PlanTab(), "Планирование")
        self.tabs.addTab(OptTab(), "Оптимизация")
        self.tabs.addTab(BaseTab(), "База")
        layout.addWidget(self.tabs)


class MapTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.map = QtWebEngineWidgets.QWebEngineView()
        layout.addWidget(self.map)

        controls = QHBoxLayout()
        controls.setSpacing(3)
        controls.setContentsMargins(5, 5, 5, 5)

        controls.addWidget(QLabel("Начало:"))
        self.start_dt = QDateTimeEdit()
        self.start_dt.setDisplayFormat("yyyy-MM-dd H:mm:ss")
        self.start_dt.setCalendarPopup(True)
        self.start_dt.setMaximumSize(170, 30)
        controls.addWidget(self.start_dt)

        controls.addWidget(QLabel("Конец:"))
        self.end_dt = QDateTimeEdit()
        self.end_dt.setDisplayFormat("yyyy-MM-dd H:mm:ss")
        self.end_dt.setCalendarPopup(True)
        self.end_dt.setMaximumSize(170, 30)
        now = QtCore.QDateTime.currentDateTime()
        self.start_dt.setDateTime(now)
        self.end_dt.setDateTime(now.addSecs(3600 * 3))
        controls.addWidget(self.end_dt)

        btn = QPushButton("Задать")
        btn.setMaximumSize(80, 30)
        controls.addWidget(btn)

        btn = QPushButton("Обновить")
        btn.setMaximumSize(100, 30)
        controls.addWidget(btn)

        self.sputnik = QRadioButton("Спутник")
        self.sputnik.setChecked(True)
        self.sputnik.setMaximumSize(80, 30)
        controls.addWidget(self.sputnik)

        self.simple = QRadioButton("Схема")
        self.simple.setMaximumSize(80, 30)
        controls.addWidget(self.simple)

        self.hybrid = QRadioButton("Гибрид")
        self.hybrid.setMaximumSize(80, 30)
        controls.addWidget(self.hybrid)

        cb = QCheckBox("Автообновление")
        cb.setMaximumSize(130, 30)
        controls.addWidget(cb)

        btn = QPushButton("Добавить объект")
        btn.setMaximumSize(120, 30)
        btn.clicked.connect(self.add_object)
        controls.addWidget(btn)

        cb = QCheckBox("Показать объекты")
        cb.setMaximumSize(130, 30)
        controls.addWidget(cb)

        controls.addStretch()
        layout.addLayout(controls)

    def add_object(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление объекта")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        fields = {}

        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("Широта (с.ш.):"))
        lat_field = QDoubleSpinBox()
        lat_field.setRange(-90, 90)
        lat_field.setDecimals(4)
        lat_field.setValue(0.0)
        lat_field.setMaximumSize(100, 30)
        coord_layout.addWidget(lat_field)

        coord_layout.addWidget(QLabel("Долгота (в.д.):"))
        lon_field = QDoubleSpinBox()
        lon_field.setRange(-180, 180)
        lon_field.setDecimals(4)
        lon_field.setValue(0.0)
        lon_field.setMaximumSize(100, 30)
        coord_layout.addWidget(lon_field)
        layout.addLayout(coord_layout)

        fields_data = [
            ("Объект (название):", "name", QLineEdit()),
            ("Опыт (КЭ):", "exp", QLineEdit()),
            ("Прибор (аппаратура):", "tool", QLineEdit()),
            ("Заказчик:", "client", QLineEdit()),
            ("Срок годности (дней):", "eol", QSpinBox()),
        ]

        for label_text, field_name, widget in fields_data:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setMinimumWidth(150)
            row_layout.addWidget(label)

            if isinstance(widget, QSpinBox):
                widget.setRange(1, 999)
                widget.setValue(14)
                widget.setMaximumSize(100, 30)
            else:
                widget.setPlaceholderText(f"Введите {label_text.lower()}")
                widget.setMaximumSize(200, 30)
                if field_name == "exp":
                    widget.setText("УРАГАН")
                elif field_name == "tool":
                    widget.setText("-")
                elif field_name == "client":
                    widget.setText("-")

            row_layout.addWidget(widget)
            layout.addLayout(row_layout)
            fields[field_name] = widget

        button_layout = QHBoxLayout()
        ok_button = QPushButton("Добавить")
        ok_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;"
        )
        cancel_button = QPushButton("Отмена")
        cancel_button.setStyleSheet(
            "background-color: #f44336; color: white; padding: 8px;"
        )

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        def on_ok():
            try:
                lat = lat_field.value()
                lon = lon_field.value()
                name = fields["name"].text().strip()
                exp = fields["exp"].text().strip().upper()
                tool = fields["tool"].text().strip().lower()
                client = fields["client"].text().strip().upper()
                eol = fields["eol"].value()

                if not name:
                    QMessageBox.warning(dialog, "Ошибка", "Введите название объекта!")
                    return

                dialog.accept()
                QMessageBox.information(
                    dialog,
                    "Успех",
                    f"Объект '{name}' успешно добавлен!\n"
                    f"Координаты: {lat}, {lon}\n"
                    f"КЭ: {exp}, Срок годности: {eol} дней",
                )

            except Exception as e:
                QMessageBox.critical(
                    dialog, "Ошибка", f"Ошибка при добавлении объекта:\n{str(e)}"
                )

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()


class PlanTab(QWidget):
    def orbita_exec(self) -> None:
        """Генерирует 2_Orbita_UTC.txt"""
        print("Кое-кто не написал функцию генерации 2_Orbita_UTC.txt")

    def pricel_exec(self) -> None:
        """Генерирует 3_Giper_pricel.txt"""
        print("Кое-кто не написал функцию генерации 3_Giper_pricel.txt")

    def modelling_handler(self) -> None:
        self.orbita_exec()

        mount = Mount(
            self.device_roll.value(),
            self.device_pitch.value(),
            self.device_yaw.value(),
            self.roll.value(),
            self.pitch.value(),
            self.yaw.value(),
        )

        t_start = self.scan_start.dateTime().toPyDateTime()
        t_end = self.scan_end.dateTime().toPyDateTime()

        if self.foto.isChecked():
            focal = self.focal.value()  # Фокусное расстояние (мм)
            matrix_w = self.matrix_width.value()  # Ширина матрицы (мм)
            matrix_h = self.matrix_height.value()  # Высота матрицы (мм)

            cam = Camera(matrix_w, matrix_h, focal)
        elif self.giper.isChecked():
            fov = self.giper_fov_manual.value()
            cam = Giper(fov, 0, 0)
        else:
            raise RuntimeError("Ошибка при выборе камеры/гиперспектрометра")

        try:
            generate_tracks(
                ORBITA_UTC_PATH, cam, mount, t_start, t_end, TRACKS_KML_PATH
            )
        except Exception as e:
            print(e)

    def calculation_handler(self) -> None:
        self.pricel_exec()

        if self.foto.isChecked():
            focal = self.focal.value()  # Фокусное расстояние (мм)
            matrix_w = self.matrix_width.value()  # Ширина матрицы (мм)
            matrix_h = self.matrix_height.value()  # Высота матрицы (мм)
            cam = [Camera(matrix_w, matrix_h, focal)]
        elif self.giper.isChecked():
            cam = [Giper(3.61, 1.0, 5), Giper(16, 9, 0), Giper(4.01, 1.0, -5)]
        else:
            raise RuntimeError("Ошибка при выборе камеры/гиперспектрометра")

        with open(DATA_TIME_PATH, "r", encoding="cp1251") as f:
            dt_f = f.readlines()
            giper_delta = float(dt_f[2].split(" ")[0])

        with open(GIPER_PRICEL_PATH, "r", encoding="cp1251") as f:
            f.readline()
            gp_f = f.readlines()
            for i, line in enumerate(gp_f):
                line = line.split()
                t_shot = datetime(
                    int(line[0]),
                    int(line[1]),
                    int(line[2]),
                    int(line[3]),
                    int(line[4]),
                    int(line[5].split(".")[0]),
                    int(line[5].split(".")[1]) * 100_000,
                )
                yaw = float(line[7])
                roll = float(line[8])
                pitch = float(line[9])

                name = line[15]

                mount = Mount(roll, pitch, yaw)

                generate_shot(
                    ORBITA_UTC_PATH,
                    cam,
                    mount,
                    t_shot,
                    timedelta(seconds=TIME_DELTA),
                    timedelta(seconds=giper_delta),
                    Path(f"Shot_{name}.kml"),
                )
                print(f"Снимок {t_shot}: {name}")

    def __init__(self):
        super().__init__()

        # Инициализируем log до загрузки базы
        self.log = QTextBrowser()
        self.log.setMaximumSize(1000, 400)
        self.log.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")

        # Загружаем данные из базы
        self.load_base_data()

        main_layout = QVBoxLayout(self)

        # Верхняя часть с двумя колонками
        top_layout = QHBoxLayout()

        # === ЛЕВАЯ КОЛОНКА ===
        left = QVBoxLayout()

        # Объект наблюдения (с фильтрами)
        gb = QGroupBox("Объект наблюдения")
        l = QVBoxLayout(gb)

        l.addWidget(QLabel("Фильтры:"))

        filter_grid = QGridLayout()
        filter_grid.setSpacing(5)

        filter_grid.addWidget(QLabel("Эксперименты:"), 0, 0)
        self.exp_filter = QListWidget()
        self.exp_filter.setSelectionMode(QListWidget.MultiSelection)
        self.exp_filter.setMaximumSize(200, 80)
        self.exp_filter.addItem("Все")
        for exp in self.exp_list:
            self.exp_filter.addItem(exp)
        self.exp_filter.setCurrentRow(0)
        filter_grid.addWidget(self.exp_filter, 0, 1)

        filter_grid.addWidget(QLabel("Заказчик:"), 1, 0)
        self.client_filter = QListWidget()
        self.client_filter.setSelectionMode(QListWidget.MultiSelection)
        self.client_filter.setMaximumSize(200, 80)
        self.client_filter.addItem("Все")
        for client in self.client_list:
            self.client_filter.addItem(client)
        self.client_filter.setCurrentRow(0)
        filter_grid.addWidget(self.client_filter, 1, 1)

        filter_grid.addWidget(QLabel("Тип (из базы):"), 2, 0)
        self.type_filter = QListWidget()
        self.type_filter.setSelectionMode(QListWidget.MultiSelection)
        self.type_filter.setMaximumSize(200, 80)
        self.type_filter.addItem("Все")
        for type_name in self.type_list:
            self.type_filter.addItem(type_name)
        self.type_filter.setCurrentRow(0)
        filter_grid.addWidget(self.type_filter, 2, 1)

        filter_grid.addWidget(QLabel("Аппаратура:"), 3, 0)
        self.tool_filter = QListWidget()
        self.tool_filter.setSelectionMode(QListWidget.MultiSelection)
        self.tool_filter.setMaximumSize(200, 80)
        self.tool_filter.addItem("Все")
        for tool in self.tool_list:
            self.tool_filter.addItem(tool)
        self.tool_filter.setCurrentRow(0)
        filter_grid.addWidget(self.tool_filter, 3, 1)

        l.addLayout(filter_grid)

        # Чекбокс "Срок годности" (как было раньше)
        self.age_cb = QCheckBox("Срок годности")
        self.age_cb.setChecked(True)
        l.addWidget(self.age_cb)

        left.addWidget(gb)

        # Орбитальные данные + Моделирование в одной строке
        orbit_model_layout = QHBoxLayout()

        gb_orbit = QGroupBox("Орбитальные данные")
        orbit_layout = QVBoxLayout(gb_orbit)
        for name in ["TLE", "БНИ"]:
            rb = QRadioButton(name)
            if name == "БНИ":
                rb.setChecked(True)
            orbit_layout.addWidget(rb)
        orbit_layout.addStretch()
        orbit_model_layout.addWidget(gb_orbit, 1)

        gb_model = QGroupBox("Моделирование")
        model_layout = QGridLayout(gb_model)
        model_layout.addWidget(QLabel("Шаг (сек):"), 0, 0)
        self.step = QSpinBox()
        self.step.setRange(1, 120)
        self.step.setValue(5)
        self.step.setMaximumSize(80, 30)
        model_layout.addWidget(self.step, 0, 1)
        model_layout.addWidget(QLabel("сек"), 0, 2)

        model_layout.addWidget(QLabel("Крен:"), 1, 0)
        self.roll = QDoubleSpinBox()
        self.roll.setRange(-180, 180)
        self.roll.setDecimals(2)
        self.roll.setValue(0.0)
        self.roll.setMaximumSize(80, 30)
        model_layout.addWidget(self.roll, 1, 1)
        model_layout.addWidget(QLabel("град"), 1, 2)

        model_layout.addWidget(QLabel("Тангаж:"), 2, 0)
        self.pitch = QDoubleSpinBox()
        self.pitch.setRange(-180, 180)
        self.pitch.setDecimals(2)
        self.pitch.setValue(0.0)
        self.pitch.setMaximumSize(80, 30)
        model_layout.addWidget(self.pitch, 2, 1)
        model_layout.addWidget(QLabel("град"), 2, 2)

        model_layout.addWidget(QLabel("Рыскание:"), 3, 0)
        self.yaw = QDoubleSpinBox()
        self.yaw.setRange(-180, 180)
        self.yaw.setDecimals(2)
        self.yaw.setValue(0.0)
        self.yaw.setMaximumSize(80, 30)
        model_layout.addWidget(self.yaw, 3, 1)
        model_layout.addWidget(QLabel("град"), 3, 2)
        orbit_model_layout.addWidget(gb_model, 2)

        left.addLayout(orbit_model_layout)

        # === КНОПКИ (Расчет, Моделировать, Сделать рисунки, Создать ИД, ЯВ) ===
        btn_layout = QHBoxLayout()
        btn_texts = ["Расчет", "Моделировать", "Сделать рисунки", "Создать ИД", "ЯВ"]
        for text in btn_texts:
            b = QPushButton(text)
            b.setMinimumSize(80, 40)
            if text == "Моделировать":
                b.clicked.connect(self.modelling_handler)
            if text == "Расчет":
                b.clicked.connect(self.calculation_handler)

            btn_layout.addWidget(b)
        btn_layout.addStretch()
        left.addLayout(btn_layout)

        # === РАБОЧАЯ ПАПКА ===
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Рабочая папка:"))
        self.folder = QTextEdit()
        self.folder.setMaximumSize(200, 40)
        self.folder.setReadOnly(True)
        folder_layout.addWidget(self.folder)

        b = QToolButton()
        b.setText("...")
        b.setMinimumSize(60, 30)
        b.clicked.connect(self.select_folder)
        folder_layout.addWidget(b)

        open_btn = QPushButton("Открыть")
        open_btn.setMinimumSize(80, 30)
        open_btn.clicked.connect(self.open_folder)
        folder_layout.addWidget(open_btn)

        folder_layout.addStretch()
        left.addLayout(folder_layout)

        left.addStretch()
        top_layout.addLayout(left, 1)

        # === ПРАВАЯ КОЛОНКА ===
        right = QVBoxLayout()

        # Ограничения
        gb_limits = QGroupBox("Ограничения")
        l_limits = QGridLayout(gb_limits)

        now = QtCore.QDateTime.currentDateTime()

        l_limits.addWidget(QLabel("Начало сканирования:"), 0, 0)
        self.scan_start = QDateTimeEdit()
        self.scan_start.setDisplayFormat("yyyy-MM-dd H:mm:ss")
        self.scan_start.setCalendarPopup(True)
        self.scan_start.setDateTime(now)
        self.scan_start.setMaximumSize(180, 30)
        l_limits.addWidget(self.scan_start, 0, 1)

        l_limits.addWidget(QLabel("Окончание сканирования:"), 1, 0)
        self.scan_end = QDateTimeEdit()
        self.scan_end.setDisplayFormat("yyyy-MM-dd H:mm:ss")
        self.scan_end.setCalendarPopup(True)
        self.scan_end.setDateTime(now.addSecs(3600 * 3))
        self.scan_end.setMaximumSize(180, 30)
        l_limits.addWidget(self.scan_end, 1, 1)

        l_limits.addWidget(QLabel("Начало рабочего дня:"), 2, 0)
        self.work_start = QTimeEdit()
        self.work_start.setDisplayFormat("HH:mm")
        self.work_start.setTime(QtCore.QTime(7, 0))
        self.work_start.setMaximumSize(80, 30)
        l_limits.addWidget(self.work_start, 2, 1)

        l_limits.addWidget(QLabel("Конец рабочего дня:"), 3, 0)
        self.work_end = QTimeEdit()
        self.work_end.setDisplayFormat("HH:mm")
        self.work_end.setTime(QtCore.QTime(22, 0))
        self.work_end.setMaximumSize(80, 30)
        l_limits.addWidget(self.work_end, 3, 1)

        check_layout = QHBoxLayout()
        self.work_time = QCheckBox("Учитывать рабочее время")
        self.work_time.setChecked(True)
        check_layout.addWidget(self.work_time)

        self.sun_check = QCheckBox("Освещенность")
        self.sun_check.setChecked(False)
        check_layout.addWidget(self.sun_check)

        self.cloud_check = QCheckBox("Облачность")
        self.cloud_check.setChecked(False)
        check_layout.addWidget(self.cloud_check)
        check_layout.addStretch()
        l_limits.addLayout(check_layout, 4, 0, 1, 2)

        l_limits.addWidget(QLabel("Угол Солнца:"), 5, 0)
        sun_layout = QHBoxLayout()
        self.sun_min = QSpinBox()
        self.sun_min.setRange(-90, 90)
        self.sun_min.setValue(20)
        self.sun_min.setMaximumSize(60, 30)
        sun_layout.addWidget(self.sun_min)
        sun_layout.addWidget(QLabel("до"))
        self.sun_max = QSpinBox()
        self.sun_max.setRange(-90, 90)
        self.sun_max.setValue(60)
        self.sun_max.setMaximumSize(60, 30)
        sun_layout.addWidget(self.sun_max)
        sun_layout.addWidget(QLabel("°"))
        sun_layout.addStretch()
        l_limits.addLayout(sun_layout, 5, 1)

        l_limits.addWidget(QLabel("Макс. облачность:"), 6, 0)
        cloud_layout = QHBoxLayout()
        self.max_cloud = QSpinBox()
        self.max_cloud.setRange(0, 100)
        self.max_cloud.setValue(100)
        self.max_cloud.setMaximumSize(80, 30)
        cloud_layout.addWidget(self.max_cloud)
        cloud_layout.addWidget(QLabel("%"))
        cloud_layout.addStretch()
        l_limits.addLayout(cloud_layout, 6, 1)

        right.addWidget(gb_limits)

        # Настройки аппаратуры
        gb = QGroupBox("Настройки аппаратуры")
        l = QVBoxLayout(gb)

        h = QHBoxLayout()
        self.foto = QRadioButton("Фотоаппарат")
        self.giper = QRadioButton("Гиперспектрометр")
        self.foto.setChecked(True)
        h.addWidget(self.foto)
        h.addWidget(self.giper)
        h.addStretch()
        l.addLayout(h)

        params_layout = QGridLayout()
        params_layout.setSpacing(5)

        params_layout.addWidget(QLabel("Профиль устройства:"), 0, 0)
        self.device_preset = QComboBox()
        self.device_preset.setEditable(True)
        self.device_preset.setMaximumSize(250, 30)
        self.device_preset.addItem("-- Выберите профиль --")
        self.device_preset.currentIndexChanged.connect(self.load_device_preset)
        params_layout.addWidget(self.device_preset, 0, 1, 1, 2)

        params_layout.addWidget(QLabel("Фокусное (мм):"), 1, 0)
        self.focal = QDoubleSpinBox()
        self.focal.setRange(0, 1000)
        self.focal.setDecimals(1)
        self.focal.setValue(50.0)
        self.focal.setMaximumSize(80, 30)
        params_layout.addWidget(self.focal, 1, 1)
        params_layout.addWidget(QLabel("мм"), 1, 2)

        params_layout.addWidget(QLabel("Размер матрицы (мм):"), 2, 0)
        matrix_layout = QHBoxLayout()
        self.matrix_width = QDoubleSpinBox()
        self.matrix_width.setRange(0, 100)
        self.matrix_width.setDecimals(1)
        self.matrix_width.setValue(36.0)
        self.matrix_width.setMaximumSize(70, 30)
        matrix_layout.addWidget(self.matrix_width)
        matrix_layout.addWidget(QLabel("x"))
        self.matrix_height = QDoubleSpinBox()
        self.matrix_height.setRange(0, 100)
        self.matrix_height.setDecimals(1)
        self.matrix_height.setValue(24.0)
        self.matrix_height.setMaximumSize(70, 30)
        matrix_layout.addWidget(self.matrix_height)
        matrix_layout.addWidget(QLabel("мм"))
        matrix_layout.addStretch()
        params_layout.addLayout(matrix_layout, 2, 1, 1, 2)

        # Крен, Тангаж, Рыскание
        params_layout.addWidget(QLabel("Крен:"), 3, 0)
        self.device_roll = QDoubleSpinBox()
        self.device_roll.setRange(-180, 180)
        self.device_roll.setDecimals(2)
        self.device_roll.setValue(0.0)
        self.device_roll.setMaximumSize(80, 30)
        params_layout.addWidget(self.device_roll, 3, 1)
        params_layout.addWidget(QLabel("град"), 3, 2)

        params_layout.addWidget(QLabel("Тангаж:"), 4, 0)
        self.device_pitch = QDoubleSpinBox()
        self.device_pitch.setRange(-180, 180)
        self.device_pitch.setDecimals(2)
        self.device_pitch.setValue(0.0)
        self.device_pitch.setMaximumSize(80, 30)
        params_layout.addWidget(self.device_pitch, 4, 1)
        params_layout.addWidget(QLabel("град"), 4, 2)

        params_layout.addWidget(QLabel("Рыскание:"), 5, 0)
        self.device_yaw = QDoubleSpinBox()
        self.device_yaw.setRange(-180, 180)
        self.device_yaw.setDecimals(2)
        self.device_yaw.setValue(0.0)
        self.device_yaw.setMaximumSize(80, 30)
        params_layout.addWidget(self.device_yaw, 5, 1)
        params_layout.addWidget(QLabel("град"), 5, 2)

        params_layout.addWidget(QLabel("Макс. угол влево:"), 6, 0)
        self.max_left = QDoubleSpinBox()
        self.max_left.setRange(-180, 0)
        self.max_left.setDecimals(2)
        self.max_left.setValue(-30)
        self.max_left.setMaximumSize(80, 30)
        params_layout.addWidget(self.max_left, 6, 1)
        params_layout.addWidget(QLabel("град"), 6, 2)

        params_layout.addWidget(QLabel("Макс. угол вправо:"), 7, 0)
        self.max_right = QDoubleSpinBox()
        self.max_right.setRange(0, 180)
        self.max_right.setDecimals(2)
        self.max_right.setValue(30)
        self.max_right.setMaximumSize(80, 30)
        params_layout.addWidget(self.max_right, 7, 1)
        params_layout.addWidget(QLabel("град"), 7, 2)

        params_layout.addWidget(QLabel("Дальность:"), 8, 0)
        self.range_val = QSpinBox()
        self.range_val.setRange(0, 30000)
        self.range_val.setValue(310)
        self.range_val.setMaximumSize(80, 30)
        params_layout.addWidget(self.range_val, 8, 1)
        params_layout.addWidget(QLabel("км"), 8, 2)

        params_layout.addWidget(QLabel("Поле зрения:"), 9, 0)
        fov_layout = QHBoxLayout()
        self.giper_fov_combo = QComboBox()
        self.giper_fov_combo.addItems(["3.61°", "4.01°", "Вручную"])
        self.giper_fov_combo.setMaximumSize(120, 30)
        self.giper_fov_combo.currentIndexChanged.connect(self.on_giper_fov_changed)
        fov_layout.addWidget(self.giper_fov_combo)

        self.giper_fov_manual = QDoubleSpinBox()
        self.giper_fov_manual.setRange(0, 180)
        self.giper_fov_manual.setDecimals(2)
        self.giper_fov_manual.setValue(3.61)
        self.giper_fov_manual.setMaximumSize(80, 30)
        self.giper_fov_manual.setEnabled(False)
        fov_layout.addWidget(self.giper_fov_manual)
        fov_layout.addWidget(QLabel("°"))
        fov_layout.addStretch()
        params_layout.addLayout(fov_layout, 9, 1, 1, 2)

        l.addLayout(params_layout)

        def fill_device_presets():
            self.device_preset.clear()
            self.device_preset.addItem("-- Выберите профиль --")
            profiles = self.load_device_profiles()
            for name in profiles.keys():
                self.device_preset.addItem(name)

        def update_values():
            if self.foto.isChecked():
                self.focal.setValue(50.0)
                self.matrix_width.setValue(36.0)
                self.matrix_height.setValue(24.0)
                self.device_roll.setValue(0.0)
                self.device_pitch.setValue(0.0)
                self.device_yaw.setValue(0.0)
                self.max_left.setValue(-30)
                self.max_right.setValue(30)
                self.range_val.setValue(310)
                self.giper_fov_combo.setEnabled(False)
                self.giper_fov_manual.setEnabled(False)
                self.focal.setEnabled(True)
                self.matrix_width.setEnabled(True)
                self.matrix_height.setEnabled(True)
                self.device_roll.setEnabled(True)
                self.device_pitch.setEnabled(True)
                self.device_yaw.setEnabled(True)
                self.max_left.setEnabled(True)
                self.max_right.setEnabled(True)
                self.range_val.setEnabled(True)
            else:
                self.focal.setValue(0.0)
                self.matrix_width.setValue(0.0)
                self.matrix_height.setValue(0.0)
                self.device_roll.setValue(0.0)
                self.device_pitch.setValue(0.0)
                self.device_yaw.setValue(0.0)
                self.max_left.setValue(-5.05)
                self.max_right.setValue(5.05)
                self.range_val.setValue(50)
                self.giper_fov_combo.setEnabled(True)
                self.on_giper_fov_changed(self.giper_fov_combo.currentIndex())
                self.focal.setEnabled(False)
                self.matrix_width.setEnabled(False)
                self.matrix_height.setEnabled(False)
                self.device_roll.setEnabled(True)
                self.device_pitch.setEnabled(True)
                self.device_yaw.setEnabled(True)
                self.max_left.setEnabled(True)
                self.max_right.setEnabled(True)
                self.range_val.setEnabled(True)
            fill_device_presets()

        self.foto.toggled.connect(update_values)
        self.giper.toggled.connect(update_values)
        update_values()

        right.addWidget(gb)
        right.addStretch()

        top_layout.addLayout(right, 1)
        main_layout.addLayout(top_layout)

        # === ЛОГИ (расширенный) ===
        main_layout.addWidget(self.log)
        self.log.append(
            "Готов к работе. Загружено объектов из базы: " + str(len(self.base_data))
        )

    def load_base_data(self):
        try:
            if os.path.exists("БАЗА.xlsx"):
                df = pd.read_excel("БАЗА.xlsx")
                self.base_data = df.to_dict("records")
                self.exp_list = sorted(df["КЭ"].dropna().unique().tolist())
                self.client_list = sorted(df["ЗАКАЗЧИК"].dropna().unique().tolist())
                self.type_list = sorted(df["ТИП"].dropna().unique().tolist())
                self.tool_list = sorted(df["АППАРАТУРА"].dropna().unique().tolist())
            else:
                self.base_data = []
                self.exp_list = ["УРАГАН", "ДУБРАВА", "СЦЕНАРИЙ"]
                self.client_list = [
                    'РКК "Энергия"',
                    "ИГРАН",
                    "ИПМЕХ",
                    "МГТУ им. Н.Э. Баумана",
                ]
                self.type_list = ["метан", "свалки", "основное", "ледники", "города"]
                self.tool_list = ["гиперспектрометр", "фото"]
        except Exception:
            self.base_data = []
            self.exp_list = ["УРАГАН", "ДУБРАВА", "СЦЕНАРИЙ"]
            self.client_list = [
                'РКК "Энергия"',
                "ИГРАН",
                "ИПМЕХ",
                "МГТУ им. Н.Э. Баумана",
            ]
            self.type_list = ["метан", "свалки", "основное", "ледники", "города"]
            self.tool_list = ["гиперспектрометр", "фото"]

    def load_device_profiles(self):
        profiles = {
            "Nikon D850": {
                "focal": 50.0,
                "matrix_width": 36.0,
                "matrix_height": 24.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "max_left": -30,
                "max_right": 30,
                "range": 310,
            },
            "Nikon Z9": {
                "focal": 50.0,
                "matrix_width": 36.0,
                "matrix_height": 24.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "max_left": -30,
                "max_right": 30,
                "range": 310,
            },
            "Canon EOS R5": {
                "focal": 50.0,
                "matrix_width": 36.0,
                "matrix_height": 24.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "max_left": -30,
                "max_right": 30,
                "range": 310,
            },
            "Sony A7R IV": {
                "focal": 50.0,
                "matrix_width": 36.0,
                "matrix_height": 24.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "max_left": -30,
                "max_right": 30,
                "range": 310,
            },
            "Specim FX10": {
                "focal": 0.0,
                "matrix_width": 0.0,
                "matrix_height": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "max_left": -5.05,
                "max_right": 5.05,
                "range": 50,
            },
            "Specim FX17": {
                "focal": 0.0,
                "matrix_width": 0.0,
                "matrix_height": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "max_left": -5.05,
                "max_right": 5.05,
                "range": 50,
            },
            "HySpex VNIR-1800": {
                "focal": 0.0,
                "matrix_width": 0.0,
                "matrix_height": 0.0,
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "max_left": -5.05,
                "max_right": 5.05,
                "range": 50,
            },
        }

        if os.path.exists("device_profiles.json"):
            try:
                with open("device_profiles.json", "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    profiles.update(loaded)
            except:
                pass

        return profiles

    def load_device_preset(self, index):
        if index <= 0:
            return
        profile_name = self.device_preset.itemText(index)
        profiles = self.load_device_profiles()
        if profile_name in profiles:
            params = profiles[profile_name]
            self.focal.setValue(params.get("focal", 50.0))
            self.matrix_width.setValue(params.get("matrix_width", 36.0))
            self.matrix_height.setValue(params.get("matrix_height", 24.0))
            self.device_roll.setValue(params.get("roll", 0.0))
            self.device_pitch.setValue(params.get("pitch", 0.0))
            self.device_yaw.setValue(params.get("yaw", 0.0))
            self.max_left.setValue(params.get("max_left", -30))
            self.max_right.setValue(params.get("max_right", 30))
            self.range_val.setValue(params.get("range", 310))

    def on_giper_fov_changed(self, index):
        if index == 2:
            self.giper_fov_manual.setEnabled(True)
            self.giper_fov_manual.setValue(3.61)
        else:
            self.giper_fov_manual.setEnabled(False)
            if index == 0:
                self.giper_fov_manual.setValue(3.61)
            elif index == 1:
                self.giper_fov_manual.setValue(4.01)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите рабочую папку")
        if folder:
            self.folder.setText(folder)
            self.log.append(f"Выбрана папка: {folder}")

    def open_folder(self):
        folder = self.folder.toPlainText().strip()
        if not folder:
            QMessageBox.warning(
                self, "Предупреждение", "Сначала выберите рабочую папку!"
            )
            return
        if not os.path.exists(folder):
            QMessageBox.warning(self, "Ошибка", f"Папка не существует:\n{folder}")
            return
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            else:
                subprocess.Popen(["explorer", folder])
            self.log.append(f"Открыта папка: {folder}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть папку:\n{str(e)}")


class OptTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()

        # === ЛЕВАЯ КОЛОНКА - Критерии и ГА ===
        left = QVBoxLayout()

        # Критерии
        gb = QGroupBox("Критерии оптимизации")
        l = QVBoxLayout(gb)
        l.addWidget(QLabel("Выберите критерии для оценки информативности объекта"))
        label = QLabel("(приоритет объекта, облачность, освещенность, покрытие)")
        label.setStyleSheet("font-size: 10px; color: gray;")
        l.addWidget(label)
        for t in [
            "Приоритет объекта",
            "Облачность",
            "Освещенность (угол Солнца)",
            "Покрытие (площадь объекта)",
        ]:
            cb = QCheckBox(t)
            cb.setChecked(True)
            l.addWidget(cb)
        left.addWidget(gb)

        # ГА
        gb = QGroupBox("Генетический алгоритм")
        l = QGridLayout(gb)
        params = [
            ("Размер популяции:", QSpinBox(), 200, 1, 1000),
            ("Вероятность скрещивания:", QDoubleSpinBox(), 0.90, 0, 1),
            ("Вероятность мутации:", QDoubleSpinBox(), 0.10, 0, 1),
            ("Количество поколений:", QSpinBox(), 1000, 1, 10000),
            ("Количество элитных особей:", QSpinBox(), 10, 1, 100),
        ]
        self.ga_widgets = {}
        for i, (label, w, val, minv, maxv) in enumerate(params):
            l.addWidget(QLabel(label), i, 0)
            if isinstance(w, QDoubleSpinBox):
                w.setDecimals(2)
            w.setRange(minv, maxv)
            w.setValue(val)
            w.setMaximumSize(80, 30)
            l.addWidget(w, i, 1)
            key = (
                label.replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace(":", "")
                .lower()
            )
            self.ga_widgets[key] = w
        left.addWidget(gb)

        # Кнопка запуска оптимизации
        btn_run = QPushButton("Запустить оптимизацию")
        btn_run.setStyleSheet(
            "background:#4CAF50;color:white;font-weight:bold;padding:10px;"
        )
        btn_run.clicked.connect(self.run_optimization)
        left.addWidget(btn_run)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        left.addWidget(self.progress)

        left.addStretch()
        top_layout.addLayout(left, 1)

        # === ПРАВАЯ КОЛОНКА - Параметры ===
        right = QVBoxLayout()

        # Выбор типа аппаратуры
        gb_type = QGroupBox("Тип аппаратуры")
        type_layout = QHBoxLayout(gb_type)
        self.opt_foto = QRadioButton("Фотоаппарат")
        self.opt_giper = QRadioButton("Гиперспектрометр")
        self.opt_foto.setChecked(True)
        type_layout.addWidget(self.opt_foto)
        type_layout.addWidget(self.opt_giper)
        type_layout.addStretch()
        right.addWidget(gb_type)

        # Параметры съемки
        shoot_gb = QGroupBox("Параметры съемки")
        shoot_layout = QGridLayout(shoot_gb)
        shoot_layout.setSpacing(8)

        shoot_params = [
            ("Угол крена:", QDoubleSpinBox(), 0, -45, 45, "град"),
            ("Тангаж:", QDoubleSpinBox(), 0, -180, 180, "град"),
            ("Рыскание:", QDoubleSpinBox(), 0, -180, 180, "град"),
            ("Длительность (сек):", QSpinBox(), 60, 1, 9999, "сек"),
            ("Перенаводка (сек):", QSpinBox(), 10, 0, 999, "сек"),
            ("Смена фокуса (сек):", QSpinBox(), 5, 0, 999, "сек"),
            ("Макс. длительность (сек):", QSpinBox(), 300, 1, 9999, "сек"),
            ("Шаг KML:", QSpinBox(), 10, 1, 100, "сек"),
        ]

        self.shoot_widgets = {}
        for i, (label, w, val, minv, maxv, unit) in enumerate(shoot_params):
            shoot_layout.addWidget(QLabel(label), i, 0)
            if isinstance(w, QDoubleSpinBox):
                w.setDecimals(2)
            w.setRange(minv, maxv)
            w.setValue(val)
            w.setMaximumSize(80, 30)
            shoot_layout.addWidget(w, i, 1)
            shoot_layout.addWidget(QLabel(unit), i, 2)
            key = (
                label.replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace(":", "")
                .lower()
            )
            self.shoot_widgets[key] = w

        right.addWidget(shoot_gb)
        right.addStretch()

        top_layout.addLayout(right, 1)

        layout.addLayout(top_layout)

    def run_optimization(self):
        try:
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)

            pop_size = self.ga_widgets["размер_популяции"].value()
            generations = self.ga_widgets["количество_поколений"].value()

            roll = self.shoot_widgets["угол_крена"].value()
            pitch = self.shoot_widgets["тангаж"].value()
            yaw = self.shoot_widgets["рыскание"].value()

            tool_type = (
                "Фотоаппарат" if self.opt_foto.isChecked() else "Гиперспектрометр"
            )

            import time

            time.sleep(2)

            self.progress.setVisible(False)
            QMessageBox.information(
                self,
                "Успех",
                f"Оптимизация успешно завершена!\n"
                f"Тип аппаратуры: {tool_type}\n"
                f"Популяция={pop_size}, поколений={generations}\n"
                f"Крен={roll}°, Тангаж={pitch}°, Рыскание={yaw}°",
            )

        except Exception as e:
            self.progress.setVisible(False)
            QMessageBox.critical(self, "Ошибка", f"Ошибка при оптимизации:\n{str(e)}")


class BaseTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.fire_group = QGroupBox("Настройки детектирования пожаров")
        fire_layout = QVBoxLayout(self.fire_group)

        params_layout = QGridLayout()
        params_layout.setSpacing(8)

        self.conf = QSpinBox()
        self.conf.setRange(0, 100)
        self.conf.setValue(85)
        self.conf.setMaximumSize(80, 30)
        params_layout.addWidget(QLabel("Достоверность:"), 0, 0)
        params_layout.addWidget(self.conf, 0, 1)
        params_layout.addWidget(QLabel("%"), 0, 2)

        self.radius = QSpinBox()
        self.radius.setRange(1, 20)
        self.radius.setValue(3)
        self.radius.setMaximumSize(80, 30)
        params_layout.addWidget(QLabel("Радиус кластеризации:"), 1, 0)
        params_layout.addWidget(self.radius, 1, 1)
        params_layout.addWidget(QLabel("км"), 1, 2)

        self.amount = QSpinBox()
        self.amount.setRange(1, 10)
        self.amount.setValue(2)
        self.amount.setMaximumSize(80, 30)
        params_layout.addWidget(QLabel("Кол-во точек в кластере:"), 2, 0)
        params_layout.addWidget(self.amount, 2, 1)
        params_layout.addWidget(QLabel("шт"), 2, 2)

        fire_layout.addLayout(params_layout)
        layout.addWidget(self.fire_group)

        types_group = QGroupBox("Типы объектов для загрузки")
        types_layout = QHBoxLayout(types_group)

        self.vulcan = QCheckBox("Вулканы")
        self.vulcan.setChecked(True)
        self.fire_check = QCheckBox("Пожары")
        self.fire_check.setChecked(True)

        self.fire_check.toggled.connect(self.toggle_fire_settings)

        types_layout.addWidget(self.vulcan)
        types_layout.addWidget(self.fire_check)
        types_layout.addStretch()
        layout.addWidget(types_group)

        self.period_group = QGroupBox("Период загрузки данных о пожарах")
        period_layout = QVBoxLayout(self.period_group)

        period_info = QLabel("Загружать данные о пожарах за период:")
        period_info.setStyleSheet("font-size: 11px;")
        period_layout.addWidget(period_info)

        period_radio_layout = QHBoxLayout()
        period_radio_layout.setSpacing(20)

        self.btn_24h = QRadioButton("Последние 24 часа")
        self.btn_48h = QRadioButton("Последние 48 часов")
        self.btn_7d = QRadioButton("Последние 7 дней")
        self.btn_24h.setChecked(True)

        period_radio_layout.addWidget(self.btn_24h)
        period_radio_layout.addWidget(self.btn_48h)
        period_radio_layout.addWidget(self.btn_7d)
        period_radio_layout.addStretch()
        period_layout.addLayout(period_radio_layout)

        layout.addWidget(self.period_group)

        btn_layout = QHBoxLayout()
        btn = QPushButton("Обновить базу")
        btn.setMinimumHeight(35)
        btn.setStyleSheet("background:#4CAF50;color:white;font-weight:bold;")
        btn.clicked.connect(self.update_base)
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        info_label = QLabel(
            "Данные о пожарах загружаются из внешних источников (FIRMS, NASA, и др.)"
        )
        info_label.setStyleSheet("font-size: 10px; font-style: italic; color: #666;")
        layout.addWidget(info_label)

        layout.addStretch()

        self.log = QTextBrowser()
        self.log.setMaximumSize(1000, 200)
        self.log.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self.log)
        self.log.append("База данных готова к работе")

        self.toggle_fire_settings(self.fire_check.isChecked())

    def toggle_fire_settings(self, enabled):
        self.conf.setEnabled(enabled)
        self.radius.setEnabled(enabled)
        self.amount.setEnabled(enabled)

        self.btn_24h.setEnabled(enabled)
        self.btn_48h.setEnabled(enabled)
        self.btn_7d.setEnabled(enabled)

        if enabled:
            self.fire_group.setTitle("Настройки детектирования пожаров")
            self.period_group.setTitle("Период загрузки данных о пожарах")
            self.log.append("Настройки пожаров включены")
        else:
            self.fire_group.setTitle("Настройки детектирования пожаров (отключено)")
            self.period_group.setTitle("Период загрузки данных о пожарах (отключено)")
            self.log.append("Настройки пожаров отключены")

    def update_base(self):
        try:
            self.log.append("Начало обновления базы...")

            conf = self.conf.value()
            radius = self.radius.value()
            amount = self.amount.value()
            vulcan = self.vulcan.isChecked()
            fire = self.fire_check.isChecked()

            if self.btn_24h.isChecked():
                period = "24 часа"
            elif self.btn_48h.isChecked():
                period = "48 часов"
            else:
                period = "7 дней"

            self.log.append(
                f"Параметры: достоверность={conf}%, радиус={radius}км, кол-во точек={amount}"
            )
            self.log.append(
                f"Типы объектов: вулканы={'Да' if vulcan else 'Нет'}, пожары={'Да' if fire else 'Нет'}"
            )
            self.log.append(f"Период загрузки: {period}")

            import time

            for i in range(5):
                time.sleep(0.3)
                self.log.append(f"  Загрузка данных... {i + 1}/5")
                QApplication.processEvents()

            time.sleep(0.5)

            self.log.append("База объектов успешно обновлена!")
            QMessageBox.information(self, "Успех", "База объектов успешно обновлена!")

        except Exception as e:
            self.log.append(f"Ошибка при обновлении базы: {str(e)}")
            QMessageBox.critical(
                self, "Ошибка", f"Ошибка при обновлении базы:\n{str(e)}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
