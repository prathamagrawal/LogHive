import os
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from loghive.logger.rabbitmqlogger import LoggerClient

app = FastAPI()
logger = LoggerClient("fastapi_service")

users = []


@app.get("/")
def home():
    logger.log("INFO", "Home page accessed")
    return {"message": "Welcome to the FastAPI Application"}


@app.get("/users")
def get_users():
    try:
        logger.log(
            "WARNING", "Users retrieved successfully", {"user_count": len(users)}
        )
        return users
    except Exception as e:
        logger.log("ERROR", "Failed to retrieve users", {"error": str(e)})
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/error")
def get_error():
    logger.log("WARNING", "Users retrieved successfully", {"user_count": len(users)})
    try:
        print(10 / 0)  # Manually triggering error for traceback logs
    except ZeroDivisionError as e:
        traceback_info = traceback.format_exc()
        logger.log(
            "ERROR",
            f"Traceback for error: {str(e)}",
            information={"error": traceback_info},
        )
        logger.log("ERROR", message=str(e), information={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users")
def create_user(request: Request):
    global users
    try:
        user_data = request.json()
        logger.log("INFO", "User creation attempt", {"user_details": user_data})
        user_data["id"] = len(users) + 1
        users.append(user_data)  # Add the user to the global list
        logger.log("INFO", "User created successfully", {"user_id": user_data["id"]})
        return JSONResponse(content=user_data, status_code=201)
    except Exception as e:
        logger.log(
            "ERROR", "User creation failed", {"error": str(e), "user_data": user_data}
        )
        raise HTTPException(status_code=400, detail="User creation failed")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
