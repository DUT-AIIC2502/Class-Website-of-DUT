"""注册界面蓝图"""
from flask import Blueprint, request, redirect, render_template, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import re

from models import User, Role, LoginLogs
from ext import db
from functions import get_session_value, load_session_value
from decorators import permission_required, role_required

auth_bp = Blueprint('auth', __name__,
                    url_prefix='/auth',
                    template_folder='templates')


@auth_bp.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        form_get = request.form.to_dict()

        """验证用户是否存在"""
        if 1 == 1:
            user_id = form_get['student_id']
            # 从数据库中检索用户对象
            retrieved_user = User.query.filter_by(student_id=user_id).first()
            """验证数据库中存在该用户，并读取需要的信息"""
            if retrieved_user:
                password_hash = retrieved_user.password_hash
            else:
                return f"<script> alert('不存在该用户！');window.open('{ url_for('auth.login') }');</script>"

        """验证密码是否正确，更新登录状态"""
        if 1 == 1:
            password = form_get['password']
            is_value = check_password_hash(password_hash, password)

            if not is_value:
                return f"<script> alert('密码错误！请重新输入。');window.open('{ url_for('auth.login') }');</script>"

            # 登录用户，'remember=True' 实现“记住我”功能, 这会将会话信息写入浏览器
            login_user(retrieved_user, remember=True)

        """登录成功后，将用户信息集成为字典，并上传至session"""
        if 1 == 1:
            # user所对应的角色，是一个一维list
            user_roles = [role.name for role in retrieved_user.roles]

            """确定用户的最高级身份，用于展示"""
            user_top_role = get_top_role(user_roles)

            user_info = {
                'id': retrieved_user.id,
                'user_id': user_id,  # 这里的 user_id 实际上为学号
                'user_name': retrieved_user.real_name,
                'telephone': retrieved_user.telephone,
                'email': retrieved_user.email,
                'create_time': retrieved_user.create_time,
                'status': retrieved_user.status,
                'user_top_role': user_top_role,
                'user_roles': user_roles
            }

            user_info_str = pickle.dumps(user_info)
            session['user_info'] = user_info_str

        """更新登录日志"""
        if 1 == 1:
            new_login_logs = LoginLogs(
                user_id=retrieved_user.id,
                ip_address=request.remote_addr
            )
            db.session.add(new_login_logs)
            db.session.commit()

        return redirect("/home/")


@auth_bp.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    elif request.method == 'POST':
        form_get = request.form.to_dict()

        """为密码加密"""
        if 1 == 1:
            password = form_get['password']
            password_hash = generate_password_hash(
                password,
                method="pbkdf2:sha256",
                salt_length=16
            )

        """将注册信息保存至数据库"""
        if 1 == 1:
            # 记录用户的基本信息
            new_user = User(
                student_id=int(form_get['student_id']),
                real_name=form_get['name'],
                password_hash=password_hash
            )

            # 将用户与User身份关联
            role_user = Role.query.filter(Role.name == 'User').first()
            new_user.add_role(role_user)

            role_guest = Role.query.filter(Role.name == 'Guest').first()
            new_user.add_role(role_guest)

            db.session.add(new_user)
            db.session.commit()

        return f"<script> alert('注册成功！请进行登录。');window.open('{ url_for('auth.login') }');</script>"


# @permission_required('user_view_detail', 'role_delete')
@auth_bp.route('/detail_info/', methods=['GET', 'POST'])
@role_required('User')
def detail_info():
    """展示用户的详细信息，并提供修改和退出登录功能"""

    """获取session中的用户信息"""
    if 1 == 1:
        user_info_str = get_session_value('user_info')
        user_info = load_session_value(user_info_str, {})

    if request.method == 'GET':
        """根据session['whether_readonly']的值来标记只读状态"""
        if 1 == 1:
            if_readonly = 'readonly'
            if session['whether_readonly'] == 1:
                # 默认只读
                pass
            elif session['whether_readonly'] == 0:
                if_readonly = ''

        return render_template("detail_info.html", **user_info, if_readonly=if_readonly)

    elif request.method == 'POST':
        form_get = request.form.to_dict()

        if form_get['method'] == 'logout':
            """取消登录状态"""
            logout_user()
            session['user_info'] = None

            return redirect("/home/")

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
                    db.session.delete(current_user)
                    db.session.commit()
                    return "<script> alert('注销成功！');window.open('/home/');</script>"

            return redirect(url_for("auth.detail_info"))


@auth_bp.route('/user_management/', methods=['GET', 'POST'])
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

        return render_template('user_management.html', all_list=all_list)

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


def get_top_role(user_roles):
    user_level = {
        "Root": 4,
        "Admin": 3,
        "User": 2,
        "Guest": 1
    }

    # 使用 max() 和 key 参数来找到最重要的任务
    # key=lambda task: user_level[task] 的意思是：
    # 对于 todo_list 中的每一个 task（任务），
    # 使用 user_level[task] 得到它的重要性数值，
    # 然后 max() 函数就根据这些数值进行比较。
    return max(user_roles, key=lambda task: user_level[task])