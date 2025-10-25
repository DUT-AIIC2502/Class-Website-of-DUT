import os
import json
import re
import httpx
import pickle
from datetime import datetime

from flask import Blueprint, request, redirect, render_template, jsonify, session, url_for
from pydantic import BaseModel, Field  # 修正：补充 Field 导入
from dotenv import load_dotenv
from typing import Optional

from common.flask_func import get_session_value, load_session_value
from common.ai_func import get_key_info

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
    # 清理 session 中的数据
    if 1 == 1:
        session.pop('origin_message', None)
        session.pop('key_info', None)

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
                        key_info = get_key_info(origin_message) # json
                        key_info = json.loads(key_info)         # dict
                        print("提取的关键信息：", key_info)
                        # 注入表单可用的日期/时间字段
                        key_info = _inject_datetime_inputs(key_info)
                    except Exception as e:
                        return f"<script>alert('解析超时或失败，请稍后重试（{type(e).__name__}）。');window.history.back();</script>"
                else:
                    return f"<script>alert('请输入活动通知文本！');window.history.back();</script>"
                
            # 存入 session
            if 1 == 1:
                session['origin_message'] = origin_message
                session['key_info'] = pickle.dumps(key_info)
        
        elif form_get['method'] == "generate_notice":
            # 读取 session 中的关键信息
            if 1 == 1:
                key_info = load_session_value(get_session_value('key_info', default={}))

            # 通过 key_info 生成通知
            if 1 == 1:
                notice_str = ""
                order = 0
                for key, value in key_info.items():
                    order += 1
                    if isinstance(value, str) and value.strip():
                        if key == "details" or key == "notes":
                            lines = value.strip().splitlines()
                            notice_str += f"{order}. {key}:\n"
                            for line in lines:
                                notice_str += f"    {line.strip()}\n"
                        else:
                            notice_str += f"{order}. {key}: {value}\n"
                print("生成的通知内容：", notice_str)

        return redirect(url_for('notices.new_notices'))


def _split_iso_datetime(iso_str: str):
    """
    将 ISO8601 时间字符串拆分为 (YYYY-MM-DD, HH:MM)。
    解析失败返回 ("", "")。支持带 Z 的 UTC 标记。
    """
    if not iso_str or not isinstance(iso_str, str):
        return "", ""
    s = iso_str.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        return dt.date().isoformat(), dt.strftime("%H:%M")
    except Exception:
        # 如果是只有日期的情形
        try:
            d = datetime.fromisoformat(s + "T00:00:00").date()
            return d.isoformat(), ""
        except Exception:
            return "", ""


def _inject_datetime_inputs(key_info: dict) -> dict:
    """
    在 key_info 中注入 HTML 表单可直接使用的日期/时间字段：
    - start_date_input, start_time_input
    - end_date_input, end_time_input
    - deadline_date_input, deadline_time_input
    """
    ki = dict(key_info or {})
    sd, st = _split_iso_datetime(ki.get("start_time"))
    ed, et = _split_iso_datetime(ki.get("end_time"))
    dd, dtm = _split_iso_datetime(ki.get("deadline"))
    ki["start_date_input"], ki["start_time_input"] = sd, st
    ki["end_date_input"], ki["end_time_input"] = ed, et
    ki["deadline_date_input"], ki["deadline_time_input"] = dd, dtm
    return ki