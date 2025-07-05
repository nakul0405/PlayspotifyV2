import json
import os

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def save_token(user_id, token_data):
    data = load_json("tokens.json")
    data[str(user_id)] = token_data
    save_json("tokens.json", data)

def get_token(user_id):
    return load_json("tokens.json").get(str(user_id))

def delete_token(user_id):
    data = load_json("tokens.json")
    data.pop(str(user_id), None)
    save_json("tokens.json", data)

def save_cookie(user_id, cookie):
    data = load_json("cookies.json")
    data[str(user_id)] = {"sp_dc": cookie}
    save_json("cookies.json", data)

def get_cookie(user_id):
    return load_json("cookies.json").get(str(user_id), {}).get("sp_dc")
