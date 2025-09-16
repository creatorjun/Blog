# ai_modules/image_searcher.py
import requests
from typing import List, Dict

class ImageSearcher:
    """설정 탭 연동 이미지 검색 API 클래스"""
    
    def __init__(self, settings_manager):
        """settings_manager에서 API 키 가져오기"""
        api_settings = settings_manager.get_api_settings()
        self.unsplash_access_key = api_settings.get('unsplash_access_key', '').strip()
        self.pixabay_key = api_settings.get('pixabay_api_key', '').strip()
        
        self.unsplash_url = "https://api.unsplash.com/search/photos"
        self.pixabay_url = "https://pixabay.com/api/"
        
        print(f"🖼️ 이미지 검색 초기화: Unsplash {'✅' if self.unsplash_access_key else '❌'}, Pixabay {'✅' if self.pixabay_key else '❌'}")
    
    def search_images(self, keywords: List[str], per_keyword: int = 1) -> Dict[str, List[Dict]]:
        """키워드별 이미지 검색"""
        results = {}
        
        if not keywords:
            print("⚠️ 이미지 검색 키워드가 없습니다.")
            return results
        
        for i, keyword in enumerate(keywords[:2], 1):  # 최대 2개 키워드
            try:
                images = []
                
                # Unsplash 우선 시도
                if self.unsplash_access_key:
                    images = self._search_unsplash(keyword, per_keyword)
                
                # Unsplash 실패 시 Pixabay 시도
                if not images and self.pixabay_key:
                    images = self._search_pixabay(keyword, per_keyword)
                
                results[f"이미지_{i}"] = images
                print(f"✅ '{keyword}' 검색 완료: {len(images)}개 이미지")
                
            except Exception as e:
                print(f"❌ '{keyword}' 검색 실패: {e}")
                results[f"이미지_{i}"] = []
        
        return results
    
    def _search_unsplash(self, keyword: str, count: int) -> List[Dict]:
        """Unsplash API로 이미지 검색"""
        if not self.unsplash_access_key:
            return []
            
        try:
            params = {
                'query': keyword,
                'per_page': count,
                'orientation': 'landscape',
                'content_filter': 'high'
            }
            
            headers = {
                'Authorization': f'Client-ID {self.unsplash_access_key}'
            }
            
            response = requests.get(self.unsplash_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                images = []
                for photo in data.get('results', []):
                    images.append({
                        'url': photo['urls']['regular'],
                        'thumb_url': photo['urls']['thumb'],
                        'description': photo.get('alt_description', keyword),
                        'photographer': photo['user']['name'],
                        'source': 'Unsplash',
                        'download_url': photo['links']['download']
                    })
                
                return images
                
        except Exception as e:
            print(f"Unsplash 검색 오류: {e}")
            
        return []
    
    def _search_pixabay(self, keyword: str, count: int) -> List[Dict]:
        """Pixabay API로 이미지 검색"""
        if not self.pixabay_key:
            return []
            
        try:
            params = {
                'key': self.pixabay_key,
                'q': keyword,
                'image_type': 'photo',
                'orientation': 'horizontal',
                'category': 'backgrounds',
                'min_width': 1280,
                'per_page': count,
                'safesearch': 'true'
            }
            
            response = requests.get(self.pixabay_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                images = []
                for hit in data.get('hits', []):
                    images.append({
                        'url': hit['webformatURL'],
                        'thumb_url': hit['previewURL'],
                        'description': hit.get('tags', keyword),
                        'photographer': hit['user'],
                        'source': 'Pixabay',
                        'download_url': hit['webformatURL']
                    })
                
                return images
                
        except Exception as e:
            print(f"Pixabay 검색 오류: {e}")
            
        return []
