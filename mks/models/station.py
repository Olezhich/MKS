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


@dataclass(frozen=True, slots=True)
class StationCurrentCoords:
    """ "Класс координат МКС в ГСК"""

    position: np.ndarray
    velocity: np.ndarray

    def get_basis_matrix(self) -> np.ndarray:
        """Строим базис ОСК в координатах ГСК"""

        # Y ось от центра земли к мкс
        y = self.position / np.linalg.norm(self.position)

        # Z ось перпендикулярная Y и вектору скорости станции (нужно для корректного вычисления X)
        z = np.cross(self.position, self.velocity)
        z = z / np.linalg.norm(z)

        # X перпендикулярна Y и Z
        x = np.cross(z, y)

        return np.column_stack((x, y, z))
