import pika
import json
from main.settings import settings

class LoggerConsumer:
    def __init__(self, service_name=None):
        self.rabbitmq_url = settings.get_queue_url
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self._setup_connection()

    def _setup_connection(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()

            # Declare the same exchange as in the LoggerClient
            self.channel.exchange_declare(
                exchange="logs_exchange", exchange_type="direct", durable=True
            )

            # Create a unique queue for this consumer
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue

            # Bind to all logs if no specific service is provided
            if self.service_name:
                binding_keys = [
                    f"{self.service_name}.info",
                    f"{self.service_name}.error",
                    f"{self.service_name}.warning"
                ]
            else:
                # Bind to all logs from all services
                binding_keys = ['#']

            for binding_key in binding_keys:
                self.channel.queue_bind(
                    exchange="logs_exchange",
                    queue=self.queue_name,
                    routing_key=binding_key
                )

            print(f"Log consumer ready. Waiting for logs...")

        except Exception as e:
            print(f"Failed to setup RabbitMQ connection: {e}")

    def consume(self, callback=None):
        def default_callback(ch, method, properties, body):
            try:
                log_data = json.loads(body)
                print(f"Received log: {log_data}")
                # You can add more sophisticated log processing here
            except Exception as e:
                print(f"Error processing log: {e}")

        try:
            # Use provided callback or default
            consume_callback = callback or default_callback

            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=consume_callback,
                auto_ack=True
            )

            self.channel.start_consuming()

        except Exception as e:
            print(f"Error in log consumption: {e}")

    def __del__(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

# Example usage
if __name__ == "__main__":
    # Consume logs from all services
    consumer = LoggerConsumer()
    consumer.consume()

    # Or consume logs from a specific service
    # consumer = LoggerConsumer(service_name="user_service")
    # consumer.consume()