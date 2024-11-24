import pika
import json
from main.settings import settings

internal_logger = settings.logger


class QueueConfig:
    QUEUE_ARGUMENTS = {
        "x-message-ttl": 604800000,  # 7 days in milliseconds
        "x-max-length": 1000000,  # Max messages in queue
    }

    @staticmethod
    def declare_queue(channel, queue_name):
        """Declare a queue with passive=True first to check if it exists"""
        try:
            # First, try to check if queue exists
            channel.queue_declare(queue=queue_name, passive=True)
        except Exception:
            # If queue doesn't exist, create it with our parameters
            channel.queue_declare(
                queue=queue_name, durable=True, arguments=QueueConfig.QUEUE_ARGUMENTS
            )


class LoggerConsumer:
    def __init__(self, service_name=None):
        self.rabbitmq_url = settings.get_queue_url
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self._setup_connection()

    def _setup_connection(self):
        try:
            params = pika.URLParameters(self.rabbitmq_url)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange="logs_exchange", exchange_type="direct", durable=True
            )

            self.queues = []
            if self.service_name:
                for level in ["info", "error", "warning"]:
                    queue_name = f"{self.service_name}_{level}_logs"
                    QueueConfig.declare_queue(self.channel, queue_name)

                    self.channel.queue_bind(
                        exchange="logs_exchange",
                        queue=queue_name,
                        routing_key=f"{self.service_name}.{level}",
                    )
                    self.queues.append(queue_name)
            else:
                # For listening to all services
                queue_name = "all_logs"
                QueueConfig.declare_queue(self.channel, queue_name)

                self.channel.queue_bind(
                    exchange="logs_exchange", queue=queue_name, routing_key="#"
                )
                self.queues.append(queue_name)

            internal_logger.info(
                f"Log consumer ready. Listening to queues: {self.queues}"
            )

        except Exception as e:
            internal_logger.error(f"Failed to setup RabbitMQ connection: {str(e)}")
            raise

    def consume(self, callback=None):
        def default_callback(ch, method, properties, body):
            try:
                log_data = json.loads(body)
                internal_logger.info(f"Received log: {log_data}")
            except Exception as e:
                internal_logger.error(f"Error processing log: {str(e)}")

        try:
            consume_callback = callback or default_callback

            for queue in self.queues:
                self.channel.basic_consume(
                    queue=queue, on_message_callback=consume_callback, auto_ack=True
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


# Example usage
if __name__ == "__main__":
    consumer = LoggerConsumer("flask_service")
    consumer.consume()
