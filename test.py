from mks.models import Station, Camera, Mount
from mks.core import (
    parse_telemetry_file,
    calculate_view_cam_points,
    calculate_center_cam_point,
    create_kml_from_tracks,
)
import numpy as np


cam = Camera(23.9, 35.9, 600)

mount = Mount(0, 0, 0)

parsed = parse_telemetry_file("out_orbitka.txt")

N = 2000

mks_pos = np.array(
    [[point.x_greenwich, point.y_greenwich, point.z_greenwich] for point in parsed[:N]]
)

mks_vel = np.array(
    [
        [point.vx_greenwich, point.vy_greenwich, point.vz_greenwich]
        for point in parsed[:N]
    ]
)

# mks_ang = (parsed[0].roll, parsed[0].pitch, parsed[0].yaw)

mks_ang = (np.deg2rad(0), np.deg2rad(0), np.deg2rad(-180))

station = Station(*mks_ang, mks_pos, mks_vel)

print("Calculate Coords")

# Подспутниковая точка
point1 = calculate_center_cam_point(cam, mount, station)

print("POINT1\n", point1)

# Центр камеры
mks_ang = (parsed[0].roll, parsed[0].pitch, parsed[0].yaw)
station = Station(*mks_ang, mks_pos, mks_vel)

point2 = calculate_center_cam_point(cam, mount, station)

print("POINT2\n", point2)

# Левый и правый края обзора

point3, point4 = calculate_view_cam_points(cam, mount, station)

print("POINT3\n", point3)
print("POINT4\n", point4)

# Делаем kml файл

create_kml_from_tracks(
    tracks=[
        point2,
        np.array([[point.latitude, point.longitude] for point in parsed[:N]]),
    ],  # , point2, point3, point4],
    colors=["#FFFFFF", "#FF00FF"],  # , "#FF0000", "#00FF00", "#00FF00"],
)
