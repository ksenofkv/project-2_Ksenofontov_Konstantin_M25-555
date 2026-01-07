"""Запуск, игровой цикл и парсинг команд."""

import shlex
from prettytable import PrettyTable

from .core import (
    create_table, drop_table, list_tables,
    insert, select, update, delete, get_table_info
)
from .utils import load_metadata, save_metadata, load_table_data, save_table_data
from .parser import parse_where_clause, parse_set_clause
from .constants import DB_META_FILE


def print_help():
    """Выводит справочную информацию"""
    print("\n***Операции с данными***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) - создать запись.")
    print("<command> select from <имя_таблицы> where <столбец> = <значение> - прочитать записи по условию.")
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print("<command> update <имя_таблицы> set <столбец1> = <новое_значение1> where <столбец_условия> = <значение_условия> - обновить запись.")
    print("<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить запись.")
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def format_select_output(table_data: list, metadata: dict, table_name: str) -> str:
    """Форматирует результат select в виде таблицы."""
    if not table_data or table_name not in metadata:
        return ""
    
    columns = []
    for col_def in metadata[table_name]:
        if ':' in col_def:
            col_name = col_def.split(':', 1)[0].strip()
            columns.append(col_name)
    
    table = PrettyTable()
    table.field_names = columns
    
    for record in table_data:
        row = []
        for col in columns:
            value = record.get(col, '')
            if isinstance(value, bool):
                value = 'True' if value else 'False'
            row.append(str(value))
        table.add_row(row)
    
    return str(table)


def run():
    """Главная функция с основным циклом программы."""
    print("***Операции с данными***")
    print_help()
    
    while True:
        metadata = load_metadata(DB_META_FILE)
        user_input = input(">>>Введите команду: ").strip()
        
        if not user_input:
            continue
        
        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue
        
        if not args:
            continue
        
        command = args[0].lower()
        if command == 'exit':
            break
        elif command == 'help':
            print_help()
        elif command == 'create_table':
            if len(args) < 3:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_name = args[1]
            columns = args[2:]
            metadata, message = create_table(metadata, table_name, columns)
            print(message)
            
            if 'успешно создана' in message:
                save_metadata(DB_META_FILE, metadata)
        elif command == 'list_tables':
            tables_list = list_tables(metadata)
            if tables_list:
                print(tables_list)
            else:
                print("Таблицы отсутствуют.")
        elif command == 'drop_table':
            if len(args) < 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_name = args[1]
            metadata, message = drop_table(metadata, table_name)
            print(message)
            
            if 'успешно удалена' in message:
                save_metadata(DB_META_FILE, metadata)
                import os
                from .constants import DATA_DIR
                data_file = f'{DATA_DIR}{table_name}.json'
                if os.path.exists(data_file):
                    os.remove(data_file)
        elif command == 'insert' and len(args) >= 2 and args[1].lower() == 'into':
            if len(args) < 4 or args[3].lower() != 'values':
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_name = args[2]
            values_str = ' '.join(args[4:])
            if values_str.startswith('(') and values_str.endswith(')'):
                values_str = values_str[1:-1]
            
            try:
                values = shlex.split(values_str.replace(',', ' '))
            except ValueError:
                values = [v.strip().strip('"').strip("'") for v in values_str.split(',')]
            
            table_data = load_table_data(table_name)
            table_data, message = insert(metadata, table_name, values, table_data)
            print(message)
            
            if 'успешно добавлена' in message:
                save_table_data(table_name, table_data)
        elif command == 'select' and len(args) >= 2 and args[1].lower() == 'from':
            # select from <table> [where <condition>]
            if len(args) < 3:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_name = args[2]
            
            where_clause = None
            if len(args) > 3 and args[3].lower() == 'where':
                where_str = ' '.join(args[4:])
                where_clause = parse_where_clause(where_str, metadata, table_name)
                if where_clause is None:
                    print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                    continue
            
            table_data = load_table_data(table_name)
            result = select(table_data, where_clause)
            output = format_select_output(result, metadata, table_name)
            if output:
                print(output)
            else:
                print("Записи не найдены.")
        elif command == 'update':
            # update <table> set <col1> = <val1> where <col2> = <val2>
            if len(args) < 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_name = args[1]
            
            set_idx = -1
            where_idx = -1
            for i, arg in enumerate(args):
                if arg.lower() == 'set':
                    set_idx = i
                elif arg.lower() == 'where':
                    where_idx = i
            
            if set_idx == -1 or where_idx == -1:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            set_str = ' '.join(args[set_idx + 1:where_idx])
            where_str = ' '.join(args[where_idx + 1:])
            
            set_clause = parse_set_clause(set_str, metadata, table_name)
            where_clause = parse_where_clause(where_str, metadata, table_name)
            
            if set_clause is None or where_clause is None:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_data = load_table_data(table_name)
            table_data, updated_count = update(table_data, set_clause, where_clause)
            
            if updated_count > 0:
                updated_ids = []
                for record in table_data:
                    match = True
                    for col, value in where_clause.items():
                        if record.get(col) != value:
                            match = False
                            break
                    if match and 'ID' in record:
                        updated_ids.append(record['ID'])
                
                if updated_ids:
                    print(f'Запись с ID={updated_ids[0]} в таблице "{table_name}" успешно обновлена.')
                else:
                    print(f'Записи в таблице "{table_name}" успешно обновлены.')
                save_table_data(table_name, table_data)
            else:
                print('Записи не найдены.')
        elif command == 'delete' and len(args) >= 2 and args[1].lower() == 'from':
            # delete from <table> where <condition>
            if len(args) < 4 or args[3].lower() != 'where':
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_name = args[2]
            where_str = ' '.join(args[4:])
            
            where_clause = parse_where_clause(where_str, metadata, table_name)
            if where_clause is None:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_data = load_table_data(table_name)
            deleted_ids = []
            for record in table_data:
                match = True
                for col, value in where_clause.items():
                    if record.get(col) != value:
                        match = False
                        break
                if match and 'ID' in record:
                    deleted_ids.append(record['ID'])
            
            table_data, deleted_count = delete(table_data, where_clause)
            
            if deleted_count > 0:
                if deleted_ids:
                    print(f'Запись с ID={deleted_ids[0]} успешно удалена из таблицы "{table_name}".')
                else:
                    print(f'Записи успешно удалены из таблицы "{table_name}".')
                save_table_data(table_name, table_data)
            else:
                print('Записи не найдены.')
        elif command == 'info':
            if len(args) < 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            
            table_name = args[1]
            table_data = load_table_data(table_name)
            message = get_table_info(metadata, table_name, table_data)
            print(message)
        else:
            print(f"Функции {command} нет. Попробуйте снова.")
