<h1 align="center">Loghive - Distributed Logger 🚀</h1> 

A robust, scalable Python logging library that enables distributed log collection with advanced connection management,
automatic reconnection, and thread-safe logging capabilities. 🌟

---

## Core Components 🛠️

### 1. LoggerClient 📝

- 🧵 **Thread-safe logging client with automatic reconnection**
- ⏳ **Exponential backoff retry mechanism**
- 🩺 **Connection health monitoring**
- 📨 **Durable message delivery**

### 2. Consumer 🛡️

- ⚙️ **Scalable message consumption**
- 📦 **Batch processing capabilities**
- 🔄 **Error handling and recovery**
- 💻 **Multi-threaded architecture**

---

## Features ✨

### Logger Client Features 🔧

- **Thread-Safe Operations**:
    - 🔒 Thread-safe logging with mutex locks
    - 👥 Concurrent access handling
    - ✅ Safe connection management
- **Robust Connection Management**:
    - 🔄 Automatic reconnection with exponential backoff
    - 🩺 Connection health monitoring
    - ⏱️ Configurable heartbeat (600 seconds)
    - ⏳ Connection timeout protection (300 seconds)
    - 🕒 Socket timeout (10 seconds)
- **Reliable Message Delivery**:
    - 📜 Durable message queues
    - 💾 Message persistence
    - ✅ Delivery confirmation
    - 🔁 Automatic retry on failure
- **Flexible Log Routing**:
    - 🛠️ Service-specific routing
    - 📊 Log level-based queues
    - 🧩 Dynamic queue declaration
    - 🔗 Direct exchange support

### Consumer Features 🛡️

- **Advanced Message Queue Management**:
    - ⏳ Configurable message TTL (7 days default) - Messages automatically expire after a set time period to prevent
      queue
      overflow.
    - 📏 Maximum queue length limits - Set hard limits on queue size to protect system resources and maintain
      performance.
    - 💪 Backpressure handling - Automatically manages message flow when the system is under heavy load to prevent
      crashes.
- **Scalable Processing**:
    - 🧵 Multi-threaded message processing - Parallel processing of messages across multiple threads for improved
      throughput.
    - 📦 Batch processing support - Groups messages into batches for efficient bulk processing and reduced database load.
    - ⚙️ Configurable worker pool - Adjust the number of worker threads based on your system's capacity and
      requirements.
- **Error Recovery**:
    - 📥 Failure backoff queue - Stores failed messages separately for retry with exponential backoff to prevent system
      overload.
    - 🔁 Automatic retry mechanism - Intelligently retries failed operations with configurable attempts and delays.
    - ✅ JSON validation - Ensures message integrity by validating JSON structure before processing to prevent data
      corruption.

---

## Installation 🛠️

```bash
pip install loghive
```

---

## Usage 📖

### Configuration file setup

Create a config.env file for the service to fetch the connection parameters for rabbitmq, rabbitmq and email connection

```dotenv
# Basic Configurations
LOG_LEVEL=DEBUG

# Database Configurations
POSTGRES_DB_HOST=localhost
POSTGRES_DB_USER=***
POSTGRES_DB_NAME=***
POSTGRES_DB_PASSWORD=***
POSTGRES_DB_PORT=***

# RabbitMQ & Consumer Configurations
QUEUE_HOST=localhost
QUEUE_USER=***
QUEUE_PASSWORD=***
QUEUE_PORT=***
QUEUE_MAX_SIZE=10000000

# Consumer
CONSUMER_BATCH_SIZE=1000

# Monitoring
ENABLE_EMAIL_MONITORING=False
EMAIL_HOST=***
EMAIL_PORT=***
EMAIL_SENDER_EMAIL=***
EMAIL_SENDER_PASSWORD=***

```

### Logger Client Setup 📝

```python
from loghive.logger.rabbitmqlogger import LoggerClient

# Initialize the logger
logger = LoggerClient(
    service_name="my-service",
    rabbitmq_url="amqp://localhost:5672/"
)

# Log messages with different levels
logger.log("INFO", "User logged in", {"user_id": "123"})
logger.log("ERROR", "Database connection failed", {"retry_count": 3})
logger.log("WARNING", "High memory usage", {"usage_percent": 85})
```

