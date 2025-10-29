from . import auth_bp

import pickle

from flask import render_template, request, session, redirect, url_for
from flask_login import current_user, logout_user

from models import User
from ext import db
from decorators import role_required
from common.flask_func import get_user_info


@auth_bp.route('/detail_info/', methods=['GET', 'POST'])
@role_required('User')
def detail_info():
    """展示用户的详细信息，并提供修改和退出登录功能"""

    """获取用户信息"""
    user_info = get_user_info()

    if request.method == 'GET':
        """根据session['whether_readonly']的值来标记只读状态"""
        if 1 == 1:
            if_readonly = 'readonly'
            if session['whether_readonly'] == 1:
                # 默认只读
                pass
            elif session['whether_readonly'] == 0:
                if_readonly = ''

        return render_template("auth/user_detail_info.html", **user_info, if_readonly=if_readonly)

    elif request.method == 'POST':
        form_get = request.form.to_dict()

        if form_get['method'] == 'logout':
            """取消登录状态"""
            logout_user()
            session['user_info'] = None

            return redirect("/home/")

        elif form_get['method'] == 'change_password':
            session['whether_hidden'] = 1
            return redirect(url_for('auth.change_password'))

        else:
            """通过“锁定”/“解锁”按钮，切换只读状态"""
            if form_get['method'] == 'unlock':
                session["whether_readonly"] = 0
            elif form_get['method'] == 'lock':
                session["whether_readonly"] = 1

            elif form_get['method'] == 'update':
                # 进行更新操作
                current_user.real_name = form_get['user_name']
                current_user.student_id = form_get['user_id']
                current_user.telephone = form_get['telephone']
                current_user.email = form_get['email']
                db.session.commit()

                # 标记锁定
                session["whether_readonly"] = 1

                """更新储存的数据"""
                if 1 == 1:
                    new_user_info = {
                        'user_id': current_user.student_id,  # 这里的 user_id 实际上为学号
                        'user_name': current_user.real_name,
                        'telephone': current_user.telephone,
                        'email': current_user.email,
                    }
                    # 更新 user_info 的值
                    user_info.update(new_user_info)

                    user_info_str = pickle.dumps(user_info)
                    session['user_info'] = user_info_str

            elif form_get['method'] == 'delete':
                if session['auth_to_delete'] == 0:
                    session['auth_to_delete'] = 1
                    return f"<script> alert('警告！你确定要注销账户吗？如果确定，请再次点击以注销。')" \
                           f";window.open('{ url_for('auth.detail_info') }');</script>"
                elif session['auth_to_delete'] == 1:
                    logout_user()
                    session['user_info'] = None

                    db.session.delete(current_user)
                    db.session.commit()
                    return "<script> alert('注销成功！');window.open('/home/');</script>"

            return redirect(url_for("auth.detail_info"))