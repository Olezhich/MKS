import numpy as np


def rotation_matrix(yaw: float, pitch: float, roll: float) -> np.ndarray:
    """Возвращает матрицу поворота для локальной системы координат.
    Порядок применения поворотов: рысканье -> тангаж -> крен"""

    # Рысканье Y
    Ry = np.array(
        [[np.cos(yaw), 0, -np.sin(yaw)], [0, 1, 0], [np.sin(yaw), 0, np.cos(yaw)]]
    )

    # Тангаж Z
    Rz = np.array(
        [
            [np.cos(pitch), np.sin(pitch), 0],
            [-np.sin(pitch), np.cos(pitch), 0],
            [0, 0, 1],
        ]
    )

    # Крен X
    Rx = np.array(
        [[1, 0, 0], [0, np.cos(roll), np.sin(roll)], [0, -np.sin(roll), np.cos(roll)]]
    )

    # Вращать будем в локальной системе координат, поэтому применяем в прямом порядке
    return Rx @ Rz @ Ry
