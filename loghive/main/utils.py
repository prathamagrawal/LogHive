from loghive.main.settings import settings, internal_logger
from loghive.main.database import DatabaseManager
from loghive.main.sendemail import send_email


async def log_to_db(log_data):
    """
    Wrapper function to log data to the database with error handling.

    :param log_data: Dictionary containing log information
    """
    database_url = settings.database_url

    db_manager = DatabaseManager(database_url)

    try:
        await db_manager.write_to_db(log_data)
        internal_logger.info(
            f"Log successfully written to database for service: {log_data.get('service')}"
        )
        if settings.enable_email_monitoring and log_data.get("level").lower() in [
            "critical",
            "error",
        ]:
            internal_logger.error(
                f"Found error log for service: {log_data.get('service')}"
            )
            internal_logger.error("Showing logs received: ")
            internal_logger.error(log_data.get("message"))
            internal_logger.error(log_data.get("information"))
            send_email(
                ["prathamagrawal1205@gmail.com", "prathamagrawal1205@gmail.com"],
                f"Error logged for: {log_data.get('service')}",
                message=log_data.get("message"),
                information=log_data.get("information"),
            )
    except Exception as e:
        raise e
