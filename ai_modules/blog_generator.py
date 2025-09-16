# ai_modules/blog_generator.py

import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

# --- 수정된 부분 (1): 필요한 모듈을 파일 상단으로 이동 ---
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except ImportError:
    # 이 경우, _init_client에서 처리되므로 여기서는 pass합니다.
    pass

from .blog_prompts import BlogPrompts

class BlogGenerator(QThread):
    """최신 Google GenAI SDK 기반 블로그 생성기 (프롬프트 분리)"""
    
    blog_generated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    
    def __init__(self, gemini_api_key: str):
        super().__init__()
        self.gemini_api_key = gemini_api_key
        self.news_data = []
        self.model = None  # --- 수정된 부분: client 대신 model 객체를 사용 ---
        self._init_client()
        
    def _init_client(self):
        """Google GenAI 클라이언트 초기화"""
        try:
            # --- 수정된 부분 (2): genai.configure를 사용한 명확한 초기화 ---
            genai.configure(api_key=self.gemini_api_key)
            # --- 수정된 부분 (3): 최신 SDK 방식에 맞춰 모델 객체 생성 ---
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest') # 유효한 최신 모델명으로 변경
            print("✅ Google GenAI 클라이언트 초기화 완료")
        except ImportError:
            print("❌ google-generativeai 라이브러리가 설치되지 않았습니다. pip install google-generativeai")
            self.model = None
        except Exception as e:
            print(f"❌ 클라이언트 초기화 실패: {e}")
            self.model = None
    
    def set_news_data(self, news_data: List[Dict]):
        self.news_data = news_data
        
    def run(self):
        try:
            # --- 수정된 부분: client 대신 model 객체 확인 ---
            if not self.model:
                self.error_occurred.emit("Google GenAI 클라이언트 초기화 실패")
                return
                
            self.progress_updated.emit(20)
            self.status_changed.emit("뉴스 분석 중...")
            
            top_news = self._select_top_news()
            if not top_news:
                self.error_occurred.emit("분석할 뉴스가 없습니다")
                return
                
            self.progress_updated.emit(50)
            self.status_changed.emit("AI 블로그 생성 중...")
            
            additional_info = self._get_additional_context(top_news)
            prompt = BlogPrompts.get_blog_prompt(top_news, additional_info)
            
            blog_data = self._generate_with_sdk(prompt)
            
            self.progress_updated.emit(90)
            self.status_changed.emit("후처리 중...")
            
            final_blog = self._post_process(blog_data, top_news)
            
            self.progress_updated.emit(100)
            self.status_changed.emit("완료!")
            
            self.blog_generated.emit(final_blog)
            
        except Exception as e:
            self.error_occurred.emit(f"오류: {str(e)}")
    
    def _select_top_news(self) -> Optional[Dict]:
        """화제성 높은 뉴스 선택"""
        if not self.news_data:
            return None
            
        news_scores = []
        for i, news in enumerate(self.news_data):
            score = max(0, 100 - i)
            title = news.get('title', '')
            
            keywords = ['국정감사', '정치', '경제', '대통령', '개혁', '정책']
            for keyword in keywords:
                if keyword in title:
                    score += 20
                    
            news_scores.append((score, news))
        
        news_scores.sort(key=lambda x: x[0], reverse=True)
        # --- 수정된 부분: 불필요한 else 구문 제거로 코드 간소화 ---
        return news_scores[0][1] if news_scores else None
    
    def _get_additional_context(self, news_item: Dict) -> str:
        """추가 컨텍스트 생성 (프롬프트 클래스 활용)"""
        title = news_item.get('title', '')
        category = news_item.get('category', '')
        
        keywords = re.findall(r'[가-힣\w]{2,}', title)[:3] # 영문/숫자도 포함하도록 \w 추가
        search_query = ' '.join(keywords) if keywords else title
        
        return BlogPrompts.get_context_template(category, search_query)
    
    def _generate_with_sdk(self, prompt: str) -> Dict:
        """최신 SDK로 생성"""
        try:
            # --- 수정된 부분 (4): 최신 SDK 호출 방식으로 전면 수정 ---
            generation_config = GenerationConfig(
                temperature=0.7,
                top_k=40,
                top_p=0.9,
                max_output_tokens=4000,
                # JSON 출력을 강제하고 싶을 때 유용합니다.
                response_mime_type="application/json"
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # response_mime_type을 사용하면 바로 JSON 파싱 시도 가능
            return json.loads(response.text)
            
        except json.JSONDecodeError:
             # 만약 모델이 JSON 형식을 완벽히 지키지 않았을 경우를 대비한 2차 처리
            return self._extract_json(response.text)
        except Exception as e:
            raise Exception(f"SDK 호출 실패: {str(e)}")
    
    def _extract_json(self, text: str) -> Dict:
        """텍스트에서 JSON 추출 (SDK가 JSON을 반환하지 못했을 때의 예비용)"""
        # 정규식 수정: 좀 더 유연하게 코드 블록을 찾도록 함
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            # --- 수정된 부분 (5): 구체적인 예외를 지정 ---
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 실패: {e}")
                pass
        
        # 기본 구조 반환
        return {
            "title": "AI 생성 블로그",
            "content": text[:2000],
            "conclusion": "추가 논의가 필요합니다.",
            "image_search_terms": ["뉴스", "분석"],
            "image_placements": [{"position": "도입부", "description": "관련 이미지"}],
            "tags": ["#뉴스", "#AI", "#블로그"]
        }
    
    def _post_process(self, blog_data: Dict, original_news: Dict) -> Dict:
        """후처리"""
        content = blog_data.get("content", "")
        # --- 수정된 부분 (6): 글자 수가 아닌 단어 수로 계산 ---
        word_count = len(content.split())
        
        return {
            **blog_data,
            "source_news": {
                "title": original_news.get("title", ""),
                "url": original_news.get("originallink", ""),
                "pub_date": original_news.get("pubDate", "")
            },
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "generator": "Gemini 1.5 Flash (Latest SDK)",
            "word_count": word_count,
            "estimated_read_time": max(1, word_count // 300) # 분당 300단어 기준으로 계산
        }