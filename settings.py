import json
import os
import sys

class Settings:
    def __init__(self):
        self._system_data = self.load_system_constants()
    
    def _get_resource_path(self, relative_path):
        try: base_path = sys._MEIPASS
        except AttributeError: 
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = current_dir
        return os.path.join(base_path, relative_path)
    
    def load_system_constants(self):
        try:
            file_path = self._get_resource_path("system_constants.json")
            with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e:
            print(f"Failed to load system_constants.json: {e}")
            return {}
    
    def get(self, key, default=None):
        for section in self._system_data.values():
            if isinstance(section, dict) and key in section: return section[key]
        return default
    
    def set(self, key, value):
        # Already in _system_data
        for section_name, section_data in self._system_data.items():
            if key in section_data:
                self._system_data[section_name][key] = value
                return True
        # If key not found, add to the 'others' section
        if 'others' in self._system_data:
            self._system_data['others'][key] = value
            return True
        return False
    
    def get_section(self, section_name):
        return self._system_data.get(section_name, {})
    
    def update_section(self, section_name, data):
        try:
            self._system_data[section_name] = data
            return True
        except Exception: return False

_settings = Settings()
def get(key, default= None): return _settings.get(key, default)
def set(key, value): return _settings.set(key, value)
def get_section(section_name): return _settings.get_section(section_name)
def update_section(section_name, data): return _settings.update_section(section_name, data)
def get_resource_path(relative_path): return _settings._get_resource_path(relative_path)
