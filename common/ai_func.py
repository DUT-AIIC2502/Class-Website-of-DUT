import os
import re
import json
import requests
import httpx
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 轻量预处理，省 token
def _prep_text(text: str, max_chars: int = 10000) -> str:
    if not text:
        return ""
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f]', '', text)  # 零宽
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)  # 压缩空行
    return text[:max_chars].strip()

# 提取时间候选片段，帮助模型“看到”关键信息（少量，省 token）
_TIME_PATTERNS = [
    r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}日?(?:（[^）]*）)?(?:\s*(?:上午|下午|晚|晚上|中午))?\s*\d{1,2}(?::|：)?\d{0,2}(?:\s*[-~至到]\s*\d{1,2}(?::|：)?\d{0,2})?',
    r'\d{1,2}月\d{1,2}日(?:（[^）]*）)?(?:\s*(?:上午|下午|晚|晚上|中午))?\s*\d{1,2}(?::|：)?\d{0,2}(?:\s*[-~至到]\s*\d{1,2}(?::|：)?\d{0,2})?',
    r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}日?',
    r'\d{1,2}月\d{1,2}日',
    r'\d{1,2}:\d{2}\s*[-~至到]\s*\d{1,2}:\d{2}',
    r'(?:上午|下午|晚|晚上|中午)\s*\d{1,2}(?::|：)?\d{0,2}',
]
def _extract_time_candidates(text: str, limit: int = 6) -> list[str]:
    seen = set()
    out = []
    for pat in _TIME_PATTERNS:
        for m in re.finditer(pat, text):
            s = m.group(0)
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
            if len(out) >= limit:
                return out
    return out

# 简单兜底：从原文用正则解析第一个起止时间，转 ISO8601（+08:00）
def _fallback_parse_times(text: str) -> tuple[str | None, str | None, str | None]:
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    curr_year = now.year

    def mk_iso(y, mo, d, h=None, mi=None):
        try:
            if h is None:
                # 仅日期：返回 YYYY-MM-DD
                return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
            dt = datetime(int(y), int(mo), int(d), int(h or 0), int(mi or 0), tzinfo=tz)
            return dt.isoformat()
        except Exception:
            return None

    # 1) 年月日 + 时间（可区间）
    m = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?(?:（[^）]*）)?\s*(上午|下午|晚|晚上|中午)?\s*(\d{1,2})(?::|：)?(\d{2})?(?:\s*[-~至到]\s*(\d{1,2})(?::|：)?(\d{2})?)?', text)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        period = m.group(4) or ''
        sh, sm, eh, em = m.group(5), m.group(6), m.group(7), m.group(8)
        def adj(h, per):
            if h is None: return None
            h = int(h)
            if per in ('下午', '晚上', '晚') and h < 12: h += 12
            return h
        sh = adj(sh, period); eh = adj(eh, period)
        start_iso = mk_iso(y, mo, d, sh, sm or 0)
        end_iso = mk_iso(y, mo, d, eh, em or 0) if eh is not None else None
        return start_iso, end_iso, m.group(0)

    # 2) 月日 + 时间（可区间），年份缺省用当年
    m = re.search(r'(\d{1,2})月(\d{1,2})日(?:（[^）]*）)?\s*(上午|下午|晚|晚上|中午)?\s*(\d{1,2})(?::|：)?(\d{2})?(?:\s*[-~至到]\s*(\d{1,2})(?::|：)?(\d{2})?)?', text)
    if m:
        mo, d = m.group(1), m.group(2)
        period = m.group(3) or ''
        sh, sm, eh, em = m.group(4), m.group(5), m.group(6), m.group(7)
        def adj(h, per):
            if h is None: return None
            h = int(h)
            if per in ('下午', '晚上', '晚') and h < 12: h += 12
            return h
        sh = adj(sh, period); eh = adj(eh, period)
        start_iso = mk_iso(curr_year, mo, d, sh, sm or 0)
        end_iso = mk_iso(curr_year, mo, d, eh, em or 0) if eh is not None else None
        return start_iso, end_iso, m.group(0)

    # 3) 仅年月日
    m = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?', text)
    if m:
        return mk_iso(m.group(1), m.group(2), m.group(3)), None, m.group(0)

    # 4) 仅月日
    m = re.search(r'(\d{1,2})月(\d{1,2})日', text)
    if m:
        return mk_iso(curr_year, m.group(1), m.group(2)), None, m.group(0)

    return None, None, None

