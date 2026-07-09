from dataclasses import dataclass
from mks.utils import rotation_matrix
import numpy as np


@dataclass(frozen=True, slots=True)
class Station:
    """Класс МКС"""

    roll: float
    pitch: float
    yaw: float

    def get_mount_rotation_matrix(self) -> np.ndarray:
        """возвращает матрицу для перевода векторов из системы координат ССК
        в систему координат ОСК"""
        return rotation_matrix(self.yaw, self.pitch, self.roll)
