import pika
import json
import threading
from main.settings import settings

internal_logger = settings.logger


class QueueConfig:
    QUEUE_ARGUMENTS = {
        "x-message-ttl": 604800000,
        "x-max-length": 1000000,
    }

    @staticmethod
    def declare_queue(channel, queue_name):
        """Declare a queue with passive=True first to check if it exists"""
        try:
            channel.queue_declare(queue=queue_name, passive=True)
        except Exception:
            channel.queue_declare(
                queue=queue_name, durable=True, arguments=QueueConfig.QUEUE_ARGUMENTS
            )


class LoggerClient:
    def __init__(self, service_name, rabbitmq_url=settings.get_queue_url):
        self.service_name = service_name
        self.rabbitmq_url = rabbitmq_url
        self._connection = None
        self._channel = None
        self._setup_connection()

        self._monitor_thread = threading.Thread(
            target=self._monitor_connection, daemon=True
        )
        self._monitor_thread.start()

    def _setup_connection(self):
        try:
            params = pika.URLParameters(self.rabbitmq_url)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300

            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()

            self._channel.exchange_declare(
                exchange="logs_exchange", exchange_type="direct", durable=True
            )

            log_levels = ["info", "error", "warning"]
            for level in log_levels:
                queue_name = f"{self.service_name}_{level}_logs"
                QueueConfig.declare_queue(self._channel, queue_name)
                self._channel.queue_bind(
                    exchange="logs_exchange",
                    queue=queue_name,
                    routing_key=f"{self.service_name}.{level}",
                )

            internal_logger.info(f"Logger connected for service: {self.service_name}")

        except Exception as e:
            internal_logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            self._connection = None
            self._channel = None

    def _monitor_connection(self):
        while True:
            if not self._connection or self._connection.is_closed:
                internal_logger.warning("Connection lost, attempting to reconnect...")
                self._setup_connection()
            threading.Event().wait(5)

    def log(self, level, message, information=None):
        if not self._channel:
            internal_logger.error(f"Logging failed - no connection: {message}")
            return

        try:
            from datetime import datetime

            log_data = {
                "service": self.service_name,
                "level": level,
                "message": message,
                "information": information or {},
                "timestamp": str(datetime.now()),
            }

            routing_key = f"{self.service_name}.{level.lower()}"
            properties = pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                timestamp=int(datetime.now().timestamp()),
            )

            self._channel.basic_publish(
                exchange="logs_exchange",
                routing_key=routing_key,
                body=json.dumps(log_data),
                properties=properties,
            )

            internal_logger.info(f"Published message with routing key: {routing_key}")

        except Exception as e:
            internal_logger.error(f"Failed to send log: {str(e)}")

    def __del__(self):
        if self._connection and not self._connection.is_closed:
            try:
                self._connection.close()
            except Exception as e:
                internal_logger.error(f"Error closing connection: {str(e)}")
