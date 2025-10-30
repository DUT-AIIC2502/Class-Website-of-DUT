import os
import re
import json
import requests
import httpx

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_key_info(text: str) -> dict:
    """
    调用火山引擎的API，提取关键信息。
    :param text: 输入的长文本
    :return: 包含关键信息的字典
    """

    # 获取环境变量，包括API地址、API密钥和模型名称
    if 1 == 1:
        base_url = os.getenv("VOLCENGINE_BASE_URL")
        api_key = os.getenv("VOLCENGINE_API_KEY")
        endpoint_id = os.getenv("VOLCENGINE_ENDPOINT_ID")

    # 初始化客户端
    if 1 == 1:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=httpx.Client(
                timeout=30.0,
                trust_env=False,   # 关键：不读取系统/终端里的 HTTP(S)_PROXY
            ),
        )

    # 构造提示词
    if 1 == 1:
        system_prompt = (
            "你是信息提取助手。请从中文活动通知原文中抽取关键信息并只严格输出 JSON 对象。如果原文中出现多个活动，仅提取第一个活动的信息。\n"
            "字段与要求：\n"
            "- title: 通知标题，简要概括。\n"
            "- theme: 活动主题，若无可留空。\n"
            "- start_time: ISO 8601，如 2025-10-23T15:00:00+08:00；若只给出日期，时间可用 00:00:00；若出现多个时间段，则为 null。\n"
            "- end_time: ISO 8601；要求同start_time，若无则为 null。\n"
            "- location: 活动地点，无则为 null。\n"
            "- participants: 参与人员（人群，如全班同学、全体师生等；或着，具体名单，如xxx、xxx等），无则为 null。\n"
            "- organizer: 组织者，无则为 null。\n"
            "- contact: 联系方式（电话/微信/邮箱），无则为 null。\n"
            "- registration: 报名方式（如到梦空间报名、班长处报名），无则为 null。\n"
            # "- deadline: 报名截止时间（ISO 8601），无则为 null。\n"
            "- raw_time_text: 原文中与时间相关的关键短语，尽量原样摘录，找不到则为 null。\n"
            "- notes: 备注或注意事项，无则为 null。\n"
            "- details: 详细说明，一定要使用单个字符串，而非列表。一定要按行分点，行首使用“- ”标志。在不与以上字段重复的前提下，保留其他信息。\n"
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
    
    # 创建非流式请求（向模型发送请求）
    if 1 == 1:
        try:
            print("向模型发送请求...")
            completion = client.chat.completions.create(
                model=endpoint_id,  # 火山方舟上创建的推理接入点ID
                messages=[
                    {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                    {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
                ],
                # reasoning_effort="medium"  # 模型推理努力程度
            )
            print("请求已发送，等待响应...")
        except TimeoutError:
            print("请求超时，请稍后重试。")
        except Exception as e:
            print("发生错误：", e)

    # 处理响应
    return completion.choices[0].message.content