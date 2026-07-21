from datetime import datetime
from pathlib import Path
from typing import IO, Generator
import numpy as np

import re

from mks.models import Station

# Пример строки Orbita_UTC
# 2026 06 29 14 00 02.673  -4628.335  2300.186  4409.189 -0.037343 -6.541189  3.365051  -176.110  -0.893   7.001  424.5   40.646  153.574  -26.0 1367/12

datetime_pattern = re.compile(r"(\d{4}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\.\d+)\b")

float_pattern = re.compile(r"(-?\d+\.\d+)\b")

circle_pattern = re.compile(r"(\d+)/\d+")

datetime_str = r"%Y %m %d %H %M %S.%f"


def parse_telemetry_f_fp(
    fp: IO[str], start: datetime, end: datetime
) -> Generator[tuple[Station, int], None, None]:
    """Парсит файл Orbita_UTC"""
    position: list[list[float]] = []
    velocity: list[list[float]] = []
    ang: list[float] = []
    cur_circle: int | None = None

    try:
        next(fp)  # Строка с заголовком
        next(fp)  # Пустая строка
    except StopIteration:
        raise ValueError("Файл должен начинаться с заголовочной и пустой строк")

    for line in fp:
        match_time = datetime_pattern.match(line)
        if not match_time:  # Пропускаем строки с мусором
            continue

        current = datetime.strptime(match_time.group(1), datetime_str)

        if current >= end:
            break
        if current <= start:
            continue

        pos = match_time.end()
        cur_vectors: list[float] = []

        try:
            for _ in range(13):
                match_val = float_pattern.search(line, pos)
                if not match_val:
                    raise ValueError(f'Ошибка в строке: "{line}"')
                cur_vectors.append(float(match_val.group(1)))
                pos = match_val.end()
        except Exception:
            raise ValueError(f'Не правильный формат строки: "{line}"')

        match_circle = circle_pattern.search(line, pos)
        if not match_circle:
            raise ValueError(f'Нет номера витка в строке: "{line}"')
        new_circle = int(match_circle.group(1))

        if cur_circle:
            if new_circle != cur_circle:
                yield (
                    Station(
                        np.deg2rad(ang[1]),
                        np.deg2rad(ang[2]),
                        np.deg2rad(ang[0]),
                        np.array(position),
                        np.array(velocity),
                    ),
                    cur_circle,
                )
                cur_circle = new_circle
                position.clear()
                velocity.clear()
        else:
            cur_circle = new_circle

        position.append(cur_vectors[:3])
        velocity.append(cur_vectors[3:6])

        if not ang:
            ang = cur_vectors[6:9]

    if not ang:
        print(position)
        raise ValueError("Нет строк в указанном диапазоне")

    if not cur_circle:
        raise ValueError("Нет подходящих строк")

    yield (
        Station(
            np.deg2rad(ang[1]),
            np.deg2rad(ang[2]),
            np.deg2rad(ang[0]),
            np.array(position),
            np.array(velocity),
        ),
        cur_circle,
    )


def parse_telemetry(
    filepath: Path, start: datetime, end: datetime, encoding: str = "cp1251"
) -> Generator[tuple[Station, int], None, None]:
    with open(filepath, "r", encoding=encoding) as fp:
        for circle in parse_telemetry_f_fp(fp, start, end):
            yield circle


def parse_telemetry_batch(
    filepath: Path, start: datetime, end: datetime, encoding: str = "cp1251"
) -> Station:
    pos = []
    vel = []
    with open(filepath, "r", encoding=encoding) as fp:
        for circle, _ in parse_telemetry_f_fp(fp, start, end):
            for point in circle.position:
                pos.append(point)
            for point in circle.velocity:
                vel.append(point)
            roll = circle.roll
            pitch = circle.pitch
            yaw = circle.yaw

    return Station(roll, pitch, yaw, np.array(pos), np.array(vel))
