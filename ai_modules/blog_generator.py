import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except ImportError:
    genai = None
    GenerationConfig = None

from .blog_prompts import BlogPrompts

class BlogGenerator(QThread):
    blog_generated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    progress_updated = pyqtSignal(int)

    def __init__(self, gemini_api_key: str):
        super().__init__()
        self.gemini_api_key = gemini_api_key
        self.news_data = []
        self.model = None
        self._init_client()

    def _init_client(self):
        if not genai:
            print("google-generativeai 라이브러리가 설치되지 않았습니다.")
            self.model = None
            return
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            print(f"클라이언트 초기화 실패: {e}")
            self.model = None

    def set_news_data(self, news_data: List[Dict]):
        self.news_data = news_data

    def run(self):
        try:
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
        return news_scores[0][1] if news_scores else None

    def _get_additional_context(self, news_item: Dict) -> str:
        title = news_item.get('title', '')
        category = news_item.get('category', '')
        keywords = re.findall(r'[가-힣\w]{2,}', title)[:3]
        search_query = ' '.join(keywords) if keywords else title
        return BlogPrompts.get_context_template(category, search_query)

    def _generate_with_sdk(self, prompt: str) -> Dict:
        try:
            generation_config = GenerationConfig(
                temperature=0.7,
                top_k=40,
                top_p=0.9,
                max_output_tokens=4000,
                response_mime_type="application/json"
            )
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return json.loads(response.text)
        except json.JSONDecodeError:
            return self._extract_json(response.text)
        except Exception as e:
            raise Exception(f"SDK 호출 실패: {str(e)}")

    def _extract_json(self, text: str) -> Dict:
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 실패: {e}")

        return {
            "title": "AI 생성 블로그",
            "content": text[:2000],
            "conclusion": "추가 논의가 필요합니다.",
            "image_search_terms": ["뉴스", "분석"],
            "tags": ["#뉴스", "#AI", "#블로그"]
        }

    def _post_process(self, blog_data: Dict, original_news: Dict) -> Dict:
        content = blog_data.get("content", "")
        word_count = len(content.split())
        return {
            **blog_data,
            "source_news": {
                "title": original_news.get("title", ""),
                "url": original_news.get("originallink", ""),
                "pub_date": original_news.get("pubDate", "")
            },
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "generator": "Gemini 2.5 Flash",
            "word_count": word_count,
            "estimated_read_time": max(1, word_count // 300)
        }