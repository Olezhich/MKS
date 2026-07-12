from mks.models import Station, Camera, Mount
from mks.core import parse_telemetry_file, calculate_cam_points
import numpy as np

# st_r = np.deg2rad(0)
# st_p = np.deg2rad(0)
# st_y = np.deg2rad(-180)

# print(st_r, st_p, st_y)

cam = Camera(23.9, 35.9, 600)

mount = Mount(0, 0, 0)

# station = Station(st_r, st_p, st_y)


# station_current = StationCurrentCoords(
#     np.array([-6469.137, 2090.010, 30.036]), np.array([-1.279913, -4.059670, 6.007082])
# )

# print(cam)

# calculate_cam_points(cam, mount, station, station_current)

parsed = parse_telemetry_file("out_orbitka.txt")

# print(parsed[1])

N = 10000

mks_pos = np.array(
    [[point.x_greenwich, point.y_greenwich, point.z_greenwich] for point in parsed[:]]
)

mks_vel = np.array(
    [
        [point.vx_greenwich, point.vy_greenwich, point.vz_greenwich]
        for point in parsed[:]
    ]
)

mks_ang = (parsed[0].roll, parsed[0].pitch, parsed[0].yaw)

mks_ang = (np.deg2rad(0), np.deg2rad(0), np.deg2rad(-180))

station = Station(*mks_ang, mks_pos, mks_vel)

# print(station)

print("calculate Coords")

calculate_cam_points(cam, mount, station)
