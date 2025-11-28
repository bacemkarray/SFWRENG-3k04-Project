import json

from parameters import PARAMETER_RULES, MODE_PARAMETER_LAYOUT

def load_users():
    with open("data/users.json", "r") as f:
        return json.load(f)
        

def save_users(data):
    with open("data/users.json", "w") as f:
        json.dump(data, f, indent=4)


def register_user(username, password):
    data = load_users()
    # Can't register multiple users with same username
    if len(data) == 10:
        return False
    # Can't reguster empty username or password
    if username == "" or password == "":
        return False
    for user in data:
        if user["username"] == username:
            return False

    data.append({
        "username": username, 
        "password": password,
        "parameters": generate_default_profile(),
        })
    save_users(data)    
    return True

# check that username and password are the same
def check_login(username, password):
    data = load_users()
    for user in data:
        if user["username"] == username and user["password"] == password:
            return True
    return False


# populate a profile with default values
def generate_default_profile():
    profile = {}
    for mode, param_list in MODE_PARAMETER_LAYOUT.items():
        profile[mode] = {}
        for param_name in param_list:
            profile[mode][param_name] = PARAMETER_RULES[param_name][0]
    return profile


def get_user(username):
    data = load_users()
    for user in data:
        if user["username"] == username:
            return user
    return None


def save_user_profile(username, params):
    data = load_users()
    for user in data:
        if user["username"] == username:
            user["parameters"] = params
            save_users(data)
            return True
    return False


def get_user_profile(username):
    user = get_user(username)
    if user is None:
        return None
    return user.get("parameters", None)


