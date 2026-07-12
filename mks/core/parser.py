from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Point:
    # Дата
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: float
    # Координаты
    x_greenwich: float
    y_greenwich: float
    z_greenwich: float
    vx_greenwich: float
    vy_greenwich: float
    vz_greenwich: float
    # Углы
    yaw: float  # рыскание
    roll: float  # крен
    pitch: float  # тангаж

    altitude: float  # высота
    latitude: float  # широта
    longitude: float  # долгота

    sun: float  # Солнце
    orbit_pass: str  # Виток П

    def get_datetime(self) -> datetime:
        return datetime(
            self.year, self.month, self.day, self.hour, self.minute, int(self.second)
        )


def parse_telemetry_file(filepath: str, encoding: str = "cp1251") -> List[Point]:
    points_list = []  # type: ignore
    try:
        with open(filepath, "r", encoding=encoding) as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        print("Не удалось прочитать файл.")
        return points_list

    data_lines = lines[1:]

    for line_num, line in enumerate(data_lines, start=2):
        line = line.strip()
        if not line:
            continue
        parts = line.split()

        if len(parts) < 19:
            print(
                f"Строка {line_num} содержит неверное количество колонок: {len(parts)}"
            )
            continue

        try:
            if "/" in parts[0]:
                # ФОРМАТ 1: orbit_pass в начале
                point = Point(
                    orbit_pass=parts[0],
                    year=int(parts[1]),
                    month=int(parts[2]),
                    day=int(parts[3]),
                    hour=int(parts[4]),
                    minute=int(parts[5]),
                    second=float(parts[6]),
                    x_greenwich=float(parts[7]),
                    y_greenwich=float(parts[8]),
                    z_greenwich=float(parts[9]),
                    vx_greenwich=float(parts[10]),
                    vy_greenwich=float(parts[11]),
                    vz_greenwich=float(parts[12]),
                    yaw=float(parts[13]),
                    roll=float(parts[14]),
                    pitch=float(parts[15]),
                    altitude=float(parts[16]),
                    latitude=float(parts[17]),
                    longitude=float(parts[18]),
                    sun=float(parts[19]) if len(parts) > 19 else 0.0,
                )
            else:
                # ФОРМАТ 2: year в начале
                point = Point(
                    year=int(parts[0]),
                    month=int(parts[1]),
                    day=int(parts[2]),
                    hour=int(parts[3]),
                    minute=int(parts[4]),
                    second=float(parts[5]),
                    x_greenwich=float(parts[6]),
                    y_greenwich=float(parts[7]),
                    z_greenwich=float(parts[8]),
                    vx_greenwich=float(parts[9]),
                    vy_greenwich=float(parts[10]),
                    vz_greenwich=float(parts[11]),
                    yaw=float(parts[12]),
                    roll=float(parts[13]),
                    pitch=float(parts[14]),
                    altitude=float(parts[15]),
                    latitude=float(parts[16]),
                    longitude=float(parts[17]),
                    sun=float(parts[18]),
                    orbit_pass=parts[19] if len(parts) > 19 else "unknown",
                )

            points_list.append(point)
        except ValueError as e:
            print(f"Ошибка преобразования данных в строке {line_num}: {e}")
            continue

    return points_list
