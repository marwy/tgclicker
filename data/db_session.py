from tortoise import Tortoise
from tortoise.transactions import in_transaction


async def create_engine(uri):
    # Инициализация базы данных
    await Tortoise.init(db_url=uri, modules={'models': ['data.models']})


async def disconnect():
    # Отключение от базы данных
    await Tortoise.close_connections()


async def create_tables():
    # Создание таблиц (safe=False вызывает метод sql DROP TABLE который просто всё сносит в бд)
    await Tortoise.generate_schemas(safe=False)


async def full_reset_database(uri):
    # Полный сброс базы данных
    await create_engine(uri)
    await create_tables()
    await disconnect()


async def reset_database(uri):
    # Подключение и отключение без сброса данных
    await create_engine(uri)
    await disconnect()


async def global_init(db_file, reset_db=True):
    # Инцилизация базы данных и проверка её пути
    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")
    else:
        conn_str = f'sqlite://{db_file.strip()}'
        print(f"Подключение к базы данных по адресу {conn_str}")
        if reset_db:
            await full_reset_database(conn_str)
        else:
            await reset_database(conn_str)


async def create_session() -> in_transaction:
    # Создает сессию
    return in_transaction()

