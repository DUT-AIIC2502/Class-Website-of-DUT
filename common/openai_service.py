"""简单的 OpenAI (GPT) 封装服务。兼容旧版和新版 SDK，增加超时与错误捕获。
"""
import os
from typing import Optional, Dict

try:
    # 新版 SDK（>=1.x）推荐用法
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # 可能未安装或是旧版 SDK

try:
    # 兼容旧版 SDK（<1.x）
    import openai  # type: ignore
except Exception:
    openai = None


class OpenAIService:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5", proxy: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.last_error: Optional[str] = None
        self.proxy = proxy or os.environ.get("OPENAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

        # 旧版全局设置 api_key
        if openai is not None and self.api_key:
            try:
                openai.api_key = self.api_key
            except Exception:
                pass

        # 设置全局代理环境变量，适配 requests 层
        if self.proxy:
            try:
                os.environ.setdefault('HTTPS_PROXY', self.proxy)
                os.environ.setdefault('HTTP_PROXY', self.proxy)
            except Exception:
                pass

    def available(self) -> bool:
        # 只要装了任一 SDK 且提供了 API key 即可认为可用
        return bool(self.api_key) and (OpenAI is not None or openai is not None)

    def chat(self, prompt: str, max_tokens: int = 256, timeout: float = 10.0) -> Optional[str]:
        """向 OpenAI 发出一个简单的对话请求，返回模型生成的文本；失败返回 None。
        会将错误信息保存到 self.last_error 便于上层返回详细错误。
        """
        self.last_error = None
        if not self.available():
            self.last_error = "SDK 未安装或缺少 API Key"
            return None

        # 新版优先
        if OpenAI is not None:
            try:
                # 新版 SDK Client 支持传入 base_url/proxies 等；不同版本参数略有差异
                # 这里用 requests 底层代理环境变量方式更通用
                client = OpenAI(api_key=self.api_key)
                # 部分版本支持 timeout 参数；如不支持会抛错，转而使用旧版或不传超时
                try:
                    resp = client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        timeout=timeout,
                    )
                except TypeError:
                    # 不支持 timeout 参数时重试
                    resp = client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                    )
                choices = getattr(resp, 'choices', None)
                if choices and len(choices) > 0:
                    content = getattr(choices[0].message, 'content', None)
                    return content
            except Exception as e:
                self.last_error = str(e)
                # 不直接返回，尝试旧版

        # 兼容旧版 SDK
        if openai is not None:
            try:
                # 某些旧版支持 timeout 参数
                # 旧版 SDK 也遵循环境变量 HTTP(S)_PROXY，可在 __init__ 时设置
                if self.proxy:
                    os.environ.setdefault('HTTPS_PROXY', self.proxy)
                    os.environ.setdefault('HTTP_PROXY', self.proxy)
                try:
                    resp = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        timeout=timeout,
                    )
                except TypeError:
                    resp = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                    )
                choices = resp.get("choices") if isinstance(resp, dict) else getattr(resp, 'choices', None)
                if choices and len(choices) > 0:
                    # 旧版通常为 dict
                    if isinstance(resp, dict):
                        return choices[0].get("message", {}).get("content")
                    else:
                        return getattr(choices[0].message, 'content', None)
            except Exception as e:
                self.last_error = str(e)

        return None
