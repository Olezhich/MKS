from mks.models import Mount, Camera, Station
from typing import Any
import numpy as np


def calculate_cam_points(cam: Camera, mount: Mount, station: Station) -> Any:

    # нужно перевести вектора камеры из системы координат камеры в ССК
    # Пирменяем вращения в кронштейне

    cam_in_mount = mount.get_camera_rotation_matrix() @ cam.get_center_vector()

    print(cam_in_mount)

    # Переводим из системы координат кронштейна в ССК
    cam_in_SCS = cam_in_mount * np.array([1, -1, 1])

    print(cam_in_SCS)

    # Переводим в ОСК
    cam_in_OCS = station.get_mount_rotation_matrix() @ cam_in_SCS

    print(cam_in_OCS)
