from mks.models import Mount, Camera, Station
import numpy as np

RE_WGS84 = 6378.137  # Экваториальный радиус (км)
FLATTENING = 1 / 298.257223563  # Сжатие Земли

A_EARTH = RE_WGS84
B_EARTH = RE_WGS84 * (1.0 - FLATTENING)


def batch_earth_intersect(station: Station, cam_in_gcs: np.ndarray) -> np.ndarray:
    """Вычисляет точки пересечения вектора камеры с землей в ГСК для каждого момента времени"""
    norm_cam = cam_in_gcs / np.linalg.norm(
        cam_in_gcs, axis=1, keepdims=True
    )  # Нормализуем вектора камеры

    # Извлекаем компоненты вектора камеры в каждый момент времени
    d_x = norm_cam[:, 0]
    d_y = norm_cam[:, 1]
    d_z = norm_cam[:, 2]

    # Извлекаем компоненты вектора позиции МКС в кажыдй момент времени
    mks_x = station.position[:, 0]
    mks_y = station.position[:, 1]
    mks_z = station.position[:, 2]

    # Считаем параметры уравнения пересечения луча (вектора камеры) и эллипсоида
    A = (d_x**2 + d_y**2) / A_EARTH**2 + d_z**2 / B_EARTH**2
    B = 2.0 * (
        mks_x * d_x / A_EARTH**2 + mks_y * d_y / A_EARTH**2 + mks_z * d_z / B_EARTH**2
    )
    C = (mks_x**2 + mks_y**2) / A_EARTH**2 + mks_z**2 / B_EARTH**2 - 1.0

    # Вычисляем дискриминант для каждого момента времени
    disc = B**2 - 4 * A * C
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
    result[final_valid, 0] = mks_x[final_valid] + t_valid * d_x[final_valid]
    result[final_valid, 1] = mks_y[final_valid] + t_valid * d_y[final_valid]
    result[final_valid, 2] = mks_z[final_valid] + t_valid * d_z[final_valid]

    return result


def batch_convert_to_geo_coords(cam_dot_in_gcs: np.ndarray) -> np.ndarray:
    """Вычисляет широту и долготу точек пересечения камеры и земли в ГСК"""

    e2 = (A_EARTH**2 - B_EARTH**2) / A_EARTH**2
    ep2 = (A_EARTH**2 - B_EARTH**2) / B_EARTH**2

    # Извлекаем компоненты точек
    x = cam_dot_in_gcs[:, 0]
    y = cam_dot_in_gcs[:, 1]
    z = cam_dot_in_gcs[:, 2]

    p = np.sqrt(x**2 + y**2)
    # Вспомогательный угол
    theta = np.arctan2(z * A_EARTH, p * B_EARTH)

    # Долгота
    longitude = np.arctan2(y, x)

    # Широта
    latitude = np.arctan2(
        z + ep2 * B_EARTH * np.sin(theta) ** 3, p - e2 * A_EARTH * np.cos(theta) ** 3
    )

    return np.column_stack((np.degrees(longitude), np.degrees(latitude)))


def calculate_sub_satellite_points(station: Station) -> np.ndarray:
    station_in_GCS = -station.position / np.linalg.norm(
        station.position, axis=1, keepdims=True
    )

    # Ищем точку пересечения вектора станции и сферы земли в ГСК
    station_dot_GCS = batch_earth_intersect(station, station_in_GCS)

    # Считаем широту и долготу
    station_dot_in_GEO = batch_convert_to_geo_coords(station_dot_GCS)

    return station_dot_in_GEO


def calculate_cam_points(
    cam_vec: np.ndarray, mount: Mount, station: Station
) -> np.ndarray:

    # нужно перевести вектора камеры из системы координат камеры в ССК
    # Пирменяем вращения в кронштейне
    cam_in_mount = mount.get_camera_rotation_matrix() @ cam_vec

    # Переводим из системы координат кронштейна в ССК
    cam_in_SCS = cam_in_mount  # * np.array([1, -1, 1])

    # Переводим в ОСК
    cam_in_OCS = station.get_mount_rotation_matrix() @ cam_in_SCS

    # ----здесь заканчивается обработка значений для одной лишь камеры
    # и начинается обработка множественных значений, зависящих от координат станции

    # Переводим в ГСК
    cam_in_GCS = station.get_gcs_basis_matrix() @ cam_in_OCS

    # Ищем точку пересечения вектора камеры и сферы земли в ГСК
    cam_dot_GCS = batch_earth_intersect(station, cam_in_GCS)

    # Считаем широту и долготу
    cam_dot_in_GEO = batch_convert_to_geo_coords(cam_dot_GCS)

    return cam_dot_in_GEO


def calculate_center_cam_point(
    cam: Camera, mount: Mount, station: Station
) -> np.ndarray:
    """Возвращает множество точкек центра камеры"""
    return calculate_cam_points(cam.get_center_vector(), mount, station)


def calculate_view_cam_points(
    cam: Camera, mount: Mount, station: Station
) -> tuple[np.ndarray, np.ndarray]:
    """Возвращает кортеж множеств точек левого и правого углов обзора камеры"""
    left, right = cam.get_h_view_vectors()
    return (
        calculate_cam_points(left, mount, station),
        calculate_cam_points(right, mount, station),
    )


def calculate_rect_view_cam_points(
    cam: Camera, mount: Mount, station: Station
) -> list[np.ndarray]:
    """Возвращает список точек лв, пв, лн, пн углов камеры"""
    # получаем вектора камеры
    lt, rt, lb, rb = cam.get_view_vectors()

    # Вычисляем их долготу и широту
    coords = [
        calculate_cam_points(lt, mount, station),
        calculate_cam_points(rt, mount, station),
        calculate_cam_points(rb, mount, station),
        calculate_cam_points(lb, mount, station),
    ]

    return coords


def calculate_circle_view_cam_points(
    station: Station, ang_deg: float
) -> list[np.ndarray]:
    """Возвращает список точек окружности обзора заданного угла"""
    vecs = Camera.get_circle_view_vectors(ang_deg)

    mount = Mount(0, 0, 0)

    res = []

    for vec in vecs:
        res.append(calculate_cam_points(vec, mount, station))

    return res
