import os
from threading import Lock
from alembic.config import Config
from alembic import command


def run_migrations():
    migration_lock = Lock()

    with migration_lock:
        alembic_cfg = Config(f"{os.path.join(os.path.dirname(__file__))}/alembic.ini")
        alembic_cfg.set_main_option(
            "script_location",
            os.path.join(os.path.dirname(__file__), "alembic"),
        )
        command.upgrade(alembic_cfg, "head")
