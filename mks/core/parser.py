from datetime import datetime
from pathlib import Path
from typing import IO
import numpy as np

import re

# 2026 06 29 14 00 02.673  -4628.335  2300.186  4409.189 -0.037343 -6.541189  3.365051  -176.110  -0.893   7.001  424.5   40.646  153.574  -26.0 1367/12

datetime_pattern = re.compile(r"(\d{4}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\.\d+)\b")

float_pattern = re.compile(r"(-?\d+\.\d+)\b")

datetime_str = r"%Y %m %d %H %M %S.%f"


def parse_telemetry_f_fp(
    fp: IO[str], start: datetime, end: datetime
) -> tuple[float, float, float, np.ndarray, np.ndarray]:
    """Парсит файл Orbita_UTC"""
    position: list[list[float]] = []
    velocity: list[list[float]] = []
    ang: list[float] = []

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

        num = 6 if ang else 9

        for _ in range(num):
            match_val = float_pattern.search(line, pos)
            if not match_val:
                raise ValueError(f'Ошибка в строке: "{line}"')
            cur_vectors.append(float(match_val.group(1)))
            pos = match_val.end()

        position.append(cur_vectors[:3])
        velocity.append(cur_vectors[3:6])

        if not ang:
            ang = cur_vectors[6:9]

    if not ang:
        print(position)
        raise ValueError("Нет строк в указанном диапазоне")

    return (
        np.deg2rad(ang[1]),
        np.deg2rad(ang[2]),
        np.deg2rad(ang[0]),
        np.array(position),
        np.array(velocity),
    )


def parse_telemetry(
    filepath: Path, start: datetime, end: datetime, encoding: str = "cp1251"
) -> tuple[float, float, float, np.ndarray, np.ndarray]:
    with open(filepath, "r", encoding=encoding) as fp:
        return parse_telemetry_f_fp(fp, start, end)
