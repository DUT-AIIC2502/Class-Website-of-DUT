from flask import Blueprint, redirect, render_template, session, request
from sqlalchemy import inspect

import models
from ext import db
from functions import get_user_info
from models import Role, Permission

main_bp = Blueprint('main', __name__,
                    template_folder='templates')


@main_bp.route('/')
def main():
    return redirect('/home/', code=302, Response=None)


@main_bp.route('/home/')
def home():
    if 1 == 1:
        """获取用户信息"""
        user_info = get_user_info()

    """初始化某些数据"""
    if 1 == 1:
        # 表名
        session["table_name"] = "student_info"
        # 班级名
        session['class_name'] = '智创2502'
        # 标记用户详细信息页面只读
        session["whether_readonly"] = 1
        # 标记注销归零
        session['auth_to_delete'] = 0

    # 清除某些记录
    if 1 == 1:
        session['info_management_select_form_data'] = None
        session['form_get'] = None
        session['page_current'] = None
        session['page_number'] = None

    return render_template('home.html', **user_info)


@main_bp.route('/create_tables/')
def create_tables():
    db.create_all()

    inspector = inspect(db.engine)
    """插入初始角色"""
    if not inspector.has_table(Role.__tablename__):
        role_list = [
            {'name': 'Root', 'description': '超级管理员'},
            {'name': 'Admin', 'description': '管理员'},
            {'name': 'User', 'description': '用户'},
            {'name': 'Guest', 'description': '访客'}
        ]

        db.session.bulk_insert_mappings(Role, role_list)
        db.session.commit()

    """插入权限"""
    if not inspector.has_table(Permission.__tablename__):
        permission_list = [
            {'name': '创建新用户', 'code': 'user_create', 'classification': 'management'},
            {'name': '编辑用户信息', 'code': 'user_edit', 'classification': 'management'},
            {'name': '删除用户', 'code': 'user_delete', 'classification': 'management'},
            {'name': '查看用户列表', 'code': 'user_view', 'classification': 'management'},
            {'name': '查看用户详细信息', 'code': 'user_view_detail', 'classification': 'management'},
            {'name': '创建新角色', 'code': 'role_create', 'classification': 'management'},
            {'name': '编辑角色信息和权限', 'code': 'role_edit', 'classification': 'management'},
            {'name': '删除角色', 'code': 'role_delete', 'classification': 'management'},
            {'name': '分配角色', 'code': 'role_assign', 'classification': 'management',
             'description': '将角色分配给用户或从用户移除角色'},
            {'name': '管理权限本身', 'code': 'permission_manage', 'classification': 'management',
             'description': '通常只有超级管理员拥有'},
            {'name': '修改系统全局配置', 'code': 'system_config_edit', 'classification': 'management'},
            {'name': '查看系统日志', 'code': 'log_view', 'classification': 'management'},
        ]

        db.session.bulk_insert_mappings(Permission, permission_list)
        db.session.commit()
    return "数据库表创建成功！插入初始 Role 成功！"


@main_bp.route('/drop_tables/')
def drop_tables():
    db.drop_all()
    return "数据库表删除成功！"
