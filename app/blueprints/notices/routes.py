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
            if key_info is not None:
                key_info = json.loads(key_info)

        return render_template('notices/new_notices.html', origin_message=origin_message, key_info=key_info)
    
    elif request.method == 'POST':
        form_get = request.form.to_dict()

        if form_get['method'] == "submit_origin_message":
            # 解析原始信息，提取关键信息
            if 1 == 1:
                origin_message = form_get.get('origin_message', '').strip()
                if origin_message:
                    try:
                        key_info = get_key_info(origin_message)
                        print("提取的关键信息：", key_info)
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


