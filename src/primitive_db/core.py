"""Основная логика работы с таблицами и данными."""

from typing import List, Tuple, Dict, Optional, Any

from .decorators import confirm_action, log_time, handle_db_errors
from .constants import VALID_TYPES


def create_table(metadata: dict, table_name: str, columns: List[str]) -> Tuple[dict, str]:
    """Создает новую таблицу в метаданных"""
    if table_name in metadata:
        return metadata, f'Ошибка: Таблица "{table_name}" уже существует.'
    
    parsed_columns = []
    for col in columns:
        if ':' not in col:
            return metadata, f'Некорректное значение: {col}. Попробуйте снова.'
        
        col_name, col_type = col.split(':', 1)
        col_type = col_type.strip().lower()
        
        if col_type not in VALID_TYPES:
            return metadata, f'Некорректное значение: {col}. Попробуйте снова.'
        
        parsed_columns.append(f'{col_name}:{col_type}')
    
    has_id = any(col.startswith('ID:') or col.startswith('id:') for col in parsed_columns)
    if not has_id:
        parsed_columns.insert(0, 'ID:int')
    else:
        id_col = None
        for i, col in enumerate(parsed_columns):
            if col.startswith('ID:') or col.startswith('id:'):
                id_col = parsed_columns.pop(i)
                break
        if id_col:
            parsed_columns.insert(0, id_col)
    
    metadata[table_name] = parsed_columns
    columns_str = ', '.join(parsed_columns)
    return metadata, f'Таблица "{table_name}" успешно создана со столбцами: {columns_str}'


@confirm_action("удаление таблицы")
def drop_table(metadata: dict, table_name: str) -> Tuple[dict, str]:
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        return metadata, f'Ошибка: Таблица "{table_name}" не существует.'
    
    del metadata[table_name]
    return metadata, f'Таблица "{table_name}" успешно удалена.'


def list_tables(metadata: dict) -> str:
    """Возвращает список всех таблиц."""
    if not metadata:
        return ''
    
    tables = list(metadata.keys())
    return '\n'.join(f'- {table}' for table in tables)


def _parse_column_schema(column_str: str) -> Tuple[str, str]:
    col_name, col_type = column_str.split(':', 1)
    return col_name.strip(), col_type.strip().lower()


def _get_table_schema(metadata: dict, table_name: str) -> List[Tuple[str, str]]:
    if table_name not in metadata:
        return []
    return [_parse_column_schema(col) for col in metadata[table_name]]


@handle_db_errors
def _convert_value(value: str, target_type: str) -> Any:
    target_type = target_type.lower()
    if target_type == 'int':
        return int(value)
    elif target_type == 'bool':
        value_lower = value.lower()
        if value_lower in ('true', '1', 'yes'):
            return True
        elif value_lower in ('false', '0', 'no'):
            return False
        else:
            raise ValueError(f'Некорректное значение: {value}. Ожидается bool.')
    elif target_type == 'str':
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        return value
    else:
        raise ValueError(f'Неподдерживаемый тип: {target_type}')


@log_time
def insert(metadata: dict, table_name: str, values: List[str], table_data: List[Dict]) -> Tuple[List[Dict], str]:
    """Вставляет новую запись в таблицу."""
    if table_name not in metadata:
        return table_data, f'Ошибка: Таблица "{table_name}" не существует.'
    
    schema = _get_table_schema(metadata, table_name)
    data_columns = schema[1:]
    
    if len(values) != len(data_columns):
        return table_data, f'Ошибка: Неверное количество значений. Ожидается {len(data_columns)}, получено {len(values)}.'
    
    converted_values = []
    for i, (col_name, col_type) in enumerate(data_columns):
        converted_value = _convert_value(values[i], col_type)
        if converted_value is None:
            return table_data, "Ошибка при преобразовании значения."
        converted_values.append(converted_value)
    
    if table_data:
        max_id = max(record.get('ID', 0) for record in table_data if 'ID' in record)
        new_id = max_id + 1
    else:
        new_id = 1
    
    new_record = {'ID': new_id}
    for i, (col_name, _) in enumerate(data_columns):
        new_record[col_name] = converted_values[i]
    
    table_data.append(new_record)
    return table_data, f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".'


_cache_result = None

def _get_cacher():
    global _cache_result
    if _cache_result is None:
        from .decorators import create_cacher
        _cache_result = create_cacher()
    return _cache_result

@log_time
def select(table_data: List[Dict], where_clause: Optional[Dict[str, Any]] = None) -> List[Dict]:
    """Выбирает записи из таблицы с опциональным условием."""
    if where_clause is None:
        return table_data
    
    cache_key = tuple(sorted(where_clause.items()))
    cacher = _get_cacher()
    
    def _select_impl():
        result = []
        for record in table_data:
            match = True
            for col, value in where_clause.items():
                if col not in record or record[col] != value:
                    match = False
                    break
            if match:
                result.append(record)
        return result
    
    return cacher(cache_key, _select_impl)


def update(table_data: List[Dict], set_clause: Dict[str, Any], where_clause: Dict[str, Any]) -> Tuple[List[Dict], int]:
    """Обновляет записи в таблице по условию."""
    updated_count = 0
    for record in table_data:
        match = True
        for col, value in where_clause.items():
            if col not in record or record[col] != value:
                match = False
                break
        
        if match:
            for col, new_value in set_clause.items():
                record[col] = new_value
            updated_count += 1
    
    return table_data, updated_count


@confirm_action("удаление записи")
def delete(table_data: List[Dict], where_clause: Dict[str, Any]) -> Tuple[List[Dict], int]:
    """Удаляет записи из таблицы по условию."""
    result = []
    deleted_count = 0
    
    for record in table_data:
        match = True
        for col, value in where_clause.items():
            if col not in record or record[col] != value:
                match = False
                break
        
        if not match:
            result.append(record)
        else:
            deleted_count += 1
    
    return result, deleted_count


def get_table_info(metadata: dict, table_name: str, table_data: List[Dict]) -> str:
    """Возвращает информацию о таблице."""
    if table_name not in metadata:
        return f'Ошибка: Таблица "{table_name}" не существует.'
    
    columns_str = ', '.join(metadata[table_name])
    count = len(table_data)
    return f'Таблица: {table_name}\nСтолбцы: {columns_str}\nКоличество записей: {count}'

