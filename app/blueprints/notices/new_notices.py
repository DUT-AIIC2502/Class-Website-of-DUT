from . import notices_bp
from .helpers import _inject_datetime_inputs, _get_datetime_str

import json, pickle
from flask import render_template, request, session, g, url_for, redirect
from flask_login import current_user

from common.flask_func import get_session_value, load_session_value
from common.ai_func import get_key_info
from common.QQ_operation import send_group_msg


"""
使用到的 session 中的键：
- origin_message：原始活动通知文本
- key_info：提取的关键信息（pickle 序列化后的字典）
- message_to_send：生成的活动通知文本
"""


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
                    return "<script>alert('请输入活动通知文本！');window.history.back();</script>"
                
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

                # 处理时间信息
                if 1 == 1:
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
                    message_to_send += f"{order}. 详细说明：\n"
                    details_lines = form_get.get('details').strip().splitlines()
                    for line in details_lines:
                        message_to_send += f"        {line}\n"

                if form_get.get('other_info'):
                    order += 1
                    message_to_send += f"{order}. 其他信息：\n"
                    other_info_lines = form_get.get('other_info').strip().splitlines()
                    for line in other_info_lines:
                        message_to_send += f"        {line}\n"

            # 将文本上传至 session，供显示使用
            if 1 == 1:
                session['message_to_send'] = message_to_send

        elif form_get['method'] == 'publish_notice':
            group_id = form_get['group']

            message_str = form_get['preview']
            user = current_user.real_name if current_user.is_authenticated else "匿名用户"
            message_str = f"【来自：{user}】{message_str}"
            message_dict = [
                {
                    "type": "text",
                    "data": {
                        "text": message_str,
                    }
                }
            ]

            status = json.loads(send_group_msg(group_id, message_dict))
            print("发送状态：", status)

            if status.get("status") == "success":
                # 清理 session 中的键
                session.pop('origin_message', None)
                session.pop('key_info', None)
                session.pop('message_to_send', None)

                return f"<script>alert('活动通知已发送！');window.location.href='{url_for('notices.home')}';</script>"
            else:
                return f"<script>alert('发送失败：{status.get('data')}');window.open('{url_for('notices.new_notices')}');</script>"

        return redirect(url_for('notices.new_notices'))
