# utils/image_downloader.py
import os
import requests
from urllib.parse import urlparse
from datetime import datetime

class ImageDownloader:
    """URL로부터 이미지 다운로드 및 로컬 저장 관리"""
    
    def __init__(self, save_dir='img'):
        self.save_dir = save_dir
        # img 폴더 생성
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            print(f"📁 이미지 저장 폴더 생성: {save_dir}")
    
    def download_image(self, url, filename_prefix="image") -> str:
        """URL에서 이미지 다운로드하고 로컬 경로 반환"""
        try:
            print(f"🔄 이미지 다운로드 중: {url[:50]}...")
            
            # URL에서 파일명 추출
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            
            # 파일 확장자 확인
            if '.' in original_filename:
                ext = os.path.splitext(original_filename)[1]
            else:
                ext = '.jpg'  # 기본 확장자
            
            # 고유한 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}{ext}"
            save_path = os.path.join(self.save_dir, filename)
            
            # 중복 방지
            counter = 1
            while os.path.exists(save_path):
                filename = f"{filename_prefix}_{timestamp}_{counter}{ext}"
                save_path = os.path.join(self.save_dir, filename)
                counter += 1
            
            # 이미지 다운로드
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()
            
            # 파일 저장
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ 이미지 다운로드 완료: {filename}")
            return save_path
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 이미지 다운로드 실패 (네트워크): {e}")
            return ''
        except Exception as e:
            print(f"❌ 이미지 다운로드 실패: {e}")
            return ''
    
    def get_file_url(self, local_path):
        """로컬 파일 경로를 파일 URL로 변환"""
        if not local_path or not os.path.exists(local_path):
            return ''
        
        # 절대 경로로 변환
        abs_path = os.path.abspath(local_path)
        # 파일 URL 형식으로 변환 (Windows 호환)
        file_url = f"file:///{abs_path.replace(os.sep, '/')}"
        return file_url
