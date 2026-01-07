"""Вспомогательные функции для работы с файлами"""

import json
from pathlib import Path

from .constants import DATA_DIR


def load_metadata(filepath: str) -> dict:
    """Загружает метаданные из JSON-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str, data: dict) -> None:
    """Сохраняет метаданные в JSON-файл."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_table_data(table_name: str) -> list:
    """Загружает данные таблицы из JSON-файла."""
    filepath = f'{DATA_DIR}{table_name}.json'
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_table_data(table_name: str, data: list) -> None:
    """Сохраняет данные таблицы в JSON-файл."""
    filepath = f'{DATA_DIR}{table_name}.json'
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

