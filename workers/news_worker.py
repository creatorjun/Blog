# workers/news_worker.py

import requests
import re
from urllib.parse import quote
from PyQt6.QtCore import QThread, pyqtSignal

class NaverNewsWorker(QThread):
    """네이버 검색 API 공식 스펙에 맞춘 뉴스 검색 워커 클래스"""
    
    # 시그널 정의
    finished = pyqtSignal(list)           # 뉴스 리스트 완료
    progress = pyqtSignal(int, int)       # 진행률 (현재, 전체)
    error = pyqtSignal(str)               # 에러 메시지
    status_changed = pyqtSignal(str)      # 상태 메시지
    
    def __init__(self, client_id, client_secret):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        # 공식 API URL 사용
        self.api_url = 'https://openapi.naver.com/v1/search/news.json'
        self.keyword = ''
        self.category_id = -1
        self.category_name = ''
        
    def set_search_params(self, keyword='', category_id=-1, category_name=''):
        """검색 파라미터 설정"""
        self.keyword = keyword
        self.category_id = category_id
        self.category_name = category_name
        
    def run(self):
        """워커 스레드 실행"""
        try:
            self.status_changed.emit("네이버 뉴스 검색 API 호출 준비 중...")
            
            # 검색 쿼리 구성
            search_query = self._build_search_query()
            
            if not search_query:
                self.error.emit("검색 키워드나 카테고리를 선택해주세요.")
                return
                
            self.status_changed.emit(f"검색어: '{search_query}' - API 호출 중...")
            
            # 네이버 뉴스 검색 API 호출 (최대 100개)
            news_list = self._fetch_news_from_api(search_query)
            
            if news_list:
                self.status_changed.emit(f"검색 완료: {len(news_list)}개 뉴스 발견")
                self.finished.emit(news_list)
            else:
                self.error.emit("검색 결과가 없습니다.")
                
        except Exception as e:
            self.error.emit(f"뉴스 검색 중 오류 발생: {str(e)}")
    
    def _build_search_query(self):
        """검색 쿼리 구성 (공식 API 스펙에 맞춤)"""
        if self.keyword and self.category_id != -1:
            # 카테고리 + 키워드 조합 검색
            category_keywords = {
                100: "정치",      # 정치
                101: "경제",      # 경제  
                102: "사회",      # 사회
                103: "문화",      # 생활/문화  
                104: "국제",      # 세계
                105: "IT 과학"    # IT/과학
            }
            category_keyword = category_keywords.get(self.category_id, "")
            return f"{self.keyword} {category_keyword}"
        elif self.keyword:
            # 키워드만 검색
            return self.keyword
        elif self.category_id != -1:
            # 카테고리만 검색 (대표 키워드 사용)
            category_queries = {
                100: "정치 국정감사 정책",
                101: "경제 주식 증시 금리",
                102: "사회 복지 교육",
                103: "문화 예술 여행 건강",
                104: "국제 해외 외교",
                105: "IT 과학 기술 인공지능"
            }
            return category_queries.get(self.category_id, "")
        
        return ""
    
    def _fetch_news_from_api(self, query):
        """네이버 뉴스 검색 API 호출 (공식 스펙 준수)"""
        # 공식 API 헤더
        headers = {
            'X-Naver-Client-Id': self.client_id,
            'X-Naver-Client-Secret': self.client_secret
        }
        
        news_list = []
        
        try:
            # API 파라미터 설정 (공식 스펙)
            params = {
                'query': query,           # 검색어 (UTF-8 인코딩 자동 처리)
                'display': 100,           # 최대 100개 (공식 최댓값)
                'start': 1,              # 검색 시작 위치
                'sort': 'date'           # 날짜순 정렬 (sim: 정확도순, date: 날짜순)
            }
            
            self.progress.emit(0, 100)
            
            # 공식 API 요청
            response = requests.get(
                self.api_url, 
                headers=headers, 
                params=params, 
                timeout=15
            )
            
            self.status_changed.emit(f"API 응답 상태: HTTP {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # 공식 API 응답 구조에 맞춤
                total_count = data.get('total', 0)
                start_pos = data.get('start', 1)
                display_count = data.get('display', 0)
                items = data.get('items', [])
                
                self.status_changed.emit(
                    f"API 응답 수신: {len(items)}개 뉴스 (전체 {total_count:,}개 중 {start_pos}번째부터)"
                )
                
                for i, item in enumerate(items):
                    try:
                        # 공식 API 응답 필드 사용
                        title = self._clean_html_text(item.get('title', ''))
                        description = self._clean_html_text(item.get('description', ''))
                        original_link = item.get('originallink', '')
                        naver_link = item.get('link', '')
                        pub_date = item.get('pubDate', '')
                        
                        # 뉴스 정보 구성
                        news_item = {
                            'index': i + 1,
                            'title': title,
                            'description': description,
                            'originallink': original_link,
                            'link': naver_link,
                            'pubDate': self._format_date(pub_date),
                            'category': self.category_name if self.category_name else '전체',
                            'keyword': self.keyword if self.keyword else '카테고리 검색',
                            'total_count': total_count
                        }
                        
                        news_list.append(news_item)
                        
                        # 진행률 업데이트
                        self.progress.emit(i + 1, len(items))
                        
                        # 스레드 중단 확인
                        if self.isInterruptionRequested():
                            self.status_changed.emit("검색이 중단되었습니다.")
                            break
                            
                    except Exception as e:
                        print(f"뉴스 항목 처리 중 오류: {e}")
                        continue
                        
            # 공식 오류 코드 처리
            elif response.status_code == 400:
                error_data = response.json()
                error_code = error_data.get('errorCode', 'SE01')
                error_message = error_data.get('errorMessage', '잘못된 요청')
                
                if error_code == 'SE01':
                    raise Exception("잘못된 쿼리 요청입니다. 검색어를 확인해주세요.")
                elif error_code == 'SE02':
                    raise Exception("부적절한 display 값입니다.")
                elif error_code == 'SE03':
                    raise Exception("부적절한 start 값입니다.")
                elif error_code == 'SE04':
                    raise Exception("부적절한 sort 값입니다.")
                elif error_code == 'SE06':
                    raise Exception("잘못된 형식의 인코딩입니다. 검색어 인코딩을 확인해주세요.")
                else:
                    raise Exception(f"API 요청 오류 ({error_code}): {error_message}")
                    
            elif response.status_code == 401:
                raise Exception("네이버 API 인증 실패. Client ID/Secret을 확인해주세요.")
            elif response.status_code == 403:
                raise Exception("API 권한이 없습니다. 네이버 개발자 센터에서 검색 API 사용 설정을 확인해주세요.")
            elif response.status_code == 404:
                raise Exception("존재하지 않는 검색 API입니다. API URL을 확인해주세요.")
            elif response.status_code == 429:
                raise Exception("API 호출 제한 초과 (일일 25,000회). 잠시 후 다시 시도해주세요.")
            elif response.status_code == 500:
                raise Exception("네이버 서버 내부 오류입니다. 잠시 후 다시 시도해주세요.")
            else:
                raise Exception(f"예상치 못한 HTTP 오류: {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise Exception("API 요청 시간 초과 (15초)")
        except requests.exceptions.ConnectionError:
            raise Exception("네트워크 연결 오류. 인터넷 연결을 확인해주세요.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 요청 실패: {str(e)}")
        
        return news_list
    
    def _clean_html_text(self, html_text):
        """HTML 태그 제거 및 텍스트 정리 (공식 API 응답 형식 처리)"""
        if not html_text:
            return ""
        
        # <b> 태그 제거 (검색어 강조용)
        clean_text = re.sub(r'</?b>', '', html_text)
        
        # 기타 HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        
        # HTML 엔티티 디코딩
        html_entities = {
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&quot;': '"',
            '&#x27;': "'",
            '&#x2F;': '/',
            '&apos;': "'"
        }
        
        for entity, char in html_entities.items():
            clean_text = clean_text.replace(entity, char)
        
        # 연속된 공백 제거
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def _format_date(self, date_string):
        """날짜 형식 정리 (공식 API 날짜 형식 처리)"""
        if not date_string:
            return ""
        
        try:
            # 공식 API 날짜 형식: "Mon, 26 Sep 2016 07:50:00 +0900"
            from datetime import datetime
            import locale
            
            # 영어 로케일 설정 (날짜 파싱용)
            try:
                locale.setlocale(locale.LC_TIME, 'C')
            except:
                pass
                
            # RFC 2822 형식 파싱
            dt = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
            
            # 한국 시간으로 변환 후 포맷팅
            return dt.strftime("%Y-%m-%d %H:%M")
            
        except Exception as e:
            # 파싱 실패 시 원본 반환
            print(f"날짜 파싱 실패 ({date_string}): {e}")
            return date_string
    
    def stop_search(self):
        """검색 중단"""
        self.requestInterruption()
        self.status_changed.emit("검색 중단 요청됨...")
