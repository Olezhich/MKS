# MKS

## Установка

```shell

git clone https://github.com/Olezhich/MKS.git

cd MKS

poetry install

```

## Запуск

```shell
# на данный момент 
poetry run python test.py
```

## Слияние веток
Чтобы проверка прошла, нужно локально прогнать ruff и mypy

```shell 
# Запускаем локально из корны проекта скрипт со всеми проверками
make fix
```

## Структура проекта

```shell
.
├── mks
│   ├── app
│   ├── core
│   │   ├── core.py
│   │   ├── kml.py
│   │   └── parser.py
│   ├── map
│   ├── models
│   │   ├── cam.py
│   │   ├── mount.py
│   │   └── station.py
│   └── utils
│       └── math.py
└── test.py

```
### Модули
- app - модуль приложения (графический интерфейс и тд)
- core - отвечает за расчет точек на карте
- map - отвечает за карту
- models - модели данных
- utils - нужен для разрешения конфликтов импортов