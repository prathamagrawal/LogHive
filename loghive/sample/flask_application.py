from flask import Flask, jsonify, request
from loghive.logger.rabbitmqlogger import LoggerClient
import os
import traceback

app = Flask(__name__)
logger = LoggerClient("flask_service")

users = []


@app.route("/")
def home():
    logger.log("INFO", "Home page accessed")
    return jsonify({"message": "Welcome to the Flask Application"})


@app.route("/users", methods=["GET"])
def get_users():
    try:
        logger.log(
            "WARNING", "Users retrieved successfully", {"user_count": len(users)}
        )
        return jsonify(users)
    except Exception as e:
        logger.log("ERROR", "Failed to retrieve users", {"error": str(e)})
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/error", methods=["GET"])
def get_error():
    logger.log("WARNING", "Users retrieved successfully", {"user_count": len(users)})
    try:
        print(10 / 0)  ## Manually triggering error for traceback logs
        return jsonify(users)
    except ZeroDivisionError as e:
        logger.log(
            "ERROR",
            f"Traceback for error: {str(e)}",
            information={"error": traceback.format_exc()},
        )
        logger.log("ERROR", message=str(e), information={"error": str(e)})
        return jsonify({"error": str(e)})


@app.route("/users", methods=["POST"])
def create_user():
    global users
    global user_data

    try:
        user_data = request.json
        logger.log("INFO", "User creation attempt", {"user_details": user_data})
        user_data["id"] = len(users) + 1
        users.append(user_data)  # Add the user to the global list
        logger.log("INFO", "User created successfully", {"user_id": user_data["id"]})
        return jsonify(user_data), 201
    except Exception as e:
        logger.log(
            "ERROR", "User creation failed", {"error": str(e), "user_data": user_data}
        )
        return jsonify({"error": "User creation failed"}), 400


def main():
    port = int(os.environ.get("PORT", 7000))
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()
