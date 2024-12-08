import pika
import json
import time
import asyncio
from main.settings import settings
from main.utils import log_to_db

internal_logger = settings.logger


class QueueConfig:
    QUEUE_ARGUMENTS = {
        "x-message-ttl": 604800000,
        "x-max-length": 1000000,
    }

    @staticmethod
    def declare_queue(channel, queue_name):
        """Declare a queue with proper error handling"""
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments=QueueConfig.QUEUE_ARGUMENTS
        )


class LoggerConsumer:
    def __init__(self, service_name=None, max_retries=5, retry_delay=5):
        self.rabbitmq_url = settings.get_queue_url
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._setup_connection_with_retry()

    def _setup_connection_with_retry(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self._setup_connection()
                return
            except Exception as e:
                retries += 1
                internal_logger.error(f"Connection attempt {retries} failed: {str(e)}")
                if retries < self.max_retries:
                    internal_logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    internal_logger.error("Max retries reached. Failed to establish connection.")
                    raise

    def _setup_connection(self):
        try:
            params = pika.URLParameters(self.rabbitmq_url)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

            self.channel.exchange_declare(
                exchange="logs_exchange",
                exchange_type="direct",
                durable=True
            )

            self.queues = []
            if self.service_name:
                for level in ["info", "error", "warning"]:
                    queue_name = f"{self.service_name}_{level}_logs"
                    # Declare queue
                    QueueConfig.declare_queue(self.channel, queue_name)

                    # Bind queue to exchange
                    self.channel.queue_bind(
                        exchange="logs_exchange",
                        queue=queue_name,
                        routing_key=f"{self.service_name}.{level}",
                    )
                    self.queues.append(queue_name)
            else:
                queue_name = "all_logs"
                QueueConfig.declare_queue(self.channel, queue_name)
                self.channel.queue_bind(
                    exchange="logs_exchange",
                    queue=queue_name,
                    routing_key="#"
                )
                self.queues.append(queue_name)

            internal_logger.info(f"Log consumer ready. Listening to queues: {self.queues}")

        except Exception as e:
            internal_logger.error(f"Failed to setup RabbitMQ connection: {str(e)}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            raise

    def consume(self, callback=None):
        def default_callback(ch, method, properties, body):
            try:
                log_data = json.loads(body)
                internal_logger.info(f"Received log: {log_data}")
                try:
                    asyncio.run(log_to_db(log_data))
                except Exception as e:
                    print(f"Failed to log to database: {e}")
            except Exception as e:
                internal_logger.error(f"Error processing log: {str(e)}")

        try:
            if not self.channel or self.channel.is_closed:
                internal_logger.warning("Channel is closed, attempting to reconnect...")
                self._setup_connection_with_retry()

            consume_callback = callback or default_callback

            for queue in self.queues:
                self.channel.basic_consume(
                    queue=queue,
                    on_message_callback=consume_callback,
                    auto_ack=True
                )

            internal_logger.info("Starting to consume messages...")
            self.channel.start_consuming()

        except Exception as e:
            internal_logger.error(f"Error in log consumption: {str(e)}")
            raise

    def __del__(self):
        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
            except Exception as e:
                internal_logger.error(f"Error closing connection: {str(e)}")


if __name__ == "__main__":
    while True:
        try:
            consumer = LoggerConsumer("flask_service")
            consumer.consume()
        except KeyboardInterrupt:
            internal_logger.info("Shutting down consumer...")
            break
        except Exception as e:
            internal_logger.error(f"Consumer error: {str(e)}")
            internal_logger.info("Restarting consumer in 5 seconds...")
            time.sleep(5)