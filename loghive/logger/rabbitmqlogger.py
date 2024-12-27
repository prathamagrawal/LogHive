import pika
import json
import threading
import time
from datetime import datetime
from loghive.main.settings import settings

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
        self._lock = threading.Lock()  # Add thread safety
        self._should_reconnect = True
        self._reconnect_delay = 1  # Start with 1 second delay
        self._max_reconnect_delay = 30  # Maximum delay between reconnection attempts

        self._setup_connection()

        self._monitor_thread = threading.Thread(
            target=self._monitor_connection, daemon=True
        )
        self._monitor_thread.start()

    def _setup_connection(self):
        """Setup connection with retry logic and exponential backoff"""
        with self._lock:
            try:
                if self._connection and not self._connection.is_closed:
                    return

                params = pika.URLParameters(self.rabbitmq_url)
                params.heartbeat = 600
                params.blocked_connection_timeout = 300
                params.socket_timeout = 10
                retry_count = 0
                max_retries = 3

                while retry_count < max_retries:
                    try:
                        self._connection = pika.BlockingConnection(params)
                        self._channel = self._connection.channel()
                        self._channel.basic_qos(prefetch_count=1)
                        self._channel.exchange_declare(
                            exchange="logs_exchange",
                            exchange_type="direct",
                            durable=True,
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
                        self._reconnect_delay = 1
                        internal_logger.info(
                            f"Logger connected for service: {self.service_name}"
                        )
                        return

                    except pika.exceptions.AMQPConnectionError as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            raise e
                        time.sleep(
                            min(
                                self._reconnect_delay * (2**retry_count),
                                self._max_reconnect_delay,
                            )
                        )

            except Exception as e:
                internal_logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
                self._connection = None
                self._channel = None
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self._max_reconnect_delay
                )

    def _monitor_connection(self):
        """Monitor connection health and reconnect if necessary"""
        while self._should_reconnect:
            try:
                if not self._connection or self._connection.is_closed:
                    internal_logger.warning(
                        "Connection lost, attempting to reconnect..."
                    )
                    self._setup_connection()
                elif self._connection.is_open:
                    try:
                        self._connection.process_data_events()
                    except Exception as e:
                        internal_logger.error(f"Error processing events: {str(e)}")
                        self._setup_connection()
            except Exception as e:
                internal_logger.error(f"Error in connection monitor: {str(e)}")

            time.sleep(5)

    def log(self, level, message, information=None):
        """Send log message with retry logic"""

        log_functions = {
            "DEBUG": internal_logger.debug,
            "INFO": internal_logger.info,
            "WARNING": internal_logger.warning,
            "ERROR": internal_logger.error,
            "CRITICAL": internal_logger.critical,
        }

        log_functions[level](f"{message} {information if information else ''}")

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                with self._lock:
                    if not self._channel or self._connection.is_closed:
                        self._setup_connection()
                        if not self._channel:
                            raise Exception("Failed to establish connection")

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

                    internal_logger.info(
                        f"Published message with routing key: {routing_key}"
                    )
                    return True

            except (
                pika.exceptions.ConnectionClosed,
                pika.exceptions.ChannelClosed,
                pika.exceptions.AMQPConnectionError,
            ) as e:
                retry_count += 1
                if retry_count == max_retries:
                    internal_logger.error(
                        f"Failed to send log after {max_retries} attempts: {str(e)}"
                    )
                    return False
                time.sleep(
                    min(
                        self._reconnect_delay * (2**retry_count),
                        self._max_reconnect_delay,
                    )
                )
                self._setup_connection()

            except Exception as e:
                internal_logger.error(f"Failed to send log: {str(e)}")
                return False

    def close(self):
        """Gracefully close the connection"""
        self._should_reconnect = False
        if self._connection and not self._connection.is_closed:
            try:
                self._connection.close()
            except Exception as e:
                internal_logger.error(f"Error closing connection: {str(e)}")

    def __del__(self):
        self.close()
