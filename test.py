from pathlib import Path

from mks.models import Camera, Mount, Giper
from mks.core import generate_tracks
import numpy as np

from datetime import datetime

GIPER_FLAG = True  # Гиперспектрометр если True, иначе фотоаппарат


camera = Camera(35.9, 23.9, 600)
giper = Giper(3.61, 1.0, 5)

cam = giper if GIPER_FLAG else camera

mount = Mount(np.deg2rad(0), np.deg2rad(0), np.deg2rad(0))

t_start = datetime(2026, 6, 29, 10, 45)
t_end = datetime(2026, 6, 30, 12, 55)

orbita_path = Path("out_orbitka.txt")

generate_tracks(orbita_path, cam, mount, t_start, t_end)
