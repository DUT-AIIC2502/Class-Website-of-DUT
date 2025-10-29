from . import auth_bp
from .helpers import captcha_time_to_wait

import time
import pickle
from flask import render_template, request, session, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash

from models import User, CAPTCHA
from ext import db
from common.flask_func import get_session_value, load_session_value



@auth_bp.route('/change_password/', methods=['GET', 'POST'])
def change_password():
    if request.method == 'GET':
        form_get_str = get_session_value('form_get')
        form_get = load_session_value(form_get_str, {})

        if get_session_value('whether_hidden') == 1:
            form_get['student_id'] = current_user.student_id

        return render_template('auth/change_password.html', **form_get, whether_hidden=session['whether_hidden'])

    elif request.method == 'POST':
        """获取表单提交的值，并保存至 session"""
        if 1 == 1:
            form_get = request.form.to_dict()

            """检查两次输入的密码一致"""
            if form_get['new_password'] != form_get['new_password_again']:
                form_get['new_password_again'] = ''
                return f"<script> alert('两次输入的密码不一致！')" \
                       f";window.open('{ url_for('auth.change_password') }');</script>"

            form_get_str = pickle.dumps(form_get)
            session['form_get'] = form_get_str

        if form_get['method'] == 'get_CAPTCHA':
            """创建新的一条验证码"""
            # 获取对应的用户
            user = User.query.filter(User.student_id == form_get['student_id']).first()

            new_captcha = CAPTCHA(user.id, user.real_name, 'change_password')
            db.session.add(new_captcha)
            db.session.commit()

            """储存验证码对应的 id"""
            session['captcha_id'] = new_captcha.id
            session['captcha_time_key'] = int(time.time())

            return f"<script> alert('已创建验证码！请联系管理员获取')" \
                   f";window.open('{ url_for('auth.change_password') }');</script>"

        elif form_get['method'] == 'confirm':
            wait = captcha_time_to_wait()
            if wait > 0:
                return f"<script> alert('请等待 {wait} 秒后再请求验证码！');" \
                       f"window.open('{url_for('auth.register')}');</script>"
            
            """检查验证码非空及正确"""
            if 1 == 1:
                if form_get['CAPTCHA'] in (None, ''):
                    return f"<script> alert('请输入验证码！')" \
                           f";window.open('{ url_for('auth.change_password') }');</script>"
                else:
                    captcha_id = get_session_value('captcha_id', 0)
                    # 从数据库中检索验证码
                    captcha = CAPTCHA.query.get(captcha_id)
                    if not captcha:
                        return f"<script> alert('验证码不存在，请重新获取！');window.history.back();</script>"

                    """验证验证码正确"""
                    if form_get['CAPTCHA'] == captcha.value:
                        """为密码加密"""
                        if 1 == 1:
                            new_password = form_get['new_password']
                            new_password_hash = generate_password_hash(
                                new_password,
                                method="pbkdf2:sha256",
                                salt_length=16
                            )

                        """将注册信息保存至数据库"""
                        if 1 == 1:
                            # 检索用户
                            user = User.query.filter(User.student_id == form_get['student_id']).first()
                            # 更新密码
                            user.password_hash = new_password_hash
                            db.session.commit()

                        """清空 session 相关数据"""
                        if 1 == 1:
                            session['form_get'] = None
                            session['captcha_id'] = None

                        return f"<script> alert('密码修改成功，请重新登录！')" \
                               f";window.open('{ url_for('auth.login') }');</script>"

                    else:
                        return f"<script> alert('验证码错误，请重新输入！')" \
                               f";window.open('{ url_for('auth.change_password') }');</script>"