from dataclasses import dataclass
from mks.utils import rotation_matrix
import numpy as np


@dataclass(frozen=True, slots=True)
class Mount:
    """Класс кронштейна, на который монтируется камера, находится в системе координат связанной со станцией (ССК),
    но Y инвертирован, то есть смотрит на землю.
    Определяет углы, на которые повёрнута камера"""

    roll: float
    pitch: float
    yaw: float

    def get_camera_rotation_matrix(self) -> np.ndarray:
        """возвращает матрицу для перевода векторов из системы координат камеры в систему координат кронштейна"""
        return rotation_matrix(self.yaw, self.pitch, self.roll)
