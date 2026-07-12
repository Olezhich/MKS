from mks.models import Camera, Mount, Station, StationCurrentCoords
from mks.core import calculate_cam_points
import numpy as np

st_r = np.deg2rad(0)
st_p = np.deg2rad(0)
st_y = np.deg2rad(-180)

print(st_r, st_p, st_y)

cam = Camera(23.9, 35.9, 600)

mount = Mount(0, 0, 0)

station = Station(st_r, st_p, st_y)


station_current = StationCurrentCoords(
    np.array([-6469.137, 2090.010, 30.036]), np.array([-1.279913, -4.059670, 6.007082])
)

print(cam)

calculate_cam_points(cam, mount, station, station_current)
