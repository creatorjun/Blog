import os
import requests
from urllib.parse import urlparse
from datetime import datetime

class ImageDownloader:
    def __init__(self, save_dir='img'):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def download_image(self, url, filename_prefix="image") -> str:
        try:
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            if '.' in original_filename:
                ext = os.path.splitext(original_filename)[1]
            else:
                ext = '.jpg'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}{ext}"
            save_path = os.path.join(self.save_dir, filename)
            counter = 1
            while os.path.exists(save_path):
                filename = f"{filename_prefix}_{timestamp}_{counter}{ext}"
                save_path = os.path.join(self.save_dir, filename)
                counter += 1
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path
        except requests.exceptions.RequestException as e:
            print(f"이미지 다운로드 실패 (네트워크): {e}")
            return ''
        except Exception as e:
            print(f"이미지 다운로드 실패: {e}")
            return ''

    def get_file_url(self, local_path):
        if not local_path or not os.path.exists(local_path):
            return ''
        abs_path = os.path.abspath(local_path)
        file_url = f"file:///{abs_path.replace(os.sep, '/')}"
        return file_url