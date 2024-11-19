import pika
import json
import threading
from functools import wraps
from main.settings import settings


class LoggerClient:
    def __init__(self, service_name, rabbitmq_url=settings.get_queue_url):
        print(rabbitmq_url)
        self.service_name = service_name
        self.rabbitmq_url = rabbitmq_url
        self._connection = None
        self._channel = None
        self._setup_connection()

        # Start connection monitor in background
        self._monitor_thread = threading.Thread(
            target=self._monitor_connection, daemon=True
        )
        self._monitor_thread.start()

    def _setup_connection(self):
        try:
            # Create connection
            self._connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self._channel = self._connection.channel()

            # Declare exchange
            self._channel.exchange_declare(
                exchange="logs_exchange", exchange_type="direct", durable=True
            )

            print(f"Logger connected for service: {self.service_name}")

        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            self._connection = None
            self._channel = None

    def _monitor_connection(self):
        while True:
            if not self._connection or self._connection.is_closed:
                self._setup_connection()
            threading.Event().wait(5)  # Check every 5 seconds

    def log(self, level, message, extra=None):
        if not self._channel:
            print(f"Logging failed - no connection: {message}")
            return

        try:
            from datetime import datetime

            log_data = {
                "service": self.service_name,
                "level": level,
                "message": message,
                "extra": extra or {},
                "timestamp": str(datetime.now()),
            }

            self._channel.basic_publish(
                exchange="logs_exchange",
                routing_key=f"{self.service_name}.{level.lower()}",
                body=json.dumps(log_data),
                properties=pika.BasicProperties(delivery_mode=2),  # persistent message
            )
        except Exception as e:
            print(f"Failed to send log: {e}")

    def __del__(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()


# Decorator for logging function calls
def log_function(logger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.log("INFO", f"Function {func.__name__} executed successfully")
                return result
            except Exception as e:
                logger.log(
                    "ERROR", f"Function {func.__name__} failed", {"error": str(e)}
                )
                raise

        return wrapper

    return decorator