def get_key_info(text: str) -> dict | str:
    """
    调用火山引擎的API，提取关键信息；若模型缺失 start_time，启用正则兜底。
    返回 JSON 字符串（与原有调用兼容），或字典（如你需要）。
    """
    # 环境变量
    base_url = os.getenv("VOLCENGINE_BASE_URL")
    api_key = os.getenv("VOLCENGINE_API_KEY")
    endpoint_id = os.getenv("VOLCENGINE_ENDPOINT_ID")

    # 初始化客户端
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        http_client=httpx.Client(
            timeout=30.0,
            trust_env=False,
        ),
    )

    # 输入预处理与时间候选
    text_prep = _prep_text(text, max_chars=10000)
    time_candidates = _extract_time_candidates(text_prep, limit=6)
    today = datetime.now(timezone(timedelta(hours=8))).date().isoformat()

    # 精准系统提示（短且明确）
    system_prompt = (
        "你是信息抽取助手。仅从给定中文活动通知中抽取“第一个活动”的关键信息，并严格输出一个 JSON 对象。"
        "字段："
        'title(字符串)、theme(字符串或空)、'
        'start_time(ISO 8601，如"2025-10-23T15:00:00+08:00"或仅日期)、'
        'end_time(ISO 8601或null)、'
        'raw_time_text(字符串或null)、notes(字符串或null)、'
        'location(字符串或null)、participants(字符串或null，如“全体同学”)、'
        'organizer(字符串或null)、contact(字符串或null)、'
        'registration(字符串或null，如“到梦空间报名”、“班长处报名”)、'
        'details(字符串，使用多行，以"- "作为每行起始)。'
        "规则："
        "1) 只输出 JSON，无解释；"
        "2) 仅提取原文按出现顺序的第一个活动；"
        "3) 出现时间范围如“15:00-16:00”，start_time 用开始，end_time 用结束；"
        "4) 仅日期也可作为 start_time（用 YYYY-MM-DD）；"
        "5) 有‘上午/下午/晚上’需换算 24 小时制；"
        "6) 缺失字段置空字符串或 null；"
        "7) 时区统一 +08:00。"
        "8) details字段的内容应不与其他字段重复，且包含除已有字段外所有重要信息（尤其是注意事项）。"
    )

    # 加入当前日期和候选片段，帮助时间解析（省流控制在少量字符）
    candidates_str = ""
    if time_candidates:
        candidates_str = "候选时间片段（供参考，若矛盾以原文为准）:\n- " + "\n- ".join(time_candidates) + "\n"

    user_prompt = (
        f"当前日期（用于解析‘本周三/本月/本周五下午’等相对描述）：{today}\n"
        f"{candidates_str}"
        "原文：\n"
        f"{text_prep}\n\n"
        "只输出 JSON，示例结构：\n"
        '{"title":"","theme":"","start_time":"","end_time":null,"location":null,"participants":null,'
        '"organizer":null,"contact":null,"registration":null,"raw_time_text":null,"notes":null,"details":""}'
    )

    # 发送请求（强制 JSON 输出，温度=0，低开销）
    kwargs = dict(
        model=endpoint_id,
        messages=[
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
        ],
        temperature=0,
        top_p=1,
        max_tokens=600,
    )
    try:
        completion = client.chat.completions.create(
            **kwargs,
            response_format={"type": "json_object"},
        )
    except Exception:
        completion = client.chat.completions.create(**kwargs)

    content = completion.choices[0].message.content

    # 解析为字典
    def _to_dict(s: str) -> dict:
        try:
            return json.loads(s)
        except Exception:
            m = re.search(r'\{[\s\S]*\}', s)
            return json.loads(m.group(0)) if m else {}

    data = _to_dict(content) or {}

    # 兜底：若模型未给出 start_time，则正则解析一次
    if not data.get("start_time"):
        s_iso, e_iso, raw_seg = _fallback_parse_times(text_prep)
        if s_iso:
            data["start_time"] = s_iso
        if e_iso and not data.get("end_time"):
            data["end_time"] = e_iso
        if raw_seg and not data.get("raw_time_text"):
            data["raw_time_text"] = raw_seg
        if not data.get("notes"):
            data["notes"] = "时间字段使用正则兜底解析"

    # 确保所有字段存在
    default_obj = {
        "title": "",
        "theme": "",
        "start_time": "",
        "end_time": None,
        "location": None,
        "participants": None,
        "organizer": None,
        "contact": None,
        "registration": None,
        "raw_time_text": None,
        "notes": None,
        "details": "",
    }
    for k, v in default_obj.items():
        data.setdefault(k, v)

    # 与现有调用兼容：返回 JSON 字符串（如需 dict，可直接返回 data）
    return json.dumps(data, ensure_ascii=False)