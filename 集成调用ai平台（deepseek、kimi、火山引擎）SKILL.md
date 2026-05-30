---
name: "unified-ai-api-caller"
description: "Provides unified API calling patterns for multiple AI platforms (DeepSeek, Volcano Ark, etc.). Invoke when user needs to call different AI platform models or wants to integrate multi-platform AI services."
---

# 统一AI平台调用Skill

本Skill整合了多个AI平台的调用方式，提供统一的调用模式和最佳实践。

## 支持的平台

| 平台 | Base URL | 认证方式 | SDK兼容性 |
|------|----------|----------|-----------|
| DeepSeek | `https://api.deepseek.com` | API Key | OpenAI兼容 |
| 火山方舟 | `https://ark.cn-beijing.volces.com/api/v3` | Bearer Token | OpenAI兼容 |
| Kimi (Moonshot) | `https://api.moonshot.cn/v1` | Bearer Token | OpenAI兼容 |

---

## 一、核心调用模式

### 1.1 环境变量配置

```env
# DeepSeek配置
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro

# 火山方舟配置
VOLCANO_API_KEY=your-api-key
VOLCANO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCANO_LLM_MODEL=ep-20260408103607-8qzk4
VOLCANO_VIDEO_MODEL=ep-20260407161453-x5xkp
VOLCANO_IMAGE_MODEL=ep-20260408105431-x5ggb

# Kimi (Moonshot) 配置
MOONSHOT_API_KEY=your-api-key
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=moonshot-v1-8k
```

### 1.2 统一客户端封装

```python
from openai import OpenAI
from typing import Optional, Dict, Any
import os

class UnifiedAIClient:
    """统一AI客户端，支持多平台"""
    
    PLATFORMS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "api_key_env": "DEEPSEEK_API_KEY",
            "default_model": "deepseek-v4-pro"
        },
        "volcano": {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "api_key_env": "VOLCANO_API_KEY",
            "default_model": "ep-20260408103607-8qzk4"
        },
        "kimi": {
            "base_url": "https://api.moonshot.cn/v1",
            "api_key_env": "MOONSHOT_API_KEY",
            "default_model": "moonshot-v1-8k"
        }
    }
    
    def __init__(self, platform: str = "deepseek", api_key: Optional[str] = None):
        if platform not in self.PLATFORMS:
            raise ValueError(f"不支持的平台: {platform}")
        
        config = self.PLATFORMS[platform]
        self.platform = platform
        self.api_key = api_key or os.getenv(config["api_key_env"], "")
        self.base_url = config["base_url"]
        self.default_model = config["default_model"]
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ):
        """统一聊天接口"""
        model_name = model or self.default_model
        
        return self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
    
    def chat_stream(self, messages: list, **kwargs):
        """流式聊天接口"""
        stream = self.chat(messages, stream=True, **kwargs)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

---

## 二、各平台详细调用指南

### 2.1 DeepSeek平台

#### 可用模型

| 模型 | 描述 | 状态 |
|------|------|------|
| deepseek-v4-pro | 高级推理，复杂任务（推荐） | 可用 |
| deepseek-v4-flash | 快速响应，日常对话 | 可用 |
| deepseek-chat | 快速响应 | 2026/07/24废弃 |
| deepseek-reasoner | 推理模式 | 2026/07/24废弃 |

#### 基础调用示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[
        {"role": "system", "content": "你是一个专业的AI助手"},
        {"role": "user", "content": "你好"}
    ],
    temperature=0.7,
    max_tokens=2000
)

print(response.choices[0].message.content)
```

#### 流式调用

```python
stream = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": "写一首诗"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

---

### 2.2 火山方舟平台

#### 可用模型

| 模型类型 | 模型名称 | Endpoint ID | 调用方式 |
|----------|---------|-------------|----------|
| 大语言模型 | DeepSeek | ep-20260408103607-8qzk4 | OpenAI SDK |
| 大语言模型 | GLM-4.7 | ep-20260408104920-r9c4f | OpenAI SDK |
| 视频生成 | Doubao-Seedance-1.5-pro | ep-20260407161453-x5xkp | HTTP REST |
| 图像生成 | Doubao-Seedream-5.0-lite | ep-20260408105431-x5ggb | OpenAI SDK |

#### 大语言模型调用

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

response = client.chat.completions.create(
    model="ep-20260408103607-8qzk4",
    messages=[
        {"role": "system", "content": "你是一个专业的AI助手"},
        {"role": "user", "content": "你好"}
    ],
    temperature=0.7,
    max_tokens=2000
)

print(response.choices[0].message.content)
```

