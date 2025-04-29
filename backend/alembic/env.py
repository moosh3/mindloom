import os
import sys
from logging.config import fileConfig
import asyncio
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add the project source directory to the Python path
# This ensures Alembic can find our models
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

# Import the Base object which contains the metadata
from mindloom.db.base import Base

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Actual migration runner logic."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the raw SQLAlchemy URL string from the config
    db_url_config = config.get_main_option("sqlalchemy.url")
    if not db_url_config:
        raise ValueError("Database URL not configured in alembic.ini.")

    # Manually resolve 'env:VAR_NAME' if present
    if db_url_config.startswith("env:"):
        var_name = db_url_config.split(":", 1)[1]
        resolved_db_url = os.getenv(var_name)
        if not resolved_db_url:
            raise ValueError(f"Environment variable {var_name} not set for database URL.")
    else:
        resolved_db_url = db_url_config

    # Create the async engine explicitly with the resolved URL
    connectable = create_async_engine(
        resolved_db_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
