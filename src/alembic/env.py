from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Add your project root so imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your Base and all models here to register metadata
from db.base import Base
from models.assignment_mapping_models import *
from models.client_models import *
from models.driver_models import *
from models.mfo_models import *
from models.porter_models import *
from models.status_models import *
from models.task_management_models import *
from models.transition_models import *
from models.vehicle_models import *
from models.costing_models import *
from models.log_models import *
from models.attendace_models import *
from db.static_tables_data import *
from models.can_data_model import *

# Alembic Config object to access alembic.ini settings
config = context.config

# Inject dynamic DB URL from your settings or environment
from db.db import DATABASE_URL
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Set up logging from config file
fileConfig(config.config_file_name)

# Alembic uses this to know what tables/models to reflect and compare for migrations
target_metadata = Base.metadata

# Filter out PostGIS system tables from migrations
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in ("geometry_columns", "spatial_ref_sys"):
        return False
    return True

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