#### 联网搜索功能

```python
tools = [{"type": "web_search", "max_keyword": 2}]

response = client.responses.create(
    model="ep-20260408103607-8qzk4",
    input=[{"role": "user", "content": "北京的天气怎么样？"}],
    tools=tools,
)
print(response)
```

#### 图像生成

```python
response = client.images.generate(
    model="ep-20260408105431-x5ggb",
    prompt="星际穿越，黑洞，视觉冲击力",
    size="2K",
    response_format="url",
    extra_body={"watermark": True}
)

print(response.data[0].url)
```

#### 视频生成（HTTP方式）

```python
import requests
import time

class VideoGenerator:
    def __init__(self, api_key: str, model_id: str):
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def generate(self, prompt: str, duration: int = 5) -> str:
        """创建视频任务，返回task_id"""
        content = [{
            "type": "text",
            "text": f"{prompt} --duration {duration} --watermark false"
        }]
        
        resp = requests.post(
            f"{self.base_url}/contents/generations/tasks",
            headers=self.headers,
            json={"model": self.model_id, "content": content},
            timeout=60
        )
        return resp.json()["id"]
    
    def get_video_url(self, task_id: str, timeout: int = 600) -> str:
        """轮询等待完成，返回视频URL"""
        elapsed = 0
        while elapsed < timeout:
            resp = requests.get(
                f"{self.base_url}/contents/generations/tasks/{task_id}",
                headers=self.headers,
                timeout=30
            )
            result = resp.json()
            status = result.get("status")
            
            if status == "succeeded":
                return result["content"]["video_url"]
            elif status == "failed":
                raise Exception(result.get("error_message"))
            
            time.sleep(10)
            elapsed += 10
        
        raise TimeoutError(f"视频生成超时 ({timeout}s)")
```

---

### 2.3 Kimi (Moonshot) 平台

#### 服务信息

| 项目 | 值 |
|------|-----|
| Base URL | `https://api.moonshot.cn/v1` |
| 认证方式 | Bearer Token |
| SDK兼容性 | OpenAI兼容 |
| Python要求 | ≥ 3.7.1 |
| Node.js要求 | ≥ 18 |
| OpenAI SDK要求 | ≥ 1.0.0 |

#### 基础调用示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="$MOONSHOT_API_KEY",
    base_url="https://api.moonshot.cn/v1",
)

response = client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[
        {"role": "system", "content": "你是一个专业的AI助手"},
        {"role": "user", "content": "你好"}
    ],
    temperature=0.7,
    max_tokens=2000
)

