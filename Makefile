install:
	@poetry install

database:
	@poetry run database

project:
	@poetry run project

build:
	@poetry build

publish:
	@poetry publish --dry-run

package-install:
	@python3 -m pip install dist/*.whl

lint:
	@poetry run ruff check .

demo_1:
	@asciinema play demo_1.cast

demo_2:
	@asciinema play demo_2.cast

demo_3:
	@asciinema play demo_3.cast

demo_final:
	@asciinema play demo_final.cast

help:
	@echo "Доступные команды:"
	@echo "  install         - Установка зависимостей через poetry"
	@echo "  database        - Запуск базы данных"
	@echo "  project         - Запуск базы данных (альтернативное имя)"
	@echo "  build           - Сборка пакета"
	@echo "  publish         - Тестовая публикация пакета"
	@echo "  package-install - Установка собранного пакета"
	@echo "  lint            - Проверка кода линтером"
	@echo "  demo_1          - Воспроизведение демо-записи (управление таблицами)"
	@echo "  demo_2          - Воспроизведение демо-записи (CRUD-операции)"
	@echo "  demo_3          - Воспроизведение демо-записи (декораторы и обработка ошибок)"
	@echo "  demo_final      - Полный сценарий работы с базой данных"
	@echo "  help            - Показать эту справку"