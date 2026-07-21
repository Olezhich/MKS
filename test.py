from pathlib import Path

from mks.models import Station, Camera, Mount
from mks.core import (
    calculate_view_cam_points,
    calculate_center_cam_point,
    create_kml_from_tracks,
    calculate_sub_satellite_points,
    parse_telemetry,
)
import numpy as np

from datetime import datetime


cam = Camera(35.9, 23.9, 600)

mount = Mount(np.deg2rad(0), np.deg2rad(0), np.deg2rad(0))

station = Station(
    *parse_telemetry(
        Path("2_Orbita_UTC_21_07_1251.txt"), datetime(2026, 6, 28), datetime(2026, 7, 1)
    )
)

print("Calculate Coords")

# Подспутниковая точка
point1 = calculate_sub_satellite_points(station)

print("POINT1\n", point1)

# Центр камеры

print(station)

point2 = calculate_center_cam_point(cam, mount, station)

print("POINT2\n", point2)

# Левый и правый края обзора

point3, point4 = calculate_view_cam_points(cam, mount, station)

print("POINT3\n", point3)
print("POINT4\n", point4)

# Делаем kml файл

create_kml_from_tracks(
    tracks=[point1, point2, point3, point4],
    colors=["#FFFFFF", "#FF0000", "#00FF00", "#00FF00"],
)
