from mks.models import Camera, Mount, Station, StationCurrentCoords
from mks.core import calculate_cam_points
import numpy as np

st_r = np.deg2rad(-0.893)
st_p = np.deg2rad(7.001)
st_y = np.deg2rad(-176.110)

print(st_r, st_p, st_y)

cam = Camera(23.9, 35.9, 600)

mount = Mount(0, 0, 0)

station = Station(st_r, st_p, st_y)

station_current = StationCurrentCoords(
    np.array([1438.722, -6640.836, 116.776]), np.array([4.185434, 0.797209, -6.007792])
)

print(cam)

calculate_cam_points(cam, mount, station, station_current)
