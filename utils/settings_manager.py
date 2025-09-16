import os
import json
from cryptography.fernet import Fernet
from typing import Dict, Any

class EncryptedSettingsManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".blog_generator")
        self.settings_file = os.path.join(self.config_dir, "settings.enc")
        self.key_file = os.path.join(self.config_dir, "key.key")
        self.default_settings = {
            'naver_client_id': '',
            'naver_client_secret': '',
            'google_api_key': '',
            'unsplash_access_key': '',
            'pixabay_api_key': '',
            'last_category_index': 0,
            'last_keyword': '',
            'window_x': 100,
            'window_y': 100,
            'window_width': 1200,
            'window_height': 800
        }
        self.settings = self.default_settings.copy()
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            self.cipher = self._get_or_create_cipher()
            self.load_settings()
        except Exception as e:
            print(f"암호화 초기화 실패, 기본 설정 사용: {e}")

    def _get_or_create_cipher(self):
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
            return Fernet(key)
        except Exception as e:
            print(f"암호화 키 생성 실패: {e}")
            return None

    def load_settings(self):
        try:
            if self.cipher and os.path.exists(self.settings_file):
                with open(self.settings_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                loaded_settings = json.loads(decrypted_data.decode())
                if 'gmail' in loaded_settings:
                    del loaded_settings['gmail']
                if 'gmail_password' in loaded_settings:
                    del loaded_settings['gmail_password']
                self.settings.update(loaded_settings)
            else:
                self.save_settings()
        except Exception as e:
            print(f"설정 로드 실패, 기본값 사용: {e}")
            self.settings = self.default_settings.copy()

    def save_settings(self):
        try:
            if self.cipher:
                clean_settings = {k: v for k, v in self.settings.items()
                                if k not in ['gmail', 'gmail_password']}
                json_data = json.dumps(clean_settings, ensure_ascii=False, indent=2)
                encrypted_data = self.cipher.encrypt(json_data.encode())
                with open(self.settings_file, 'wb') as f:
                    f.write(encrypted_data)
            else:
                print("암호화 키가 없어 저장 실패")
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def get_window_geometry(self) -> Dict[str, int]:
        return {
            'x': self.settings.get('window_x', 100),
            'y': self.settings.get('window_y', 100),
            'width': self.settings.get('window_width', 1200),
            'height': self.settings.get('window_height', 800)
        }

    def set_window_geometry(self, geometry_dict: Dict[str, int]):
        self.settings['window_x'] = geometry_dict.get('x', 100)
        self.settings['window_y'] = geometry_dict.get('y', 100)
        self.settings['window_width'] = geometry_dict.get('width', 1200)
        self.settings['window_height'] = geometry_dict.get('height', 800)
        self.save_settings()

    def get_last_search_settings(self) -> Dict[str, Any]:
        return {
            'category_index': self.settings.get('last_category_index', 0),
            'keyword': self.settings.get('last_keyword', '')
        }

    def set_last_search_settings(self, category_index: int, keyword: str):
        self.settings['last_category_index'] = category_index
        self.settings['last_keyword'] = keyword
        self.save_settings()

    def get_api_settings(self) -> Dict[str, str]:
        return {
            'naver_client_id': self.settings.get('naver_client_id', ''),
            'naver_client_secret': self.settings.get('naver_client_secret', ''),
            'google_api_key': self.settings.get('google_api_key', ''),
            'unsplash_access_key': self.settings.get('unsplash_access_key', ''),
            'pixabay_api_key': self.settings.get('pixabay_api_key', '')
        }

    def set_api_settings(self, api_settings: Dict[str, str]):
        filtered_settings = {k: v for k, v in api_settings.items()
                           if k not in ['gmail', 'gmail_password']}
        for key, value in filtered_settings.items():
            if key in self.default_settings:
                self.settings[key] = value
        self.save_settings()

    def get_all_settings(self) -> Dict[str, Any]:
        return {k: v for k, v in self.settings.items()
                if k not in ['gmail', 'gmail_password']}

    def set_all_settings(self, new_settings: Dict[str, Any]):
        filtered_settings = {k: v for k, v in new_settings.items()
                           if k not in ['gmail', 'gmail_password']}
        for key, value in filtered_settings.items():
            if key in self.default_settings:
                self.settings[key] = value
        self.save_settings()

    def get_setting(self, key: str, default=None):
        if key in ['gmail', 'gmail_password']:
            return default
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any):
        if key in ['gmail', 'gmail_password']:
            return
        if key in self.default_settings:
            self.settings[key] = value
            self.save_settings()

    def reset_to_defaults(self):
        self.settings = self.default_settings.copy()
        self.save_settings()

    def cleanup_gmail_settings(self):
        removed = False
        if 'gmail' in self.settings:
            del self.settings['gmail']
            removed = True
        if 'gmail_password' in self.settings:
            del self.settings['gmail_password']
            removed = True
        if removed:
            self.save_settings()

SettingsManager = EncryptedSettingsManager

DEFAULT_SETTINGS = {
    'naver_client_id': '',
    'naver_client_secret': '',
    'google_api_key': '',
    'unsplash_access_key': '',
    'pixabay_api_key': '',
    'last_category_index': 0,
    'last_keyword': '',
    'window_x': 100,
    'window_y': 100,
    'window_width': 1200,
    'window_height': 800
}