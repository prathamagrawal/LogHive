import asyncio
from main.settings import settings,internal_logger
from main.database import DatabaseManager

async def log_to_db(log_data):
    """
    Wrapper function to log data to the database with error handling.

    :param log_data: Dictionary containing log information
    """
    database_url = settings.database_url

    db_manager = DatabaseManager(database_url)

    try:
        await db_manager.write_to_db(log_data)
        internal_logger.info("Log successfully written to database")
    except Exception as e:
        raise(f"Error writing log to database: {e}")

