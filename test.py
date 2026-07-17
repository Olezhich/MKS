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


cam = Camera(23.9, 35.9, 600)

mount = Mount(np.deg2rad(0), np.deg2rad(0), np.deg2rad(0))

# parsed = parse_telemetry_file("out_orbitka.txt")
# parsed = parse_telemetry_file("orbitca_photo_2.txt")

# N = 100000

# mks_pos = np.array(
#     [[point.x_greenwich, point.y_greenwich, point.z_greenwich] for point in parsed[:N]]
# )

# mks_vel = np.array(
#     [
#         [point.vx_greenwich, point.vy_greenwich, point.vz_greenwich]
#         for point in parsed[:N]
#     ]
# )

# mks_ang = (
#     np.deg2rad(parsed[0].roll),
#     np.deg2rad(parsed[0].pitch),
#     np.deg2rad(parsed[0].yaw),
# )

# station = Station(*mks_ang, mks_pos, mks_vel)

station = Station(
    *parse_telemetry(
        Path("out_orbitka.txt"), datetime(2026, 6, 28), datetime(2026, 7, 1)
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
