import numpy as np
from abc import ABC, abstractmethod

from mks.utils import rotation_matrix


class BaseCam(ABC):
    """Базовый класс для камер. Должен предоставлять набор необходимых векторов для отрисовки.
    Система координат камеры: X - вверх, Y - вперед, Z - вправо"""

    def __init__(self, view_angle_horisontal: float, view_angle_vertical: float):
        self._view_angle_horisontal: float = view_angle_horisontal
        self._view_angle_vertical: float = view_angle_vertical

    @abstractmethod
    def get_view_vectors(self) -> list[np.ndarray]:
        pass

    def get_h_view_vectors(self) -> list[np.ndarray]:
        delta_h = np.tan(self._view_angle_horisontal / 2)
        return [
            np.array([0, -1, delta_h]),
            np.array([0, -1, -delta_h]),
        ]

    def get_center_vector(self) -> np.ndarray:
        return np.array([0, -1, 0])

    def __repr__(self) -> str:
        return f"<BaseCam va_h={self._view_angle_horisontal}, va_v={self._view_angle_vertical}"


class Camera(BaseCam):
    """Класс для фотоаппаратов"""

    def __init__(self, matrix_width: float, matrix_height: float, focal_lenght: float):
        view_angle_horisontal = 2 * np.arctan(matrix_width / (2 * focal_lenght))
        view_angle_vertical = 2 * np.arctan(matrix_height / (2 * focal_lenght))
        super().__init__(view_angle_horisontal, view_angle_vertical)

    def get_view_vectors(self):
        """Возвращает точки соответственно: лв, пв, лн, пн углов"""
        delta_h = np.tan(self._view_angle_horisontal / 2)
        delta_v = np.tan(self._view_angle_vertical / 2)
        return [
            np.array([delta_v, -1, -delta_h]),
            np.array([delta_v, -1, delta_h]),
            np.array([-delta_v, -1, -delta_h]),
            np.array([-delta_v, -1, delta_h]),
        ]

    @classmethod
    def get_circle_view_vectors(
        self, ang_deg: float, vec_num: int = 36
    ) -> list[np.ndarray]:
        """возвращает список векторов для заданного угла обзора"""
        pitch = np.deg2rad(ang_deg / 2)

        res = []

        yaw = 0.0

        step = (np.pi * 2) / vec_num

        cam_default = np.array([0, -1, 0])

        for _ in range(vec_num):
            new = rotation_matrix(yaw, pitch, 0, invert_order=True) @ cam_default
            res.append(new)
            yaw += step
        return res


class Giper(BaseCam):
    """Класс для камер гиперспектрометра, конструктор все значения принимает в градусах"""

    def __init__(
        self,
        view_angle_horisontal: float,
        view_angle_vertical: float,
        camera_pitch: float,
    ):
        super().__init__(
            np.deg2rad(view_angle_horisontal), np.deg2rad(view_angle_vertical)
        )
        self.camera_pitch = np.deg2rad(camera_pitch)

    def get_h_view_vectors(self):
        delta_h = np.tan(self._view_angle_horisontal / 2)
        matrix = rotation_matrix(0, self.camera_pitch, 0)
        return [
            matrix @ np.array([0, -1, delta_h]),
            matrix @ np.array([0, -1, -delta_h]),
        ]

    def get_view_vectors(self):
        return self.get_h_view_vectors()

    def get_center_vector(self) -> np.ndarray:
        matrix = rotation_matrix(0, self.camera_pitch, 0)
        return matrix @ np.array([0, -1, 0])
