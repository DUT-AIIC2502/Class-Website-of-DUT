from . import auth_bp

from flask import render_template, request, redirect, session
from flask_login import login_user
from werkzeug.security import check_password_hash

from models import User, LoginLogs
from ext import db


@auth_bp.route('/login/', methods=['GET', 'POST'])
def login():
    # 初始化 session 中的值
    session['whether_hidden'] = 0

    if request.method == 'GET':
        return render_template('auth/login.html')

    elif request.method == 'POST':
        form_get = request.form.to_dict()

        # 验证用户是否存在
        if 1 == 1:
            # 根据学号，从数据库中检索用户对象
            user_id = form_get['student_id']
            retrieved_user = User.query.filter_by(student_id=user_id).first()

            # 验证数据库中存在该用户，并读取需要的信息
            if retrieved_user:
                password_hash = retrieved_user.password_hash+""
            else:
                return f"<script> alert('不存在该用户！');" \
                       f"window.history.back();</script>"

        # 验证用户是否激活
        if int(retrieved_user.status) == 0:
            return "<script> alert('该用户还未激活！');window.open('/home/‘);</script>"

        # 验证密码是否正确，更新登录状态
        if 1 == 1:
            password = form_get['password']
            is_value = check_password_hash(password_hash, password)

            if not is_value:
                return f"<script> alert('密码错误！请重新输入。');window.history.back();</script>"

            # 登录用户，'remember=True' 实现“记住我”功能, 这会将会话信息写入浏览器
            login_user(retrieved_user, remember=True)
            session['user_id'] = retrieved_user.student_id

        # 更新登录日志
        if 1 == 1:
            new_login_logs = LoginLogs(
                user_id=retrieved_user.id,
                ip_address=request.remote_addr
            )
            db.session.add(new_login_logs)
            db.session.commit()

        # 清空 session 相关数据
        if 1 == 1:
            session['form_get'] = None
            session['captcha_id'] = None

        return redirect("/home/")
    


