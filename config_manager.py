import json
import os

class ConfigManager:
    DEFAULT_CONFIG = {
        "font_family": "Arial",
        "font_size": 24,
        "text_color": "#FFFFFF",
        "window_x": 100,
        "window_y": 100,
        "window_height": 100,
        "alignment": "Custom",
        "locked": False,
        "click_through": False,
        "provider": "Auto"
    }
    
    CONFIG_FILE = "config.json"

    def __init__(self):
        self.config = self.load_config()
        self.callbacks = []

    def load_config(self):
        if not os.path.exists(self.CONFIG_FILE):
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                # Merge with defaults in case of missing keys
                config = self.DEFAULT_CONFIG.copy()
                config.update(saved_config)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key):
        return self.config.get(key, self.DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        if self.config.get(key) != value:
            self.config[key] = value
            self.save_config()
            self.notify_listeners()

    def add_listener(self, callback):
        self.callbacks.append(callback)

    def notify_listeners(self):
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in config listener: {e}")
