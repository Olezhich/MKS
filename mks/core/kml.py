import numpy as np
import simplekml  # type: ignore


def split_at_nan(coords: np.ndarray) -> list[np.ndarray]:
    """
    Разбивает массив координат на сегменты в местах, где встречаются NaN.
    coords: np.ndarray формы (N, 2), где столбцы - это [долгота, широта]
    """
    segments: list[np.ndarray] = []
    current_segment = []  # type: ignore

    for point in coords:
        # Проверяем, есть ли NaN в долготе или широте
        if np.isnan(point).any():
            # Если встретили NaN, сохраняем накопленный сегмент (если он не пустой)
            if current_segment:
                segments.append(np.array(current_segment))
                current_segment = []
        else:
            current_segment.append(point)

    # Не забываем добавить последний сегмент
    if current_segment:
        segments.append(np.array(current_segment))

    return segments


def hex_to_kml_color(hex_color: str, alpha: int = 255) -> str:
    """
    Переводит HEX цвет (например, '#FF0000') в формат KML (aabbggrr).
    KML использует обратный порядок цветов (ABGR), а не стандартный RGB!
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Формат KML: Alpha, Blue, Green, Red
    return f"{alpha:02x}{b:02x}{g:02x}{r:02x}"


def create_kml_from_tracks(
    tracks: list[np.ndarray], colors: list[str], output_file: str = "output.kml"
):
    """
    Создает KML файл из списка треков.
    tracks: список np.ndarray с координатами (lon, lat)
    colors: список HEX цветов для каждого трека (или один цвет для всех)
    """
    kml = simplekml.Kml()

    # Если передан один цвет, применяем его ко всем трекам
    if isinstance(colors, str):
        colors = [colors] * len(tracks)

    for i, track in enumerate(tracks):
        # 1. Разбиваем трек на непрерывные сегменты
        segments = split_at_nan(track)

        # 2. Настраиваем стиль (цвет и толщину)
        style = simplekml.Style()
        kml_color = hex_to_kml_color(
            colors[i], alpha=255
        )  # 255 - полная непрозрачность
        style.linestyle.color = kml_color
        style.linestyle.width = 4  # Толщина линии

        # 3. Добавляем каждый сегмент как отдельную LineString
        for seg in segments:
            if len(seg) >= 2:  # Линия должна состоять минимум из 2 точек
                # simplekml ожидает координаты в формате (lon, lat, alt) или (lon, lat)
                ls = kml.newlinestring(name=f"Track_{i + 1}", coords=seg.tolist())
                ls.style = style

    # Сохраняем файл
    kml.save(output_file)
    print(f"KML файл успешно сохранен в {output_file}")
