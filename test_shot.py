from pathlib import Path

from mks.core import generate_shot
from mks.models import Camera, Mount, Giper, BaseCam


from datetime import datetime, timedelta


camera: list[BaseCam] = [Camera(35.9, 23.9, 600)]

giper: list[BaseCam] = [Giper(3.61, 1.0, 5), Giper(16, 9, 0), Giper(4.01, 1.0, -5)]

mount = Mount(24.25, 1.95, 4.22)

GIPER_FLAG = False  # Гиперспектрометр если True, иначе фотоаппарат

FOV_WO_ANG = True  # Флаг, если True углы обзора рисуются без учета углов станции - по подспутниковой точке

TIME_DELTA = 90  # Время трассировки подспутниковой точки до и после точки съёмки

TIME_DELTA_GIPER = (
    30  # Время трассировки обзора гиперспектрометра до и после точки съёмки
)

cam = giper if GIPER_FLAG else camera

# рыск    крен    тангаж
# 4.22  24.25   1.95

time_shot = datetime(2026, 6, 29, 14, 31, 42)

generate_shot(
    Path("2_Orbita_UTC.txt"),
    cam,
    mount,
    time_shot,
    timedelta(seconds=TIME_DELTA),
    timedelta(seconds=TIME_DELTA_GIPER),
)
