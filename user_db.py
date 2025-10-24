import json


def load_users():
    with open("data/users.json", "r") as f:
        return json.load(f)
        

def save_users(data):
    with open("data/users.json", "w") as f:
        json.dump(data, f, indent=4)


def register_user(username, password):
    data = load_users()
    # Can't register multiple users with same username
    for user in data:
        if user["username"] == username:
            return False

    data.append({
        "username": username, 
        "password": password
        })
    save_users(data)    
    return True


def check_login(username, password):
    data = load_users()
    for user in data:
        if user["username"] == username and user["password"] == password:
            return True
    return False

register_user("Bacem", "1234")
