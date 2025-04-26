import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Ошибка при загрузке конфигурации: {e}")
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка при сохранении конфигурации: {e}")

def clear_account_data():
    config = load_config()
    if "username" in config:
        del config["username"]
    if "refresh_token" in config:
        del config["refresh_token"]
    save_config(config)

def update_config(new_data):
    config = load_config()
    config.update(new_data)
    save_config(config)
