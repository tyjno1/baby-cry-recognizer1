# -*- coding: utf-8 -*-
"""DeepSeek AI Client"""
import httpx
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, NEED_CATEGORIES, BEHAVIOR_PATTERNS

class DeepSeekClient:
    """DeepSeek API Client"""

    def __init__(self):
        self._client = None
        self.model = DEEPSEEK_MODEL

    def _get_client(self):
        if self._client is None:
            if not DEEPSEEK_API_KEY:
                raise RuntimeError("DeepSeek API Key 未配置，请在侧边栏设置")
            http_client = httpx.Client(timeout=60.0)
            self._client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL,
                http_client=http_client
            )
        return self._client
    
    def analyze_cry(self, feature_description: str, behaviors: list = None) -> dict:
        """
        Analyze baby cry with audio features and behavior patterns
        Returns: {"need": "hungry", "confidence": 0.85, "reason": "..."}
        """
        categories_desc = "\n".join([f"- {k}: {v}" for k, v in NEED_CATEGORIES.items()])
        behaviors_desc = "\n".join([f"- {k}: {v}" for k, v in BEHAVIOR_PATTERNS.items()])
        
        behavior_text = ""
        if behaviors:
            selected = [BEHAVIOR_PATTERNS.get(b, b) for b in behaviors]
            behavior_text = f"\n观察到的行为：{', '.join(selected)}"
        
        system_prompt = f"""你是一位专业的婴儿护理专家。根据提供的音频特征和行为表现，判断宝宝的需求类别。

可用需求类别：
{categories_desc}

可用行为表现：
{behaviors_desc}

分析规则：
1. 结合音频特征和行为表现进行综合判断
2. 行为表现是强指示信号，请给予较高权重
3. 只返回JSON格式，不要其他文字：
{{
    "need": "category_code",
    "confidence": 0.85,
    "reason": "简要分析理由（中文）"
}}
"""
        
        user_content = f"{feature_description}{behavior_text}"
        
        try:
            response = self._get_client().chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            import json
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            
            if result["need"] not in NEED_CATEGORIES:
                result["need"] = "hungry"
                result["confidence"] = 0.0
            
            return result
            
        except Exception as e:
            print(f"DeepSeek API call failed: {e}")
            return {
                "need": "hungry",
                "confidence": 0.0,
                "reason": f"API调用失败：{str(e)}"
            }
    
    def is_configured(self) -> bool:
        """Check if API Key is configured"""
        return bool(DEEPSEEK_API_KEY)
