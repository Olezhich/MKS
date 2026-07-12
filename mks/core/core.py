from mks.models import Mount, Camera, Station
from typing import Any
import numpy as np

RE_WGS84 = 6378.137             # Экваториальный радиус (км)
FLATTENING = 1 / 298.257223563  # Сжатие Земли

A_EARTH = RE_WGS84
B_EARTH = RE_WGS84 * (1.0 - FLATTENING)

def batch_earth_intersect(station: Station, cam_in_gcs: np.ndarray) ->np.ndarray:
    """Вычисляет точки пересечения вектора камеры с землей в ГСК для каждого момента времени"""
    norm_cam = cam_in_gcs / np.linalg.norm(cam_in_gcs, axis=1, keepdims=True) # Нормализуем вектора камеры

    # Извлекаем компоненты вектора камеры в каждый момент времени
    d_x = norm_cam[:,0]
    d_y = norm_cam[:,1]
    d_z = norm_cam[:,2]

    # Извлекаем компоненты вектора позиции МКС в кажыдй момент времени
    mks_x = station.position[:,0]
    mks_y = station.position[:,1]
    mks_z = station.position[:,2]

    # Считаем параметры уравнения пересечения луча (вектора камеры) и эллипсоида
    A = (d_x**2 + d_y**2) / A_EARTH**2 + d_z**2 / B_EARTH**2
    B = 2.0 * (mks_x * d_x / A_EARTH**2 + mks_y * d_y / A_EARTH**2 + mks_z * d_z / B_EARTH**2)
    C = (mks_x**2 + mks_y**2) / A_EARTH**2 + mks_z**2 / B_EARTH**2 - 1.0

    # Вычисляем дискриминант для каждого момента времени
    disc = B**2 - 4*A*C
    valid_mask = disc >= 0

    # Инициализируем массивы для решений уравнения пересечения
    N = len(disc)
    t1 = np.full(N, np.nan)
    t2 = np.full(N, np.nan) 

    # Вычисляем решения уравнения, только в тех точках, где неотрицателен дискриминант
    if np.any(valid_mask):
        d_valid = disc[valid_mask]
        a_valid = A[valid_mask]
        b_valid = B[valid_mask]

        t1[valid_mask] = (-b_valid - np.sqrt(d_valid)) / (2 * a_valid)
        t2[valid_mask] = (-b_valid + np.sqrt(d_valid)) / (2 * a_valid)

    t = np.full(N, np.nan)

    # Ищем наименьший положительный корень (ближняя стенка эллипсоида)
    # Считаем априорно, что t1 < t2, при условии, что они оба положительны
    t1_positive = (t1 > 0) & valid_mask
    t2_positive = (t2 > 0) & valid_mask & ~t1_positive
    t[t1_positive] = t1[t1_positive]
    t[t2_positive] = t2[t2_positive]

    final_valid = ~np.isnan(t)
    t_valid = t[final_valid]

    result = np.full((N, 3), np.nan)
    result[final_valid,0] = mks_x[final_valid] + t_valid * d_x[final_valid]
    result[final_valid,1] = mks_y[final_valid] + t_valid * d_y[final_valid]
    result[final_valid,2] = mks_z[final_valid] + t_valid * d_z[final_valid]

    return result


"""
    re - экваториальный радиус земли (км)
    a - геометрическое сжатие земли
    Возвращает: долгота, широта в градусах и высоту от поверхности
"""


def convert_to_geo_cords(cam_dot_in_gcs_batch: np.ndarray) -> np.ndarray:
    res = []

    for cam_dot_in_gcs in cam_dot_in_gcs_batch:
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

        res.append([np.degrees(longitude), np.degrees(latitude), h])
    return np.array(res)


def calculate_cam_points(cam: Camera, mount: Mount, station: Station) -> Any:

    # нужно перевести вектора камеры из системы координат камеры в ССК
    # Пирменяем вращения в кронштейне
    cam_in_mount = mount.get_camera_rotation_matrix() @ cam.get_center_vector()

    # Переводим из системы координат кронштейна в ССК
    cam_in_SCS = cam_in_mount * np.array([1, -1, 1])

    # Переводим в ОСК
    cam_in_OCS = station.get_mount_rotation_matrix() @ cam_in_SCS

    # ----здесь заканчивается обработка значений для одной лишь камеры
    # и начинается обработка множественных значений, зависящих от координат станции

    # Переводим в ГСК
    cam_in_GCS = np.einsum("nij,j->ni", station.get_gcs_basis_matrix(), cam_in_OCS)

    # Ищем точку пересечения вектора камеры и сферы земли в ГСК
    cam_dot_GCS = batch_earth_intersect(station, cam_in_GCS)

    # Считаем широту и долготу
    cam_dot_in_GEO = convert_to_geo_cords(cam_dot_GCS)
    print(cam_dot_in_GEO)
