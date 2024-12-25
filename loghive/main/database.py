from loghive.main.models import LoggingDetails
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


def parse_timestamp(timestamp_value):
    if isinstance(timestamp_value, str):
        try:
            return datetime.strptime(timestamp_value, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return datetime.strptime(timestamp_value, "%Y-%m-%d %H:%M:%S")
    if isinstance(timestamp_value, datetime):
        return timestamp_value

    raise ValueError("Invalid timestamp format")


class DatabaseManager:
    def __init__(self, database_url):
        """
        Initialize the database manager with async engine and session factory.

        :param database_url: Async database connection URL
        """
        self.async_engine = create_async_engine(
            database_url,
            echo=False,  # Set to False in production
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def write_to_db(self, log_data):
        """
        Write log data to the database.

        :param log_data: Dictionary containing log information
        """
        async with self.AsyncSessionLocal() as session:
            try:
                entry = LoggingDetails(
                    service_name=log_data.get("service", "Unknown"),
                    data=log_data.get("message", {}),
                    timestamp=parse_timestamp(
                        log_data.get("timestamp", datetime.utcnow())
                    ),
                    status=log_data.get("level", ""),
                    information=str(
                        log_data.get("information", {}),
                    ),
                )
                session.add(entry)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise
