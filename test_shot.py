from pathlib import Path

from mks.core import (
    calculate_sub_satellite_points,
    calculate_center_cam_point,
    calculate_rect_view_cam_points,
    parse_telemetry_batch,
    calculate_circle_view_cam_points,
    create_kml_circle,
    create_kml_track,
)
from mks.models import Camera, Mount, Station

import numpy as np
import simplekml  # type: ignore

from datetime import datetime, timedelta


cam = Camera(35.9, 23.9, 600)

mount = Mount(np.deg2rad(24.25), np.deg2rad(1.95), np.deg2rad(4.22))

kml = simplekml.Kml()

FOV_WO_ANG = True  # Флаг, если True углы обзора рисуются без учета углов станции - по подспутниковой точке

TIME_DELTA = 90  # Время трассировки подспутниковой точки до и после точки съёмки

# рыск    крен    тангаж
# 4.22  24.25   1.95

time_shot = datetime(2026, 6, 29, 14, 31, 42)
time_shot_start = time_shot - timedelta(seconds=TIME_DELTA)
time_shot_end = time_shot + timedelta(seconds=TIME_DELTA)

station = parse_telemetry_batch(
    Path("2_Orbita_UTC_21_07_1251.txt"),
    time_shot_start,
    time_shot_end,
)

# Подспутниковая точка
point1 = calculate_sub_satellite_points(station)
create_kml_track(kml, point1, "#FFFFFF", "Подспутниковая точка")

old = station
cnt = len(station.position) // 2

station = Station(
    old.roll,
    old.pitch,
    old.yaw,
    old.position[cnt : cnt + 1],
    old.velocity[cnt : cnt + 1],
)

# Центр камеры
point2 = calculate_center_cam_point(cam, mount, station)

lat2, lon2 = point2[0][1], point2[0][0]

point = kml.newpoint(
    name="Центр камеры",
    description="Центральная точка обзора камеры",
    coords=[(lon2, lat2)],
)
point.style.iconstyle.color = simplekml.Color.blue
point.style.iconstyle.scale = 1.5

# прямоугольник обзора
rect = calculate_rect_view_cam_points(cam, mount, station)

outer_coords = []
for pt in rect:
    lat_r, lon_r = pt[0][1], pt[0][0]
    outer_coords.append((lon_r, lat_r))

# Замыкаем контур (первая точка = последняя)
if outer_coords[0] != outer_coords[-1]:
    outer_coords.append(outer_coords[0])

polygon = kml.newpolygon(
    name="Прямоугольник обзора",
    description="Область обзора камеры",
    outerboundaryis=outer_coords,
)
polygon.style.linestyle.color = simplekml.Color.green
polygon.style.linestyle.width = 2
polygon.style.polystyle.color = simplekml.Color.changealpha("55", simplekml.Color.green)

# Окужности обзоров
if FOV_WO_ANG:
    old = station

    station = Station(
        0,
        0,
        0,
        old.position,
        old.velocity,
    )

circle30 = calculate_circle_view_cam_points(station, 30)
circle60 = calculate_circle_view_cam_points(station, 60)
circle90 = calculate_circle_view_cam_points(station, 90)

create_kml_circle(kml, circle30, "#00FF00", "fov30")
create_kml_circle(kml, circle60, "#FFFF00", "fov60")
create_kml_circle(kml, circle90, "#FF0000", "fov90")

kml.save("camera_view.kml")
print("KML-файл успешно сохранён: camera_view.kml")
