from . import auth_bp
from .helpers import captcha_time_to_wait

import time
import pickle

from flask import render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from models import User, CAPTCHA, Role
from ext import db
from config import Config
from common.flask_func import get_session_value, load_session_value
from common.QQ_operation import send_private_msg


@auth_bp.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        form_get_str = get_session_value('form_get')
        form_get = load_session_value(form_get_str, {})

        return render_template('auth/register.html', **form_get)

    elif request.method == 'POST':
        """获取表单提交的值，并保存至 session"""
        if 1 == 1:
            form_get = request.form.to_dict()
            form_get_str = pickle.dumps(form_get)
            session['form_get'] = form_get_str


        if form_get['method'] == 'get_CAPTCHA':
            wait = captcha_time_to_wait()
            if wait > 0:
                return f"<script> alert('请等待 {wait} 秒后再请求验证码！');" \
                       f"window.history.back();</script>"
            
            # 检查学号是否已存在，若存在则提示并停止
            existing_user = User.query.filter(User.student_id == form_get['student_id']).first()
            if existing_user:
                return f"<script> alert('该学号已被注册！');window.history.back();</script>"

            # 获取或创建临时用户，以绑定验证码
            temporary_user = db.session.query(User).filter(User.real_name == "临时用户").first()
            if not temporary_user:
                # 创建临时用户
                temporary_user = User(
                    student_id="0",
                    real_name="临时用户",
                    password_hash="0"
                )
                db.session.add(temporary_user)
                db.session.commit()

            # 创建新的一条验证码
            new_captcha = CAPTCHA(temporary_user.id, form_get["name"], 'register')
            db.session.add(new_captcha)
            db.session.commit()

            # 将验证码信息发送到管理员QQ
            if 1 == 1:
                message_str = f"新用户注册验证码请求：\n姓名：{form_get['name']}\n学号：{form_get['student_id']}\n验证码：{new_captcha.value}\n请尽快联系该用户完成注册。"
                message = [
                    {
                        "type": "text",
                        "data": {
                            "text": message_str
                        }
                    }
                ]
                send_private_msg(Config.ADMIN_QQ, message)

            # 将验证码存储到数据库后，更新 session 中的相关键值
            if 1 == 1:
                # 储存验证码对应的 id: int
                session['captcha_id'] = new_captcha.id
                # 记录发送时间，防止 1 分钟内重复发送
                session['captcha_time_key'] = int(time.time())

            return "<script> alert('已创建验证码！请联系管理员获取');window.history.back();</script>"


        elif form_get['method'] == 'register':
            if form_get['CAPTCHA'] in (None, ''):
                return "<script> alert('请输入验证码！');window.history.back();</script>"

            # 获取验证码 id 并从数据库中检索
            captcha_id = session.pop('captcha_id', 0)
            captcha = CAPTCHA.query.get(captcha_id)
            if captcha_id == 0 or not captcha:
                return f"<script> alert('验证码不存在，请重新获取！');window.history.back();</script>"

            # 验证验证码正确
            if form_get['CAPTCHA'] == captcha.value:
                # 为密码加密
                password = form_get['password']
                password_hash = generate_password_hash(
                    password,
                    method="pbkdf2:sha256",
                    salt_length=16
                )

                # 创建新用户（已激活）
                if 1 == 1:
                    new_user = User(
                        student_id=form_get['student_id'],
                        real_name=form_get['name'],
                        password_hash=password_hash
                    )
                    new_user.status = 1  # 激活状态

                    # 将用户与 User 身份关联
                    role_user = Role.query.filter(Role.name == 'User').first()
                    new_user.add_role(role_user)
                    # 将用户与 Guest 身份关联
                    role_guest = Role.query.filter(Role.name == 'Guest').first()
                    new_user.add_role(role_guest)

                    db.session.add(new_user)
                    db.session.commit()

                # 清空 session 相关数据
                if 1 == 1:
                    session['form_get'] = None
                    session['captcha_id'] = None

                return f"<script> alert('注册成功！请进行登录。');" \
                        f"window.open('{ url_for('auth.login') }');</script>"

            else:
                return f"<script> alert('验证码错误，请重新输入！')" \
                        f";window.open('{url_for('auth.register')}');</script>"