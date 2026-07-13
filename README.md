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