from flask import Flask, jsonify, request
from loggerclient.pythonlogger import LoggerClient
import os

# Initialize Flask app
app = Flask(__name__)

# Initialize Logger
logger = LoggerClient("flask_service")

users = []


@app.route("/")
def home():
    logger.log("INFO", "Home page accessed")
    return jsonify({"message": "Welcome to the Flask Application"})


@app.route("/users", methods=["GET"])
def get_users():
    try:
        print("1234564321")
        logger.log("WARNING", "Users retrieved successfully", {"user_count": len(users)})
        return jsonify(users)
    except Exception as e:
        logger.log("ERROR", "Failed to retrieve users", {"error": str(e)})
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/users", methods=["POST"])
def create_user():
    global users  # Declare users as global to modify it
    global user_data  # Remove this global declaration

    try:
        user_data = request.json
        print("123")

        # Remove global reference
        logger.log("INFO", "User creation attempt", {"user_details": user_data})

        # Simulating user creation
        user_data["id"] = len(users) + 1
        users.append(user_data)  # Add the user to the global list

        logger.log("INFO", "User created successfully", {"user_id": user_data["id"]})
        return jsonify(user_data), 201
    except Exception as e:
        logger.log(
            "ERROR", "User creation failed", {"error": str(e), "user_data": user_data}
        )
        return jsonify({"error": "User creation failed"}), 400


# Global error handler
@app.errorhandler(Exception)
def handle_error(e):
    logger.log(
        "CRITICAL", "Unhandled exception", {"error": str(e), "type": type(e).__name__}
    )
    return jsonify({"error": "Internal Server Error"}), 500


def main():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()
