import json
import os

USER_DB_PATH = "users.json"

def load_users():
    if os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, "r") as f:
            return json.load(f)
    else:
        return {"users": {}}