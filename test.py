from pathlib import Path

from mks.models import Camera, Mount, Giper
from mks.core import (
    calculate_view_cam_points,
    calculate_center_cam_point,
    calculate_sub_satellite_points,
    parse_telemetry,
    create_kml_track,
)
import numpy as np

from datetime import datetime

import simplekml  # type: ignore

GIPER_FLAG = False  # Гиперспектрометр если True, иначе фотоаппарат


camera = Camera(35.9, 23.9, 600)
giper = Giper(3.61, 1.0, 5)

cam = giper if GIPER_FLAG else camera

mount = Mount(np.deg2rad(0), np.deg2rad(0), np.deg2rad(0))

kml = simplekml.Kml()

for station, circle in parse_telemetry(
    Path("2_Orbita_UTC_21_07_1251.txt"), datetime(2026, 6, 28), datetime(2026, 7, 1)
):
    # Подспутниковая точка
    point1 = calculate_sub_satellite_points(station)

    # Центр камеры
    point2 = calculate_center_cam_point(cam, mount, station)

    # Левый и правый края обзора
    point3, point4 = calculate_view_cam_points(cam, mount, station)

    current_folder = kml.newfolder(name=f"Виток_{circle}")
    create_kml_track(current_folder, point1, "#FFFFFF", "Подспутниковая точка")
    create_kml_track(current_folder, point2, "#FF0000", "Центр обзора")
    create_kml_track(current_folder, point3, "#00FF00", "Граница обзора 1")
    create_kml_track(current_folder, point4, "#00FF00", "Граница обзора 2")

    print(f"Coords for {circle} calculated")

kml.save("output.kml")
print(f"KML файл успешно сохранен в {'output.kml'}")
