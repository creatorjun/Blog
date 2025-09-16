# utils/settings_manager.py
import os
import json
from cryptography.fernet import Fernet
from typing import Dict, Any

class EncryptedSettingsManager:
    """암호화된 설정 관리자 (Gmail 설정 제거됨)"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".blog_generator")
        self.settings_file = os.path.join(self.config_dir, "settings.enc")
        self.key_file = os.path.join(self.config_dir, "key.key")
        
        # 🔧 기본 설정값 (Gmail 관련 완전 제거)
        self.default_settings = {
            'naver_client_id': '',
            'naver_client_secret': '',
            'google_api_key': '',
            
            # 이미지 API 키
            'unsplash_access_key': '',
            'pixabay_api_key': '',
            
            # 앱 설정
            'last_category_index': 0,
            'last_keyword': '',
            'window_x': 100,
            'window_y': 100,
            'window_width': 1200,
            'window_height': 800
        }
        
        self.settings = self.default_settings.copy()
        
        # 디렉토리 생성
        os.makedirs(self.config_dir, exist_ok=True)
        
        try:
            # 암호화 키 생성 또는 로드
            self.cipher = self._get_or_create_cipher()
            # 설정 로드
            self.load_settings()
        except Exception as e:
            print(f"⚠️ 암호화 초기화 실패, 기본 설정 사용: {e}")
    
    def _get_or_create_cipher(self):
        """암호화 키 생성 또는 로드"""
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
        """설정 로드 (Gmail 설정 호환성 처리)"""
        try:
            if self.cipher and os.path.exists(self.settings_file):
                with open(self.settings_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self.cipher.decrypt(encrypted_data)
                loaded_settings = json.loads(decrypted_data.decode())
                
                # 🔧 Gmail 관련 설정 제거 (기존 설정 파일과 호환성)
                if 'gmail' in loaded_settings:
                    del loaded_settings['gmail']
                    print("📧 Gmail 설정 제거됨")
                    
                if 'gmail_password' in loaded_settings:
                    del loaded_settings['gmail_password'] 
                    print("🔐 Gmail 패스워드 설정 제거됨")
                
                self.settings.update(loaded_settings)
                print("✅ 설정 파일 로드 완료 (Gmail 설정 제거 적용)")
            else:
                print("📄 새 설정 파일 생성")
                self.save_settings()
                
        except Exception as e:
            print(f"⚠️ 설정 로드 실패, 기본값 사용: {e}")
            self.settings = self.default_settings.copy()
    
    def save_settings(self):
        """설정 저장"""
        try:
            if self.cipher:
                # Gmail 관련 키가 혹시 있다면 제거
                clean_settings = {k: v for k, v in self.settings.items() 
                                if k not in ['gmail', 'gmail_password']}
                
                json_data = json.dumps(clean_settings, ensure_ascii=False, indent=2)
                encrypted_data = self.cipher.encrypt(json_data.encode())
                
                with open(self.settings_file, 'wb') as f:
                    f.write(encrypted_data)
                
                print("💾 설정 저장 완료 (Gmail 설정 제외)")
            else:
                print("❌ 암호화 키가 없어 저장 실패")
                
        except Exception as e:
            print(f"❌ 설정 저장 실패: {e}")
    
    def get_window_geometry(self) -> Dict[str, int]:
        """윈도우 위치 및 크기 반환"""
        return {
            'x': self.settings.get('window_x', 100),
            'y': self.settings.get('window_y', 100),
            'width': self.settings.get('window_width', 1200),
            'height': self.settings.get('window_height', 800)
        }
    
    def set_window_geometry(self, geometry_dict: Dict[str, int]):
        """윈도우 위치 및 크기 저장"""
        self.settings['window_x'] = geometry_dict.get('x', 100)
        self.settings['window_y'] = geometry_dict.get('y', 100)
        self.settings['window_width'] = geometry_dict.get('width', 1200)
        self.settings['window_height'] = geometry_dict.get('height', 800)
        self.save_settings()
    
    def get_last_search_settings(self) -> Dict[str, Any]:
        """마지막 검색 설정 반환"""
        return {
            'category_index': self.settings.get('last_category_index', 0),
            'keyword': self.settings.get('last_keyword', '')
        }
    
    def set_last_search_settings(self, category_index: int, keyword: str):
        """마지막 검색 설정 저장"""
        self.settings['last_category_index'] = category_index
        self.settings['last_keyword'] = keyword
        self.save_settings()
    
    def get_api_settings(self) -> Dict[str, str]:
        """API 설정 반환 (Gmail 제외)"""
        return {
            'naver_client_id': self.settings.get('naver_client_id', ''),
            'naver_client_secret': self.settings.get('naver_client_secret', ''),
            'google_api_key': self.settings.get('google_api_key', ''),
            'unsplash_access_key': self.settings.get('unsplash_access_key', ''),
            'pixabay_api_key': self.settings.get('pixabay_api_key', '')
        }
    
    def set_api_settings(self, api_settings: Dict[str, str]):
        """API 설정 저장 (Gmail 관련 키 무시)"""
        # Gmail 관련 키는 무시
        filtered_settings = {k: v for k, v in api_settings.items() 
                           if k not in ['gmail', 'gmail_password']}
        
        for key, value in filtered_settings.items():
            if key in self.default_settings:
                self.settings[key] = value
        
        self.save_settings()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """모든 설정 반환 (Gmail 제외)"""
        # Gmail 관련 키 제외하고 반환
        return {k: v for k, v in self.settings.items() 
                if k not in ['gmail', 'gmail_password']}
    
    def set_all_settings(self, new_settings: Dict[str, Any]):
        """모든 설정 저장 (Gmail 관련 키 무시)"""
        # Gmail 관련 키는 무시
        filtered_settings = {k: v for k, v in new_settings.items() 
                           if k not in ['gmail', 'gmail_password']}
        
        for key, value in filtered_settings.items():
            if key in self.default_settings:
                self.settings[key] = value
        
        self.save_settings()
    
    def get_setting(self, key: str, default=None):
        """개별 설정 값 반환"""
        if key in ['gmail', 'gmail_password']:
            print(f"⚠️ Gmail 설정 '{key}'는 더 이상 지원되지 않습니다.")
            return default
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """개별 설정 값 저장"""
        if key in ['gmail', 'gmail_password']:
            print(f"⚠️ Gmail 설정 '{key}'는 더 이상 지원되지 않습니다.")
            return
            
        if key in self.default_settings:
            self.settings[key] = value
            self.save_settings()
    
    def reset_to_defaults(self):
        """설정을 기본값으로 초기화 (Gmail 제외)"""
        self.settings = self.default_settings.copy()
        self.save_settings()
        print("🔄 설정이 기본값으로 초기화되었습니다 (Gmail 설정 제외).")
    
    def cleanup_gmail_settings(self):
        """기존 Gmail 설정 정리 (일회성 실행용)"""
        removed = False
        if 'gmail' in self.settings:
            del self.settings['gmail']
            removed = True
        if 'gmail_password' in self.settings:
            del self.settings['gmail_password']
            removed = True
            
        if removed:
            self.save_settings()
            print("🧹 Gmail 설정이 완전히 제거되었습니다.")

# 기존 코드와의 호환성을 위한 별칭
SettingsManager = EncryptedSettingsManager

# 🔧 기본 설정값 업데이트 (Gmail 제거)
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