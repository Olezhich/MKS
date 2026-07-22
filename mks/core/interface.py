from pathlib import Path

import numpy as np
import simplekml  # type: ignore

from mks.models import BaseCam, Mount, Giper, Station, Camera
from mks.core.parser import parse_telemetry, parse_telemetry_batch
from mks.core.core import (
    calculate_circle_view_cam_points,
    calculate_rect_view_cam_points,
    calculate_sub_satellite_points,
    calculate_center_cam_point,
    calculate_view_cam_points,
)
from mks.core.kml import create_kml_circle, create_kml_track

from datetime import datetime, timedelta


def generate_tracks(
    orbita_utc: Path,
    camera: BaseCam,
    mount: Mount,
    t_start: datetime,
    t_end: datetime,
    kml_path: Path = Path("output.kml"),
) -> None:
    """Генерирует kml для пролетов станции

    Перед запуском этой функции должен быть сгенерирован файл 2_Orbita_UTC.txt в нужном временном интервале

    Аргументы:
    - orbita_utc: путь к файлу 2_Orbita_UTC.txt
    - camera: объект камеры (Camera или Giper передаём один из классов, наследованный от BaseCam), импртируется из mks.models
    - mount: объект крепления, импртируется из mks.models
    - t_start: время начала пролетов
    - t_end: время окончания пролетов
    - kml_path: путь к создаваемому kml файлу"""

    kml = simplekml.Kml()

    for station, circle in parse_telemetry(orbita_utc, t_start, t_end):
        current_folder = kml.newfolder(name=f"Виток_{circle}")

        # Подспутниковая точка
        point1 = calculate_sub_satellite_points(station)
        create_kml_track(current_folder, point1, "#FFFFFF", "Подспутниковая точка")

        # Центр камеры
        point2 = calculate_center_cam_point(camera, mount, station)
        create_kml_track(current_folder, point2, "#FF0000", "Центр обзора")

        # Левый и правый края обзора
        point3, point4 = calculate_view_cam_points(camera, mount, station)
        create_kml_track(current_folder, point3, "#00FF00", "Граница обзора 1")
        create_kml_track(current_folder, point4, "#00FF00", "Граница обзора 2")

        print(f"Coords for {circle} calculated")

    kml.save(kml_path)
    print(f"KML файл успешно сохранен в {kml_path}")


def generate_shot(
    orbita_utc: Path,
    cameras: list[BaseCam],
    mount: Mount,
    t_shot: datetime,
    ssp_delta: timedelta,
    giper_delta,
    kml_path: Path = Path("camera_view.kml"),
    fov_wo_ang: bool = True,
) -> None:
    """Генерирует kml для снимков камеры

    Перед запуском этой функции должен быть сгенерирован файл 2_Orbita_UTC.txt в нужном временном интервале

    Аргументы:
    - orbita_utc: путь к файлу 2_Orbita_UTC.txt
    - camera: список объектов камер ([Camera] - для камеры или [Giper, Giper, Giper] - для 3 камер гиперспектрометра (если нужна только одна камера гиперспектрометра то передаётся [Giper]) передаём список объектов нужного класса, наследованных от BaseCam), импртируется из mks.models
    - mount: объект крепления, импртируется из mks.models
    - t_shot: время съемки
    - ssp_delta: время трассировки подспутниковой точки до и после точки съёмки
    - giper_delta: время трассировки обзора гиперспектрометра до и после точки съёмки
    - kml_path: путь к создаваемому kml файлу
    - fov_wo_ang: флаг, если True углы обзора рисуются без учета углов станции - по подспутниковой точке"""

    station = parse_telemetry_batch(
        orbita_utc,
        t_shot - ssp_delta,
        t_shot + ssp_delta,
    )

    kml = simplekml.Kml()

    # Подспутниковая точка
    point1 = calculate_sub_satellite_points(station)
    create_kml_track(kml, point1, "#FFFFFF", "Подспутниковая точка")

    if len(cameras) > 0 and all(isinstance(cam, Giper) for cam in cameras):
        # Для гиперспектрометра

        station = parse_telemetry_batch(
            orbita_utc,
            t_shot - giper_delta,
            t_shot + giper_delta,
        )

        colors = ["#00FF00", "#FFFF00", "#FF0000"]

        for i, cam in enumerate(cameras):
            point3, point4 = calculate_view_cam_points(cam, mount, station)
            cam1_rect = [
                i
                for i in np.array(
                    point3.tolist() + [i for i in reversed(point4.tolist())]
                )
            ]

            create_kml_circle(kml, cam1_rect, colors[i], f"Камера_{i + 1}")

    elif len(cameras) == 1 and isinstance(cameras[0], Camera):
        # для фотоаппарата
        old = station
        cnt = len(station.position) // 2

        cam = cameras[0]

        station = Station(
            old.roll,
            old.pitch,
            old.yaw,
            old.position[cnt : cnt + 1],
            old.velocity[cnt : cnt + 1],
        )
        # Центр камеры
        point2 = calculate_center_cam_point(cam, mount, station)

        cam_center = kml.newpoint(
            name="Центр камеры",
            coords=[(point2[0][0], point2[0][1])],
        )
        cam_center.style.iconstyle.color = simplekml.Color.blue
        cam_center.style.iconstyle.scale = 3

        # прямоугольник обзора
        rect = calculate_rect_view_cam_points(cam, mount, station)
        create_kml_circle(kml, rect, "#00FF00", "Прямоугольник обзора")

        # Окужности обзоров
        if fov_wo_ang:
            old = station
            station = Station(
                0,
                0,
                0,
                old.position,
                old.velocity,
            )

        circle30 = calculate_circle_view_cam_points(station, 30)
        circle60 = calculate_circle_view_cam_points(station, 60)
        circle90 = calculate_circle_view_cam_points(station, 90)

        create_kml_circle(kml, circle30, "#00FF00", "fov30")
        create_kml_circle(kml, circle60, "#FFFF00", "fov60")
        create_kml_circle(kml, circle90, "#FF0000", "fov90")

    else:
        raise ValueError("Передан неверный аргумент: cameras")

    kml.save(kml_path)
    print(f"KML-файл успешно сохранён: {kml_path}")
