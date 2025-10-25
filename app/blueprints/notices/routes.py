import json
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
        session.pop('message_to_send', None)

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
            message_to_send = get_session_value('message_to_send', default='')

        return render_template('notices/new_notices.html', origin_message=origin_message, key_info=key_info, message_to_send=message_to_send)

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
                
            # session 操作
            if 1 == 1:
                session['origin_message'] = origin_message
                session['key_info'] = pickle.dumps(key_info)
                session.pop('message_to_send', None)  # 清除之前生成的通知文本（如果有）
        
        elif form_get['method'] == "generate_notice":
            # 根据填入的数据，生成新的活动通知文本
            message_to_send = ""

            # 组织文本内容
            if 1 == 1:
                if form_get.get('tags'):
                    if form_get.get('tags') == 'activity':
                        message_to_send += f"【活动通知】\n"
                    elif form_get.get('tags') == 'course':
                        message_to_send += f"【课程通知】\n"
                if form_get.get('title'):
                    message_to_send += f"『{form_get.get('title')}』\n"

                order = 0
                if form_get.get('theme'):
                    order += 1
                    message_to_send += f"{order}. 主题：{form_get.get('theme')}\n"

                # 将时间信息处理为易读的字符串
                if form_get.get('start_date'):
                    start_datetime = _get_datetime_str(form_get.get('start_date'), form_get.get('start_time'))
                if form_get.get('end_date'):
                    end_datetime = _get_datetime_str(form_get.get('end_date'), form_get.get('end_time'))
                # 拼接时间信息
                order += 1
                if form_get.get('start_date') and form_get.get('end_date'):
                    message_to_send += f"{order}. 时间：{start_datetime} - {end_datetime}\n"
                elif form_get.get('start_date'):
                    message_to_send += f"{order}. 开始时间：{start_datetime}\n"
                else:
                    message_to_send += f"{order}. 时间：{form_get['raw_time_text']}\n"

                if form_get.get('location'):
                    order += 1
                    message_to_send += f"{order}. 地点：{form_get.get('location')}\n"

                if form_get.get('participants'):
                    order += 1
                    message_to_send += f"{order}. 参与人员：{form_get.get('participants')}\n"

                if form_get.get('organizer'):
                    order += 1
                    message_to_send += f"{order}. 组织者：{form_get.get('organizer')}\n"

                if form_get.get('contact'):
                    order += 1
                    message_to_send += f"{order}. 联系方式：{form_get.get('contact')}\n"

                if form_get.get('registration'):
                    order += 1
                    message_to_send += f"{order}. 报名方式：{form_get.get('registration')}\n"   

                if form_get.get('deadline_date') and form_get.get('deadline_time'):
                    order += 1
                    deadline_time = _get_datetime_str(form_get.get('deadline_date'), form_get.get('deadline_time'))
                    message_to_send += f"{order}. 报名截止时间：{deadline_time}\n"

                if form_get.get('details'):
                    order += 1
                    message_to_send += f"{order}. 详细说明：{form_get.get('details')}\n"

                if form_get.get('other_info'):
                    order += 1
                    message_to_send += f"{order}. 其他信息：{form_get.get('other_info')}\n"

            # 将文本上传至 session，供显示使用
            if 1 == 1:
                session['message_to_send'] = message_to_send

        return redirect(url_for('notices.new_notices'))


def _split_iso_datetime(iso_str: str):
    """
    将 ISO8601 时间字符串（如"2025-10-23T15:00:00+08:00"）拆分为 (YYYY-MM-DD, HH:MM)。
    解析失败返回 ("", "")。支持带 Z 的 UTC 标记。
    """

    # 预处理数据
    if 1 == 1:
        # 处理 None 或非字符串输入
        if not iso_str or not isinstance(iso_str, str):
            return "", ""
        s = iso_str.strip() # 去除首尾空白
        # 处理 UTC 标记
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

    # 解析并拆分为字符串
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


def _get_datetime_str(date: str, time: str) -> str:
    """
    根据 HTML 表单的日期和时间输入，生成可读性强的日期时间字符串。
    若仅有日期则返回仅含日期的字符串；若两者皆无则返回空字符串。
    """
    if date and time:
        date_list = date.split("-")
        time_list = time.split(":")
        date_now_year = datetime.now().year
        if date_list[0] == str(date_now_year):
            date = f"{int(date_list[1])}月{int(date_list[2])}日"
        else:
            date = f"{int(date_list[0])}年{int(date_list[1])}月{int(date_list[2])}日"
        time = f"{int(time_list[0])}:{int(time_list[1]):02d}"

        return f"{date} {time}"
    
    elif date:
        date_list = date.split("-")
        date_now_year = datetime.now().year
        if date_list[0] == str(date_now_year):
            date = f"{int(date_list[1])}月{int(date_list[2])}日"
        else:
            date = f"{int(date_list[0])}年{int(date_list[1])}月{int(date_list[2])}日"
        return date
    else:
        return ""
