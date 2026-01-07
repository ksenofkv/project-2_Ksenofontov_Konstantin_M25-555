"""Декораторы для обработки ошибок, логирования и подтверждения действий."""

import time
from functools import wraps
from typing import Callable, Any


def handle_db_errors(func: Callable) -> Callable:
    """Декоратор для обработки ошибок базы данных."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, база данных не инициализирована.")
            if args:
                return args[0], "Ошибка: Файл данных не найден."
            return None
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
            if args:
                return args[0], f"Ошибка: Таблица или столбец {e} не найден."
            return None
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
            if args:
                return args[0], f"Ошибка валидации: {e}"
            return None
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            if args:
                return args[0], f"Произошла непредвиденная ошибка: {e}"
            return None
    return wrapper


def confirm_action(action_name: str):
    """Декоратор для запроса подтверждения опасных операций."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ').strip().lower()
            if response != 'y':
                return args[0] if args else None, 'Операция отменена.'
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_time(func: Callable) -> Callable:
    """Декоратор для логирования времени выполнения функции."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start_time
        print(f'Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.')
        return result
    return wrapper


def create_cacher():
    """Создает функцию кэширования с замыканием."""
    cache = {}
    
    def cache_result(key: Any, value_func: Callable) -> Any:
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result
    
    return cache_result

