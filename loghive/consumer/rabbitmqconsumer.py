import pika
import json
import time
import asyncio
import queue
import threading
from loghive.main.settings import settings
from loghive.main.utils import log_to_db

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
            queue=queue_name, durable=True, arguments=QueueConfig.QUEUE_ARGUMENTS
        )


class Consumer:
    def __init__(
        self,
        service_names=None,
        max_workers=10,  # Configurable thread pool size
        batch_size=200,  # Number of messages to process in a batch
        max_queue_size=100000000,  # Maximum queue size before backpressure
        max_retries=5,
        retry_delay=5,
        fallback_consumer=False,
    ):
        self.rabbitmq_url = settings.get_queue_url
        self.service_names = service_names
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.fallback_consumer = fallback_consumer
        self.message_queue = queue.Queue(maxsize=max_queue_size)
        self.error_queue = queue.Queue(maxsize=max_queue_size)
        self.stop_event = threading.Event()
        self.consumer_thread = None
        self.processor_thread = None
        self.queues = []
        self.connection = None
        self.channel = None

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
                    internal_logger.error(
                        "Max retries reached. Failed to establish connection."
                    )
                    raise

    def _setup_connection(self):
        try:
            params = pika.URLParameters(self.rabbitmq_url)
            params.heartbeat = 600
            params.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

            if not self.fallback_consumer:
                if self.service_names:
                    for service_name in self.service_names:
                        for level in ["info", "error", "warning", "debug", "critical"]:
                            queue_name = f"{service_name}_{level}_logs"
                            QueueConfig.declare_queue(self.channel, queue_name)
                            self.channel.queue_bind(
                                exchange="logs_exchange",
                                queue=queue_name,
                                routing_key=f"{service_name}.{level}",
                            )
                            self.queues.append(queue_name)
                else:
                    queue_name = "all_logs"
                    QueueConfig.declare_queue(self.channel, queue_name)
                    self.channel.queue_bind(
                        exchange="logs_exchange", queue=queue_name, routing_key="#"
                    )
                    self.queues.append(queue_name)
            else:
                self.channel.exchange_declare(
                    exchange="logs_exchange", exchange_type="direct", durable=True
                )
                self.channel.exchange_declare(
                    exchange="failure_backoff", exchange_type="direct", durable=True
                )
                queue_name = "failure_backoff"
                QueueConfig.declare_queue(self.channel, queue_name)
                self.channel.queue_bind(
                    exchange="failure_backoff",
                    queue=queue_name,
                    routing_key="failure.backoff",
                )
                self.queues.append(queue_name)

            internal_logger.info(
                f"Log consumer ready. Listening to queues: {self.queues}"
            )

        except Exception as e:
            internal_logger.error(f"Failed to setup RabbitMQ connection: {str(e)}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            raise

    async def _process_batch(self, batch):
        """Process a batch of log messages with robust error handling"""
        failed_messages = []

        for log_data in batch:
            try:
                await log_to_db(log_data)
            except Exception as e:
                internal_logger.error(f"Error processing log message: {e}")
                failed_messages.append(log_data)

        if failed_messages:
            try:
                for failed_message in failed_messages:
                    self.channel.basic_publish(
                        exchange="failure_backoff",
                        routing_key="failure.backoff",
                        body=json.dumps(failed_message),
                        properties=pika.BasicProperties(delivery_mode=2),
                    )
                internal_logger.info(
                    f"Sent {len(failed_messages)} failed messages to failure_backoff queue"
                )
            except Exception as publish_error:
                internal_logger.error(
                    f"Failed to publish to failure_backoff: {publish_error}"
                )

    def _processor_worker(self):
        """Worker method to process messages from queue in batches"""
        while not self.stop_event.is_set():
            try:
                batch = []
                while len(batch) < self.batch_size:
                    try:
                        log_data = self.message_queue.get(timeout=1)
                        batch.append(log_data)
                    except queue.Empty:
                        break

                if batch:
                    try:
                        asyncio.run(self._process_batch(batch))
                        internal_logger.info(f"Processed batch of {len(batch)} logs")
                    except Exception as e:
                        internal_logger.error(f"Batch processing error: {e}")
            except Exception as e:
                internal_logger.error(f"Processor worker error: {e}")

    def _consumer_worker(self):
        """Worker method to consume messages from RabbitMQ"""
        params = pika.URLParameters(self.rabbitmq_url)
        params.heartbeat = 600
        params.blocked_connection_timeout = 300
        connection = pika.BlockingConnection(params)
        try:
            channel = connection.channel()
            channel.exchange_declare(
                exchange="logs_exchange", exchange_type="direct", durable=True
            )
            if self.service_names:
                for service_name in self.service_names:
                    for level in ["info", "error", "warning", "debug", "critical"]:
                        queue_name = f"{service_name}_{level}_logs"
                        QueueConfig.declare_queue(channel, queue_name)
                        channel.queue_bind(
                            exchange="logs_exchange",
                            queue=queue_name,
                            routing_key=f"{service_name}.{level}",
                        )
            else:
                queue_name = "all_logs"
                QueueConfig.declare_queue(channel, queue_name)
                channel.queue_bind(
                    exchange="logs_exchange", queue=queue_name, routing_key="#"
                )

            def on_message(ch, method, properties, body):
                try:
                    log_data = json.loads(body)
                    try:
                        try:
                            self.message_queue.put(
                                log_data, timeout=30
                            )  # 30 second timeout
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                        except queue.Full:
                            internal_logger.warning(
                                "Message queue full, rejecting message for requeue"
                            )
                            ch.basic_nack(
                                delivery_tag=method.delivery_tag, requeue=True
                            )
                            time.sleep(0.1)
                    except Exception as queue_error:
                        internal_logger.error(f"Error queueing message: {queue_error}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                except json.JSONDecodeError as e:
                    internal_logger.error(f"Invalid JSON in message, discarding: {e}")
                    ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                except Exception as e:
                    internal_logger.error(f"Unexpected error processing message: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            for queue_name in self.queues:
                channel.basic_consume(
                    queue=queue_name, on_message_callback=on_message, auto_ack=False
                )
            internal_logger.info("Starting message consumption...")
            channel.start_consuming()

        except Exception as e:
            internal_logger.error(f"Consumer worker error: {e}")
        finally:
            if connection and not connection.is_closed:
                connection.close()

    def start(self):
        """Start the scaled consumer"""
        self.stop_event.clear()
        self.consumer_thread = threading.Thread(
            target=self._consumer_worker, daemon=True
        )
        self.consumer_thread.start()
        self.processor_thread = threading.Thread(
            target=self._processor_worker, daemon=True
        )
        self.processor_thread.start()
        internal_logger.info("Starting Consumer: ")

    def stop(self):
        """Gracefully stop the consumer"""
        self.stop_event.set()
        if self.consumer_thread:
            internal_logger.info("Stopping consumer thread...")
            self.consumer_thread.join(timeout=5)

        if self.processor_thread:
            internal_logger.info("Stopping processor thread...")
            self.processor_thread.join(timeout=5)

        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
            except Exception as e:
                internal_logger.error(f"Error closing connection: {e}")

    def __del__(self):
        """Destructor to ensure clean shutdown"""
        try:
            self.stop()
        except Exception as e:
            internal_logger.error(f"Error in destructor: {e}")


def start_consumer(service_names: list) -> None:
    consumer = Consumer(service_names=service_names)
    try:
        consumer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        internal_logger.info("Shutting down consumer...")
        consumer.stop()
    except Exception as e:
        internal_logger.error(f"Consumer error: {str(e)}")
        internal_logger.info("Restarting consumer in 5 seconds...")
        time.sleep(5)