### Consumer

```python
from loghive.consumer.rabbitmqconsumer import start_consumer
from loghive.main.settings import internal_logger

try:
    start_consumer(["flask_service"])  # replace with your service names
except Exception as e:
    internal_logger.error(f"Error faced while starting consumer: {e}")
```

The internal_logger can be imported from ```loghive.main.settings```, this will be behave like a normal logger and will
not be publishing the message to rabbitmq.

### Message Structure 📦

```json
{
  "service": "service_name",
  "level": "INFO",
  "message": "Log message",
  "information": {
    "# Additional context as dictionary"
  },
  "timestamp": "2024-12-27 10:30:45"
}
```

### Connection Configuration ⚙️

```python
connection_params = {
    "heartbeat": 600,  # Heartbeat interval in seconds
    "blocked_connection_timeout": 300,  # Connection timeout in seconds
    "socket_timeout": 10,  # Socket timeout in seconds
}
```

### Queue Settings 📜

```python
QUEUE_ARGUMENTS = {
    "x-message-ttl": 604800000,  # 7 days in milliseconds
    "x-max-length": 1000000,  # Maximum queue size
}
```

---

## Architecture 🏗️

### Logger Client Architecture 🖇️

```
+----------------+     +------------------+     +----------------+
|  Application   |     |   LoggerClient   |     |   RabbitMQ    |
|    Code        | --> | - Thread Safety  | --> |   Exchange    |
|                |     | - Auto Reconnect |     |   (Direct)    |
+----------------+     | - Retry Logic    |     +----------------+
                      +------------------+
```

### Message Flow 🔄

```
1. Application generates log
   ↓
2. LoggerClient validates and formats message
   ↓
3. Thread-safe connection check
   ↓
4. Publish with retry mechanism
   ↓
5. RabbitMQ confirms delivery
   ↓
6. Consumer processes message
```

---

## Error Handling ⚠️

### Logger Client Error Recovery 🛡️

1. 🔄 Connection failures trigger automatic reconnection
2. ⏳ Exponential backoff between retry attempts (1-30 seconds)
3. 🚫 Maximum of 3 retry attempts per operation
4. 🩺 Separate monitoring thread for connection health
5. 🔒 Thread-safe operation handling

### Message Delivery Guarantees ✅

- 📜 Durable queues and exchanges
- 💾 Persistent messages (delivery_mode=2)
- ✅ Message acknowledgment
- 🛠️ Automatic queue declaration
- 🔄 Connection recovery

---

## Best Practices ✅

1. **Initialization**:

```python
logger = LoggerClient(
    service_name="unique-service-name",
    rabbitmq_url="amqp://username:password@host:port/vhost"
)
```

2. **Graceful Shutdown**:

```python
# Always close the logger when done
logger.close()
```

3. **Error Handling**:

```python
try:
    # Your application code
    logger.log("INFO", "Operation successful")
except Exception as e:
    logger.log("ERROR", "Operation failed", {"error": str(e)})
```

4. **Structured Logging**:

```python
logger.log(
    "INFO",
    "User action completed",
    {
        "user_id": "123",
        "action": "checkout",
        "duration_ms": 150
    }
)
```

---

## Monitoring 📊

The logger provides built-in monitoring for:

- 🩺 Connection status
- ✅ Message delivery success/failure
- 🔁 Retry attempts
- 📜 Queue health
- 🧵 Thread status

---

## Performance Considerations ⚡

- 🧵 Thread-safe operations may impact throughput
- 🩺 Connection monitoring adds minimal overhead
- 🔁 Retry mechanisms prevent message loss
- ⏱️ Heartbeat monitoring ensures connection health
- 🚫 Socket timeouts prevent hanging operations

---

## Contributing 🤝

See our [Contributing Guide](CONTRIBUTING.md) for details on how to contribute to this project.

---

## License 📜

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support 💬

For issues and help:

1. 📖 Check the [documentation](docs/)
2. 🔍 Review existing [issues](issues/)
3. 📝 Create a new issue with detailed reproduction steps  