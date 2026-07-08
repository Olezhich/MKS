import numpy as np
from abc import ABC, abstractmethod


class BaseCam(ABC):
    """Базовый класс для камер. Должен предоставлять набор необходимых векторов для отрисовки.
    Система координат камеры: X - вправо, Y - вперед, Z - вверх"""

    def __init__(self, view_angle_horisontal: float, view_angle_vertical: float):
        self._view_angle_horisontal: float = view_angle_horisontal
        self._view_angle_vertical: float = view_angle_vertical

    @abstractmethod
    def get_view_vectors(self) -> list[np.ndarray]:
        pass

    def get_center_vector(self) -> np.ndarray:
        return np.array([0, 1, 0])

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
            np.array([-delta_h, 1, delta_v]),
            np.array([delta_h, 1, delta_v]),
            np.array([-delta_h, 1, -delta_v]),
            np.array([delta_h, 1, delta_v]),
        ]
