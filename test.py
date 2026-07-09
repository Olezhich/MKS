from mks.models import Camera, Mount, Station
from mks.core import calculate_cam_points
import numpy as np

st_r = np.deg2rad(-0.893)
st_p = np.deg2rad(7.001)
st_y = np.deg2rad(-176.110)

print(st_r, st_p, st_y)

cam = Camera(23.9, 35.9, 600)

mount = Mount(0, 0, 0)

station = Station(st_r, st_p, st_y)

# station = Station(-0.893, 7.001, -176.110)

print(cam)

calculate_cam_points(cam, mount, station)
