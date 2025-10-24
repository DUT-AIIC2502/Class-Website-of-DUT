import os
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv()


def get_key_info(text: str) -> dict:
    """
    调用火山引擎的API，提取关键信息。
    :param text: 输入的长文本
    :return: 包含关键信息的字典
    """

    # 获取环境变量，包括API地址、API密钥和模型名称
    base_url = os.getenv("VOLCENGINE_BASE_URL")
    api_key = os.getenv("VOLCENGINE_API_KEY")
    endpoint_id = os.getenv("VOLCENGINE_ENDPOINT_ID")

    api_url = f"{base_url.rstrip('/')}/chat/completions"

    # 构造提示词
    if 1 == 1:
        system_prompt = (
            "你是信息抽取助手。请从中文活动通知原文中抽取关键信息并只严格输出 JSON 对象。\n"
            "字段与要求：\n"
            "- title: 通知标题，简要概括\n"
            "- theme: 活动主题，若无可留空\n"
            "- start_time: ISO 8601，如 2025-10-23T15:00:00+08:00；若只给出日期，时间可用 00:00:00\n"
            "- end_time: ISO 8601；若无则为 null\n"
            "- location: 活动地点，无则空字符串\n"
            "- participants: 参与人员（人群或名单）\n"
            "- organizer: 组织者，无则为 null\n"
            "- contact: 联系方式（电话/微信/邮箱），无则为 null\n"
            "- deadline: 报名截止时间（ISO 8601），无则为 null\n"
            "- raw_time_text: 原文中与时间相关的关键短语，尽量原样摘录，找不到则为 null\n"
            "- notes: 备注或注意事项，无则为 null\n"
            "- details: 详细说明，使用单个字符串，按行分点（用换行分隔），行首使用“- ”标志。要求不与以上字段重复，且剔除无用信息（如客套话等）\n"
            "- confidence: 0~1 的置信度（浮点数）\n"
            "规则：\n"
            "1) 严格输出一个 JSON 对象，不要添加解释或多余文本。\n"
            "2) 所有日期时间尽量解析为含 +08:00 时区的 ISO 8601；实在无法解析则置为 null 并在 notes 中说明。\n"
            "3) 若字段缺失，用空字符串或 null（见上）。\n"
        )

        user_prompt = (
            "原始文本：\n"
            f"{text}\n\n"
            "请按上述字段与要求输出 JSON 对象。"
        )
    
    # 构建请求头和请求体
    if 1 == 1:
        payload = {
            "model": endpoint_id,
            "messages": [
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
            ],
            "temperature": 0.2,
            "top_p": 0.9,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }

    # 发送POST请求到火山引擎API
    if 1 == 1:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to retrieve key information"}