from mks.utils import rotation_matrix
import numpy as np


class Mount:
    """Класс кронштейна, на который монтируется камера, находится в системе координат связанной со станцией (ССК).
    Определяет углы, на которые повёрнута камера

    Все углы задаются в градусах"""

    def __init__(
        self,
        roll: float,
        pitch: float,
        yaw: float,
        corr_roll: float = 0,
        corr_pitch: float = 0,
        corr_yaw: float = 0,
    ):
        self.roll = np.deg2rad(roll)
        self.pitch = np.deg2rad(pitch)
        self.yaw = np.deg2rad(yaw)

        self.corr_roll = np.deg2rad(corr_roll)
        self.corr_pitch = np.deg2rad(corr_pitch)
        self.corr_yaw = np.deg2rad(corr_yaw)

    def get_camera_rotation_matrix(self) -> np.ndarray:
        """возвращает матрицу для перевода векторов из системы координат камеры в систему координат кронштейна"""
        return rotation_matrix(self.yaw, self.pitch, self.roll) @ rotation_matrix(
            self.corr_yaw, self.corr_pitch, self.corr_roll
        )
