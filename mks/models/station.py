from dataclasses import dataclass
from mks.utils import rotation_matrix
import numpy as np


@dataclass(frozen=True, slots=True)
class Station:
    """Класс МКС"""

    roll: float
    pitch: float
    yaw: float

    position: np.ndarray  # batch of MKS positions
    velocity: np.ndarray  # batch of MKS velocities

    def get_mount_rotation_matrix(self) -> np.ndarray:
        """возвращает матрицу для перевода векторов из системы координат ССК
        в систему координат ОСК"""
        return rotation_matrix(self.yaw, self.pitch, self.roll)

    def get_gcs_basis_matrix(self) -> np.ndarray:
        """Строим базис ОСК в координатах ГСК"""

        # Для ускорения работы работаем со всеми значениями как с матрицами,
        # чтобы все вычисления происходили внутри NumPy

        # Y ось от центра земли к мкс
        y = self.position / np.linalg.norm(self.position, axis=1, keepdims=True)

        # Z ось перпендикулярная Y и вектору скорости станции (нужно для корректного вычисления X)
        z = np.cross(self.position, self.velocity)
        z = z / np.linalg.norm(z, axis=1, keepdims=True)

        # X перпендикулярна Y и Z
        x = np.cross(z, y)

        M_batch = np.stack((x, y, z), axis=-1)  # создаём массив матриц перехода

        return M_batch
