"""Парсеры для разбора команд SQL-подобного синтаксиса."""

from typing import Dict, Any, Optional


def parse_where_clause(where_str: str, metadata: dict, table_name: str) -> Optional[Dict[str, Any]]:
    """Парсит условие WHERE в словарь."""
    if not where_str:
        return None
    
    parts = where_str.split('=', 1)
    if len(parts) != 2:
        return None
    
    col_name = parts[0].strip()
    value_str = parts[1].strip()
    
    if table_name not in metadata:
        return None
    
    col_type = None
    for col_def in metadata[table_name]:
        if ':' in col_def:
            name, col_type_str = col_def.split(':', 1)
            if name.strip().lower() == col_name.lower():
                col_type = col_type_str.strip().lower()
                break
    
    if col_type is None:
        return None
    
    try:
        if col_type == 'int':
            value = int(value_str)
        elif col_type == 'bool':
            value_lower = value_str.lower()
            if value_lower in ('true', '1', 'yes'):
                value = True
            elif value_lower in ('false', '0', 'no'):
                value = False
            else:
                return None
        elif col_type == 'str':
            if (value_str.startswith('"') and value_str.endswith('"')) or \
               (value_str.startswith("'") and value_str.endswith("'")):
                value = value_str[1:-1]
            else:
                value = value_str
        else:
            return None
        
        return {col_name: value}
    except (ValueError, AttributeError):
        return None


def parse_set_clause(set_str: str, metadata: dict, table_name: str) -> Optional[Dict[str, Any]]:
    """Парсит условие SET в словарь."""
    if not set_str:
        return None
    
    result = {}
    assignments = set_str.split(',')
    
    for assignment in assignments:
        parts = assignment.split('=', 1)
        if len(parts) != 2:
            return None
        
        col_name = parts[0].strip()
        value_str = parts[1].strip()
        
        if table_name not in metadata:
            return None
        
        col_type = None
        for col_def in metadata[table_name]:
            if ':' in col_def:
                name, col_type_str = col_def.split(':', 1)
                if name.strip().lower() == col_name.lower():
                    col_type = col_type_str.strip().lower()
                    break
        
        if col_type is None:
            return None
        
        try:
            if col_type == 'int':
                value = int(value_str)
            elif col_type == 'bool':
                value_lower = value_str.lower()
                if value_lower in ('true', '1', 'yes'):
                    value = True
                elif value_lower in ('false', '0', 'no'):
                    value = False
                else:
                    return None
            elif col_type == 'str':
                if (value_str.startswith('"') and value_str.endswith('"')) or \
                   (value_str.startswith("'") and value_str.endswith("'")):
                    value = value_str[1:-1]
                else:
                    value = value_str
            else:
                return None
            
            result[col_name] = value
        except (ValueError, AttributeError):
            return None
    
    return result if result else None








