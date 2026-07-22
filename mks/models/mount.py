from mks.utils import rotation_matrix
import numpy as np


class Mount:
    """Класс кронштейна, на который монтируется камера, находится в системе координат связанной со станцией (ССК).
    Определяет углы, на которые повёрнута камера

    Все углы задаются в градусах"""

    def __init__(self, roll: float, pitch: float, yaw: float):
        self.roll = np.deg2rad(roll)
        self.pitch = np.deg2rad(pitch)
        self.yaw = np.deg2rad(yaw)

    def get_camera_rotation_matrix(self) -> np.ndarray:
        """возвращает матрицу для перевода векторов из системы координат камеры в систему координат кронштейна"""
        return rotation_matrix(self.yaw, self.pitch, self.roll)
