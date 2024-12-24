import logging
import colorlog
import sys
from pydantic_settings import BaseSettings
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

internal_logger = logging.getLogger("internal_logger")


class Settings(BaseSettings):
    log_level: str
    postgres_db_host: str
    postgres_db_name: str
    postgres_db_user: str
    postgres_db_password: str
    postgres_db_port: str
    queue_user: str
    queue_password: str
    queue_host: str
    queue_port: str
    queue_max_size: int
    consumer_batch_size: int
    enable_email_monitoring: bool
    email_host: str
    email_port: int
    email_sender_email: str
    email_sender_password: str

    class Config:
        env_file = "../../config.env"

    @property
    def get_sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_db_user}:"
            f"{self.postgres_db_password}@{self.postgres_db_host}:{self.postgres_db_port}/"
            f"{self.postgres_db_name}"
        )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_db_user}:"
            f"{self.postgres_db_password}@{self.postgres_db_host}:{self.postgres_db_port}/"
            f"{self.postgres_db_name}"
        )

    @property
    def get_queue_url(self) -> str:
        return f"amqp://{self.queue_user}:{self.queue_password}@{self.queue_host}:{self.queue_port}/"

    @contextmanager
    def get_session(self):
        engine = create_engine(self.database_url())
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def logger(self):
        """Returns a configured logger instance with colors."""

        def configure_logger(level=logging.INFO):
            if internal_logger.hasHandlers():
                internal_logger.handlers.clear()

            internal_logger.setLevel(level)

            log_colors = {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }

            formatter = colorlog.ColoredFormatter(
                fmt="%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(asctime)s%(reset)s %(white)s%(message)s%(reset)s",
                log_colors=log_colors,
                secondary_log_colors={},
                style="%",
                reset=True,
            )

            console_handler = colorlog.StreamHandler(stream=sys.stderr)
            console_handler.setFormatter(formatter)
            console_handler.terminator = "\n"
            console_handler.emit = lambda record: sys.stderr.write(
                console_handler.format(record) + console_handler.terminator
            )
            internal_logger.addHandler(console_handler)

        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        level = log_level_map.get(self.log_level.upper(), logging.INFO)
        configure_logger(level)
        return internal_logger

    @property
    def get_service_names(self):
        if self.service_names:
            return self.service_names.split(",")
        else:
            return None


settings = Settings()