print(response.choices[0].message.content)
```

#### 流式调用

```python
stream = client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[{"role": "user", "content": "写一首诗"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### Kimi特有功能

**Thinking模式**（通过`extra_body`传递）：

```python
response = client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[{"role": "user", "content": "复杂推理问题"}],
    extra_body={"thinking": True}
)
```

**Partial Mode**（在assistant消息中设置）：

```python
messages = [
    {"role": "user", "content": "帮我写一篇文章"},
    {"role": "assistant", "content": "好的，我来写", "partial": True},
]
```

#### 可用API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | 创建对话补全 |
| `/v1/models` | GET | 列出模型 |
| `/v1/tokenizers/estimate-token-count` | POST | 计算Token |
| `/v1/users/me/balance` | GET | 查询余额 |
| `/v1/files` | POST | 上传文件 |
| `/v1/files` | GET | 列出文件 |
| `/v1/files/{file_id}` | GET | 获取文件信息 |
| `/v1/files/{file_id}` | DELETE | 删除文件 |
| `/v1/files/{file_id}/content` | GET | 获取文件内容 |

#### 错误处理

常见HTTP状态码：
- 400：请求错误
- 401：认证失败
- 429：速率限制
- 500：服务端错误

错误响应格式：
```json
{
  "error": {
    "type": "error_type",
    "message": "error_message"
  }
}
```

---

## 三、平台对比与选择指南

### 3.1 功能对比

| 功能 | DeepSeek | 火山方舟 | Kimi (Moonshot) |
|------|----------|----------|-----------------|
| 文本对话 | ✅ | ✅ | ✅ |
| 流式输出 | ✅ | ✅ | ✅ |
| 联网搜索 | ❌ | ✅ | ❌ |
| 图像生成 | ❌ | ✅ | ❌ |
| 视频生成 | ❌ | ✅ | ❌ |
| Thinking模式 | ✅ (原生) | ❌ | ✅ (extra_body) |
| Partial Mode | ❌ | ❌ | ✅ |
| 文件上传 | ❌ | ❌ | ✅ |
| Token估算 | ❌ | ❌ | ✅ |
| 余额查询 | ❌ | ❌ | ✅ |
| 多模型支持 | 仅DeepSeek系列 | DeepSeek、GLM、Doubao系列 | Moonshot系列 |

### 3.2 选择建议

- **纯文本对话**：三个平台均可，根据响应速度和成本选择
- **需要联网搜索**：选择火山方舟
- **需要多媒体生成**：选择火山方舟
- **需要多模型切换**：选择火山方舟
- **需要Thinking模式**：DeepSeek或Kimi
- **需要Partial Mode**：选择Kimi
- **需要文件处理**：选择Kimi
- **成本敏感**：根据实际定价对比选择

---

## 四、最佳实践

### 4.1 配置管理

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class AISettings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-pro"
    
    # 火山方舟
    volcano_api_key: str = ""
    volcano_llm_model: str = "ep-20260408103607-8qzk4"
    volcano_video_model: str = "ep-20260407161453-x5xkp"
    volcano_image_model: str = "ep-20260408105431-x5ggb"
    
    # Kimi (Moonshot)
    moonshot_api_key: str = ""
    moonshot_model: str = "moonshot-v1-8k"
    
    # 默认平台
    default_platform: str = "deepseek"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_ai_settings() -> AISettings:
    return AISettings()
```

### 4.2 错误处理

```python
from openai import OpenAIError, APIStatusError, APITimeoutError

def safe_chat(client, messages, **kwargs):
    """安全的聊天调用"""
    try:
        response = client.chat.completions.create(
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    except APIStatusError as e:
        print(f"API状态错误: {e.status_code} - {e.message}")
        return None
    except APITimeoutError:
        print("请求超时")
        return None
    except OpenAIError as e:
        print(f"OpenAI错误: {e}")
        return None
    except Exception as e:
        print(f"未知错误: {e}")
        return None
```

### 4.3 客户端池化

```python
class AIClientPool:
    """AI客户端连接池"""
    
    def __init__(self):
        self._clients = {}
    
    def get_client(self, platform: str):
        """获取或创建客户端"""
        if platform not in self._clients:
            self._clients[platform] = UnifiedAIClient(platform=platform)
        return self._clients[platform]
    
    def close_all(self):
        """关闭所有客户端"""
        self._clients.clear()

# 全局连接池
ai_pool = AIClientPool()
```

---

## 五、快速开始清单

- [ ] 安装依赖：`pip install openai requests pydantic-settings`
- [ ] 创建`.env`文件，配置API Key
- [ ] 选择目标平台（DeepSeek或火山方舟）
- [ ] 使用统一客户端或平台特定客户端
- [ ] 测试基础聊天功能
- [ ] 根据需要启用流式输出、联网搜索等功能
- [ ] 添加错误处理和重试机制

---

## 六、常见问题

### Q1: 如何切换平台？
修改`UnifiedAIClient`初始化时的`platform`参数，或创建不同平台的客户端实例。

### Q2: 火山方舟的Endpoint ID从哪里获取？
在火山方舟控制台创建模型部署后获取。

### Q3: 视频生成为什么不支持OpenAI SDK？
火山方舟的视频生成使用自定义API格式，需使用HTTP REST或火山SDK。

### Q4: 如何处理API Key过期？
捕获`APIStatusError`，检查状态码401，提示用户更新API Key。

---

## 七、扩展建议

1. **添加新平台**：在`PLATFORMS`字典中添加新平台配置
2. **添加新功能**：根据平台API文档扩展对应方法
3. **添加监控**：记录API调用次数、延迟、错误率
4. **添加缓存**：对相同请求缓存响应结果
5. **添加重试**：实现指数退避重试机制
