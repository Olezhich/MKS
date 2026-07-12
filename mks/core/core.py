from mks.models import Mount, Camera, Station, StationCurrentCoords
from typing import Any
import numpy as np


def earth_intersect(
    station_current: StationCurrentCoords, cam_in_gcs: np.ndarray
) -> np.ndarray:
    """Вычисляет точку пересечения вектора камеры с землей в ГСК"""

    cam_in_gcs = cam_in_gcs / np.linalg.norm(
        cam_in_gcs
    )  # Нужно сделать условие, что мы работаем только с нормализованными векторами

    # R_x = MKS_x + t * d_x уравнение луча

    d_x, d_y, d_z = cam_in_gcs
    mks_x, mks_y, mks_z = station_current.position

    a_semi = 6378.137
    b_semi = 6378.137 * (1.0 - 1 / 298.257223563)

    A = (d_x**2 + d_y**2) / a_semi**2 + d_z**2 / b_semi**2
    B = 2.0 * (
        mks_x * d_x / a_semi**2 + mks_y * d_y / a_semi**2 + mks_z * d_z / b_semi**2
    )
    C = (mks_x**2 + mks_y**2) / a_semi**2 + mks_z**2 / b_semi**2 - 1.0

    disc = B**2 - 4 * A * C
    if disc < 0:
        raise ValueError

    sqrt_disc = np.sqrt(disc)
    t1 = (-B - sqrt_disc) / (2 * A)
    t2 = (-B + sqrt_disc) / (2 * A)

    # Ищем наименьший положительный корень (ближняя стенка эллипсоида)
    t = t1 if t1 > 0 else (t2 if t2 > 0 else None)
    if t is None:
        raise ValueError

    return np.array([mks_x + t * d_x, mks_y + t * d_y, mks_z + t * d_z])


"""
    re - экваториальный радиус земли (км)
    a - геометрическое сжатие земли
    Возвращает: долгота, широта в градусах и высоту от поверхности
"""


def convert_to_geo_cords(cam_dot_in_gcs: np.ndarray) -> np.ndarray:
    a = 6378.137
    b = 6378.137 * (1.0 - 1 / 298.257223563)
    e2 = (a**2 - b**2) / a**2
    ep2 = (a**2 - b**2) / b**2

    x, y, z = cam_dot_in_gcs

    p = np.sqrt(x**2 + y**2)

    # Вспомогательный угол
    theta = np.arctan2(z * a, p * b)

    longitude = np.arctan2(y, x)

    latitude = np.arctan2(
        z + ep2 * b * np.sin(theta) ** 3, p - e2 * a * np.cos(theta) ** 3
    )

    # Высота
    n = a / np.sqrt(1.0 - e2 * np.sin(latitude) ** 2)
    h = (p / np.cos(latitude)) - n

    return np.array([np.degrees(longitude), np.degrees(latitude), h])


def calculate_cam_points(
    cam: Camera, mount: Mount, station: Station, station_current: StationCurrentCoords
) -> Any:

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

    # Переводим в ГСК
    cam_in_GCS = station_current.get_basis_matrix() @ cam_in_OCS

    print(cam_in_GCS)

    # Ищем точку пересечения вектора камеры и сферы земли в ГСК
    cam_dot_GCS = earth_intersect(station_current, cam_in_GCS)

    print(cam_dot_GCS)

    # Считаем широту и долготу
    cam_dot_in_GEO = convert_to_geo_cords(cam_dot_GCS)
    print(cam_dot_in_GEO)
