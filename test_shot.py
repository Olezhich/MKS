from pathlib import Path

from mks.core import (
    calculate_sub_satellite_points,
    calculate_center_cam_point,
    calculate_rect_view_cam_points,
    parse_telemetry,
    calculate_circle_view_cam_points,
    create_kml_circle,
)
from mks.models import Camera, Mount, Station

import numpy as np
import simplekml  # type: ignore

from datetime import datetime


cam = Camera(35.9, 23.9, 600)

mount = Mount(-np.deg2rad(24.25), np.deg2rad(1.95), np.deg2rad(4.22))

# рыск    крен    тангаж
# 4.22  24.25   1.95

station = Station(
    *parse_telemetry(
        Path("2_Orbita_UTC_0_1.txt"),
        datetime(2026, 6, 29, 14, 31, 12),
        datetime(2026, 6, 29, 14, 32, 12),
    )
)

# Подспутниковая точка
point1 = calculate_sub_satellite_points(station)

# Задаём новую станцию одной точкой
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

# прямоугольник обзора
rect = calculate_rect_view_cam_points(cam, mount, station)

# Окужности обзоров
circle30 = calculate_circle_view_cam_points(station, 30)
circle60 = calculate_circle_view_cam_points(station, 60)
circle90 = calculate_circle_view_cam_points(station, 90)


kml = simplekml.Kml()

# ============================================================
# 1. Трек подспутниковой точки (LineString)
# ============================================================
# simplekml ожидает координаты в формате (lon, lat[, alt])
# Если point1 хранится как (lat, lon), нужно поменять местами

coords_track = []
for pt in point1:
    lon, lat = pt[0], pt[1]
    coords_track.append((lon, lat))

linestring = kml.newlinestring(
    name="Подспутниковый трек",
    description="Трек подспутниковой точки",
    coords=coords_track,
)
linestring.style.linestyle.color = simplekml.Color.white
linestring.style.linestyle.width = 3

# ============================================================
# 2. Центр камеры (Point)
# ============================================================
lat2, lon2 = point2[0][1], point2[0][0]

point = kml.newpoint(
    name="Центр камеры",
    description="Центральная точка обзора камеры",
    coords=[(lon2, lat2)],
)
point.style.iconstyle.color = simplekml.Color.blue
point.style.iconstyle.scale = 1.5

# ============================================================
# 3. Прямоугольник обзора (Polygon)
# ============================================================
# Собираем координаты прямоугольника (должно быть 4 точки)
# Для замкнутого полигона simplekml автоматически замыкает контур,
# но можно явно указать первую точку в конце
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


# circles
create_kml_circle(kml, circle30, "#00FF00", "fov30")
create_kml_circle(kml, circle60, "#FFFF00", "fov60")
create_kml_circle(kml, circle90, "#FF0000", "fov90")

# ============================================================
# Сохранение KML
# ============================================================
kml.save("camera_view.kml")
print("KML-файл успешно сохранён: camera_view.kml")
