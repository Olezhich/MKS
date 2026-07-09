from mks.models import Camera, Mount
from mks.core import calculate_cam_points

cam = Camera(23.9, 35.9, 600)

mount = Mount(0, 0, 0)

print(cam)

calculate_cam_points(cam, mount)
