from typing import Dict

class BlogPrompts:
    CATEGORY_GUIDELINES = {
        '정치': "정치적 중립성을 유지하면서 다양한 관점을 균형있게 제시하고, 정책의 실질적 영향을 분석해주세요.",
        '경제': "경제 지표와 시장 동향을 포함하여 일반인도 이해하기 쉽게 설명하고, 실생활 영향을 중심으로 작성해주세요.",
        '사회': "사회 현상의 배경과 원인을 심층 분석하고, 다양한 계층의 입장을 고려한 균형잡힌 시각을 제시해주세요.",
        '전체': "해당 이슈의 전반적인 맥락과 의미를 포괄적으로 다루어주세요."
    }

    JSON_FORMAT = """{
  "title": "SEO 최적화된 블로그 제목 (30-40자)",
  "content": "# 메인 제목\\n\\n[이미지_1]\\n\\n## 도입부\\n\\n본문 내용...\\n\\n[이미지_2]\\n\\n## 본론\\n\\n계속 내용... (2500자 내외)",
  "conclusion": "독자의 사고를 자극하는 결론 (200자 내외)",
  "image_keywords": ["검색 키워드1", "검색 키워드2"],
  "tags": ["#주요태그1", "#주요태그2", "#트렌딩태그3", "#카테고리태그4", "#SEO태그5", "#관련키워드6", "#이슈태그7", "#소셜태그8"]
}"""

    @classmethod
    def get_blog_prompt(cls, news_item: Dict, additional_info: str = "") -> str:
        title = news_item.get('title', '제목 없음')
        description = news_item.get('description', '')
        category = news_item.get('category', '일반')
        pub_date = news_item.get('pubDate', '')
        category_guide = cls.CATEGORY_GUIDELINES.get(category, cls.CATEGORY_GUIDELINES['전체'])

        return f"""당신은 10년 경력의 전문 블로그 작가입니다. 다음 뉴스를 바탕으로 고품질 블로그 포스팅을 작성해주세요.
                **📰 뉴스 정보**
                - 제목: {title}
                - 카테고리: {category}
                - 발행일: {pub_date}
                - 요약: {description}

                **🔍 추가 배경 정보**
                {additional_info}

                **✍️ 작성 가이드라인**

                **제목 작성**
                - 30-40자 내외의 SEO 최적화된 클릭 유도 제목

                **본문 구성 (2500자 내외)**
                1. **도입부**: 독자의 관심을 끄는 흥미로운 시작
                2. **배경 설명**: 이슈의 맥락과 배경 ([이미지_1] 마커 삽입)
                3. **핵심 내용 분석**: 뉴스의 주요 내용과 의미
                4. **다양한 관점**: 여러 입장과 의견 제시 ([이미지_2] 마커 삽입)
                - {category_guide}
                5. **영향과 전망**: 향후 예상되는 변화와 영향

                **이미지 키워드 생성**
                - `image_keywords`는 이미지 검색에 사용할 구체적인 영어 키워드 2개를 포함해야 합니다.
                - 추상적인 단어(예: 'economy', 'society')보다는 뉴스 내용과 관련된 구체적인 사물이나 장면을 묘사하는 키워드(예: 'stock market chart', 'protesting crowd')를 사용해주세요.

                **📋 JSON 출력 형식**
                반드시 아래 JSON 형식으로만 응답하세요. 다른 설명은 추가하지 마세요.

                **🚨 중요사항**
                - 본문에는 반드시 [이미지_1], [이미지_2] 마커를 포함해야 합니다.

                전문적이고 매력적인 블로그 포스팅을 작성해주세요."""

    @classmethod
    def get_context_template(cls, category: str, search_query: str) -> str:
        templates = {
            '정치': f"최근 정치권에서는 '{search_query}' 관련 논의가 활발히 진행되고 있으며, 여야 간 입장 차이가 뚜렷합니다.",
            '경제': f"'{search_query}' 이슈는 국내 경제와 시장에 미치는 영향이 클 것으로 전망되며, 전문가들의 의견이 분분합니다.",
            '사회': f"'{search_query}' 사안에 대해 시민사회와 각계각층에서 다양한 의견과 대안이 제시되고 있습니다.",
            '전체': f"'{search_query}' 관련하여 다방면에서 관심이 집중되고 있으며, 향후 전개 과정이 주목받고 있습니다."
        }
        return templates.get(category, templates['전체'])