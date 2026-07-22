from pathlib import Path

from mks.core import (
    calculate_sub_satellite_points,
    parse_telemetry_batch,
    create_kml_circle,
    create_kml_track,
    calculate_view_cam_points,
)
from mks.models import Giper, Mount

import numpy as np
import simplekml  # type: ignore

from datetime import datetime, timedelta


cam1 = Giper(3.61, 1.0, 5)
cam2 = Giper(16, 9, 0)
cam3 = Giper(4.01, 1.0, -5)

mount = Mount(np.deg2rad(4.32), np.deg2rad(4.18), np.deg2rad(4.15))

# рыск    крен    тангаж
# 4.32	4.15	4.18

kml = simplekml.Kml()

TIME_DELTA = 150  # Время трассировки подспутниковой точки до и после точки съёмки
TIME_DELTA_GIPER = (
    30  # Время трассировки обзора гиперспектрометра до и после точки съёмки
)

time_shot = datetime(2026, 7, 29, 12, 32, 50)
time_shot_start = time_shot - timedelta(seconds=TIME_DELTA)
time_shot_end = time_shot + timedelta(seconds=TIME_DELTA)

station = parse_telemetry_batch(
    Path("2_Orbita_UTC_giper.txt"),
    time_shot_start,
    time_shot_end,
)

# Подспутниковая точка
point1 = calculate_sub_satellite_points(station)
create_kml_track(kml, point1, "#FFFFFF", "Подспутниковая точка")

time_shot_start = time_shot - timedelta(seconds=TIME_DELTA_GIPER)
time_shot_end = time_shot + timedelta(seconds=TIME_DELTA_GIPER)

station = parse_telemetry_batch(
    Path("2_Orbita_UTC_giper.txt"),
    time_shot_start,
    time_shot_end,
)

# Первая камера
point3, point4 = calculate_view_cam_points(cam1, mount, station)
cam1_rect = [
    i for i in np.array(point3.tolist() + [i for i in reversed(point4.tolist())])
]

create_kml_circle(kml, cam1_rect, "#00FF00", "Камера 1")

# Вторая камера
point3, point4 = calculate_view_cam_points(cam2, mount, station)
cam1_rect = [
    i for i in np.array(point3.tolist() + [i for i in reversed(point4.tolist())])
]

create_kml_circle(kml, cam1_rect, "#FFFF00", "Камера 2")

# Третья камера
point3, point4 = calculate_view_cam_points(cam3, mount, station)
cam1_rect = [
    i for i in np.array(point3.tolist() + [i for i in reversed(point4.tolist())])
]

create_kml_circle(kml, cam1_rect, "#FF0000", "Камера 3")


kml.save("camera_view.kml")
print("KML-файл успешно сохранён: camera_view.kml")
