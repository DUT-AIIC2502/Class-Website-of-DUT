import os
import json
import re
import httpx
import pickle

from flask import Blueprint, request, redirect, render_template, jsonify, session, url_for
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
from openai import OpenAI

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
            key_info = load_session_value(get_session_value('notice_extracted_info', default={}))

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


def _build_messages(notice_text: str) -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    tz = os.getenv("TZ", "Asia/Shanghai")
    sys = (
        "你是信息抽取助手，从中文活动通知中提取关键字段。"
        "必须只输出一个严格的 JSON 对象字符串，不要任何额外文字、解释、前后缀、Markdown 代码块或注释。"
        f"当前日期：{today}；时区：{tz}。"
        "尽量解析相对时间（如“本周五下午三点”）为 ISO 8601，无法解析则置空，并在 raw_time_text 中保留原短语。"
        "若字段缺失请用空字符串或 null；给出 0~1 的 confidence。"
        "JSON 字段为：title, theme, start_time, end_time, location, participants, organizer, contact, deadline, raw_time_text, notes, details, confidence。"
        "其中 details 必须是一个字符串：按分点列出要点，每个要点独占一行，使用“- ”前缀；不要数组或嵌套结构。"
        "严格避免 details 与其它字段信息重复：details 不得包含或改写 title、theme、start_time、end_time、location、participants、organizer、contact、deadline、raw_time_text 中的内容（例如时间、地点、人员、联系人、报名截止等）。"
        "details 仅保留补充性要点，如：注意事项、所需材料清单、流程/日程安排、着装/携带物、报名方式/步骤、费用或补贴说明、打卡/考勤、奖惩要求等。"
        "对 details 去重去噪，删除签名、页脚、广告、与任务无关的客套话，若无法提供补充性要点则返回空字符串。"
    )
    user = f"待解析文本：\n{notice_text}"
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ]


# 新增：从模型返回中稳健提取 JSON
def _extract_json_object(text: str) -> dict:
    # 1) 去掉可能的代码围栏```json ... ```
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fenced:
        text = fenced.group(1)

    # 2) 直接尝试
    try:
        return json.loads(text)
    except Exception:
        pass

    # 3) 扫描首个完整的大括号 JSON 对象
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        break

    # 4) 兜底：返回空结构，避免崩溃
    return {
        "title": "",
        "theme": "",
        "start_time": None,
        "end_time": None,
        "location": "",
        "participants": "",
        "organizer": None,
        "contact": None,
        "deadline": None,
        "raw_time_text": None,
        "notes": None,
        "details": "",
        "confidence": 0.0,
    }


# 归一化 details：将任意形式（字符串/数组/对象树）转换为分点字符串
def _coerce_details_text(value) -> str:
    if not value:
        return ""
    items: list[str] = []

    def push(s):
        s = str(s).strip()
        if not s:
            return
        # 去掉常见项目符号或编号
        s = re.sub(r"^\s*[\-\*•·●○\u2022\u25CF\u25CB]+\s*", "", s)
        s = re.sub(r"^\s*\d+[\.\)]\s*", "", s)
        if s:
            items.append(s)

    if isinstance(value, str):
        # 按行/分号/顿号分割
        parts = re.split(r"(?:\r?\n|[;；]|[、])", value)
        for p in parts:
            push(p)
    elif isinstance(value, list):
        for e in value:
            if isinstance(e, str):
                push(e)
            elif isinstance(e, dict):
                t = (e.get("title") or "")
                x = (e.get("text") or "")
                combined = f"{t}：{x}" if t and x else (t or x)
                if combined:
                    push(combined)
                ch = e.get("children")
                if isinstance(ch, list):
                    # 递归拍平
                    for sub in ch:
                        if isinstance(sub, dict):
                            st = (sub.get("title") or "")
                            sx = (sub.get("text") or "")
                            sc = f"{st}：{sx}" if st and sx else (st or sx)
                            if sc:
                                push(sc)
                        else:
                            push(sub)
            else:
                push(e)
    elif isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (str, int, float)):
                push(f"{k}: {v}")
            else:
                # 深层拍平
                sv = _coerce_details_text(v)
                if sv:
                    for line in sv.splitlines():
                        push(line)
    else:
        push(value)

    # 拼成多行分点字符串
    if not items:
        return ""
    return "\n".join(f"- {s}" for s in items)


# -------- 方舟（豆包）OpenAI 兼容客户端（支持模型名或端点ID） --------
def _get_ark_client() -> OpenAI:
    """
    .env 需配置：
      VOLCENGINE_API_KEY=你的API Key（方舟控制台-API Key）
      VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
      VOLCENGINE_MODEL=模型名或端点ID
        - 公共模型名示例：doubao-lite-4k、doubao-pro-4k、doubao-vision、doubao-reasoning 等
        - 端点ID示例：ep-xxxxxxxxxxxxxxxx
    """
    api_key = os.getenv("VOLCENGINE_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 VOLCENGINE_API_KEY（方舟 API Key）")

    base_url = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    timeout = float(os.getenv("ARK_TIMEOUT", "45"))

    # 忽略系统代理，避免无效代理导致连接被拒。需要代理可改为 trust_env=True
    http_client = httpx.Client(timeout=timeout, trust_env=False)
    return OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)


# -------- 核心：解析函数（使用豆包）--------
def extract_notice_json(notice_text: str) -> dict:
    client = _get_ark_client()
    model = os.getenv("VOLCENGINE_MODEL", "").strip()
    if not model:
        model = "doubao-lite-4k"  # 公共模型名

    resp = client.chat.completions.create(
        model=model,  # 支持 doubao-xxx 或 ep-xxxx
        messages=_build_messages(notice_text),
        temperature=0,
        # 去掉不被支持的 response_format
    )
    content = resp.choices[0].message.content

    # 使用稳健解析
    data = _extract_json_object(content)

    # 字段兼容与补全
    if "theme" not in data and "activity_name" in data:
        data["theme"] = data.get("activity_name") or ""
    data.setdefault("title", "")
    data["details"] = _coerce_details_text(data.get("details"))

    # Pydantic 校验与兜底
    try:
        parsed = NoticeInfo(**data)
        return parsed.model_dump() if hasattr(parsed, "model_dump") else parsed.dict()
    except ValidationError:
        return {
            "title": data.get("title", ""),
            "theme": data.get("theme", data.get("activity_name", "")),
            "start_time": data.get("start_time", ""),
            "end_time": data.get("end_time", ""),
            "location": data.get("location", ""),
            "participants": data.get("participants", ""),
            "organizer": data.get("organizer", ""),
            "contact": data.get("contact", ""),
            "deadline": data.get("deadline", ""),
            "raw_time_text": data.get("raw_time_text", ""),
            "notes": data.get("notes", ""),
            "details": _coerce_details_text(data.get("details")),
            "confidence": float(data.get("confidence", 0)) if isinstance(data.get("confidence", 0), (int, float, str)) else 0.0
        }


# -------- 提供一个 API：POST /notices/api/parse_notice --------
@notices_bp.route('/api/parse_notice', methods=['POST'])
def parse_notice():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text 为空"}), 400

    try:
        result = extract_notice_json(text)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500