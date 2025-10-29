from . import auth_bp
from .helpers import get_top_role

import re
from flask import render_template, request, session, redirect, url_for

from models import User, Role
from ext import db
from decorators import role_required


@auth_bp.route('/user_management/', methods=['GET', 'POST'])
@role_required('User', 'Root')
def user_management():
    if request.method == 'GET':
        all_users = User.query.all()
        # 生成展示序列
        roots_list = []
        admins_list = []
        users_list = []
        guests_list = []
        for user in all_users:
            user_roles = [role.name for role in user.roles]
            user_top_role = get_top_role(user_roles)
            new_list = [user.real_name, user.student_id, user_top_role, user.status]
            if user_top_role == 'Root':
                roots_list.append(new_list)
            elif user_top_role == 'Admin':
                admins_list.append(new_list)
            elif user_top_role == 'User':
                users_list.append(new_list)
            elif user_top_role == 'Guest':
                guests_list.append(new_list)

        all_list = [roots_list, admins_list, users_list, guests_list]

        return render_template('auth/user_management.html', all_list=all_list)

    elif request.method == 'POST':
        form_get = request.form.to_dict()

        if form_get['method'] in ('insert_user', 'delete_choose'):

            if form_get['method'] == 'insert_user':
                pass

            elif form_get['method'] == 'delete_choose':
                pass

        else:
            # 根据学号，查找该用户信息
            student_id = re.findall(r'\d+', form_get['method'])
            user = User.query.filter_by(student_id=student_id).first()

            # 获取最高身份
            user_roles = [role.name for role in user.roles]
            user_top_role = get_top_role(user_roles)

            """验证数据库中存在该用户"""
            if not user:
                return f"<script> alert('不存在该用户！');window.open('{url_for('auth.login')}');</script>"

            """获取角色对象"""
            if 1 == 1:
                role_root = Role.query.filter(Role.name == 'Root').first()
                role_admin = Role.query.filter(Role.name == 'Admin').first()
                role_user = Role.query.filter(Role.name == 'User').first()
                role_guest = Role.query.filter(Role.name == 'Guest').first()

            if 'upgrade' in form_get['method']:
                """角色升级"""
                if user_top_role == 'Admin':
                    user.add_role(role_root)
                elif user_top_role == 'User':
                    user.add_role(role_admin)
                elif user_top_role == 'Guest':
                    user.add_role(role_user)

            elif 'downgrade' in form_get['method']:
                """角色降级"""
                if user_top_role == 'Root':
                    user.remove_role(role_root)
                elif user_top_role == 'Admin':
                    user.remove_role(role_admin)
                elif user_top_role == 'User':
                    user.remove_role(role_user)

            elif 'delete' in form_get['method']:
                db.session.delete(user)

            db.session.commit()

            return redirect(url_for('auth.user_management'))