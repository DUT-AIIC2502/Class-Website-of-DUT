import os
import json
import re
import httpx
import pickle

from flask import Blueprint, request, redirect, render_template, jsonify, session, url_for
from pydantic import BaseModel, Field  # 修正：补充 Field 导入
from dotenv import load_dotenv
from typing import Optional

from common.flask_func import get_session_value, load_session_value

load_dotenv()

notices_bp = Blueprint('notices', __name__,
                       url_prefix='/notices',
                       template_folder='templates')

"""
使用到 session 的键：
- origin_message：用户提交的原始活动通知文本（字符串）
- key_info：提取出的关键信息（pickled bytes）
"""

# ===== 使用豆包抽取关键信息 =====
def extract_notice_json(text: str) -> dict:
    """
    使用 Volcengine Ark Doubao 从自由格式中文活动通知文本中抽取关键信息，返回 dict。
    输出字段见 NoticeInfo。时间字段要求 ISO 8601（含时区 +08:00），缺失用 null 或空字符串。
    """
    api_key = os.getenv("VOLCENGINE_API_KEY")
    base_url = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model = os.getenv("VOLCENGINE_MODEL", "doubao-seed-1-6-lite-251015")
    if not api_key:
        raise RuntimeError("缺少 VOLCENGINE_API_KEY 环境变量")

    url = f"{base_url.rstrip('/')}/chat/completions"

    system_prompt = (
        "你是信息抽取助手。请从中文活动通知原文中抽取关键信息并只输出 JSON 对象。\n"
        "字段与要求：\n"
        "- title: 通知标题，简要概括\n"
        "- theme: 活动主题，若无可留空\n"
        "- start_time: ISO 8601，如 2025-10-23T15:00:00+08:00；若只给出日期，时间可用 00:00:00\n"
        "- end_time: ISO 8601；若无则为 null\n"
        "- location: 活动地点，无则为 null\n"
        "- participants: 参与人员（人群或名单），无则为 null\n"
        "- organizer: 组织者，无则为 null\n"
        "- contact: 联系方式（电话/微信/邮箱），无则为 null\n"
        "- deadline: 报名截止时间（ISO 8601），无则为 null\n"
        "- raw_time_text: 原文中与时间相关的关键短语，尽量原样摘录，找不到则为 null\n"
        "- notes: 备注或注意事项，无则为 null\n"
        "- details: 详细说明，使用单个字符串，按行分点（用换行分隔）\n"
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

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json; charset=utf-8"
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
    except httpx.HTTPError as e:
        raise RuntimeError(f"调用豆包接口失败：{e}") from e
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"豆包返回格式异常：{e}") from e

    try:
        raw_obj = json.loads(content)
    except json.JSONDecodeError:
        # 兜底：尝试截取花括号内容
        m = re.search(r"\{.*\}", content, flags=re.S)
        if not m:
            raise RuntimeError("未能解析为合法 JSON")
        raw_obj = json.loads(m.group(0))

    # Pydantic 校验并标准化键
    notice = NoticeInfo(**raw_obj)

    # 兼容 pydantic v1/v2
    normalized = notice.model_dump() if hasattr(notice, "model_dump") else notice.dict()
    return normalized


@notices_bp.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # 处理表单提交
        pass
    return render_template('notices/home.html')


@notices_bp.route('/new_notices/', methods=['GET', 'POST'])
def new_notices():
    if request.method == 'GET':
        # 获取 session 中的值
        if 1 == 1:
            origin_message = get_session_value('origin_message', default='')
            key_info = load_session_value(get_session_value('key_info', default={}))

        return render_template('notices/new_notices.html', origin_message=origin_message, key_info=key_info)
    
    elif request.method == 'POST':
        form_get = request.form.to_dict()

        if form_get['method'] == "submit_origin_message":
            # 解析原始信息，提取关键信息
            if 1 == 1:
                origin_message = form_get.get('origin_message', '').strip()
                if origin_message:
                    try:
                        key_info = extract_notice_json(origin_message)
                    except Exception as e:
                        return f"<script>alert('解析超时或失败，请稍后重试（{type(e).__name__}）。');window.history.back();</script>"
                else:
                    return f"<script>alert('请输入活动通知文本！');window.history.back();</script>"
                
            # 存入 session
            if 1 == 1:
                session['origin_message'] = origin_message
                session['key_info'] = pickle.dumps(key_info)

        
        elif form_get['method'] == "generate_notice":
            pass

        return redirect(url_for('notices.new_notices'))


# -------- 数据结构 --------
class NoticeInfo(BaseModel):
    title: str = Field(default="", description="通知标题（简要概括）")
    theme: str = Field(default="", description="活动主题")
    start_time: Optional[str] = Field(default=None, description="ISO 8601，如 2025-10-23T15:00:00+08:00")
    end_time: Optional[str] = Field(default=None, description="ISO 8601")
    location: str = Field(default="", description="地点")
    participants: str = Field(default="", description="参与人员（人群或名单）")
    organizer: Optional[str] = None
    contact: Optional[str] = None
    deadline: Optional[str] = None
    raw_time_text: Optional[str] = Field(default=None, description="原文中的时间短语")
    notes: Optional[str] = None
    details: str = Field(default="", description="详细说明（分点展示的单条字符串，每行一个要点）")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


