import sys
import traceback
import datetime

from flask import Blueprint, redirect, render_template, session, request, jsonify, g, current_app
from sqlalchemy import inspect

import models
from ext import db, aps
from functions import get_user_info
from models import Role, Permission, Logs, ScheduleFunctions, NavbarUrls

main_bp = Blueprint('main', __name__,
                    template_folder='templates')


def setup_app_hooks(state):
    """
        这个函数将在蓝图被注册到应用时调用。
        在这里，我们可以为 app 添加钩子。
    """
    app = state.app

    def get_current_view_function_name():
        # 1. 获取请求的 URL 规则
        # request.url_rule 会返回一个 Rule 对象，其中包含了端点信息
        rule = request.url_rule
        if not rule:
            return None  # 可能是在处理 404 等情况

        # 2. 从规则中获取端点 (endpoint)
        endpoint = rule.endpoint

        # 3. 通过端点从视图函数映射中获取函数对象
        # current_app.view_functions 是一个 {endpoint: function} 的字典
        view_function = current_app.view_functions.get(endpoint)

        if view_function:
            # 4. 返回函数的名称
            return view_function.__name__
        else:
            return endpoint  # 如果找不到函数，至少返回端点名称作为 fallback

    @app.before_request
    def before():
        g.new_log = Logs()
        g.param = {}
        if request:
            # 请求信息
            g.new_log.req_method = request.method
            g.new_log.req_url = request.url
            g.new_log.req_ip_adress = request.remote_addr
            # 获取视图函数名
            g.new_log.oper_function = get_current_view_function_name()
            # 获取表单提交数据
            form_get = request.form.to_dict()
            g.param['form_get'] = form_get
            g.new_log.oper_param = str(g.param)

    @app.after_request
    def after(response):
        """正常请求处理完成后执行"""
        """记录日志"""
        g.new_log.level = 'Info'

        # 记录 session 中的信息
        session_dict = dict(session)
        my_session_dict = {k: v for k, v in session_dict.items() if not k.startswith('_')}

        g.param['session'] = my_session_dict
        g.new_log.oper_param = str(g.param)

        """保存日志"""
        db.session.add(g.new_log)
        db.session.commit()

        return response

    @app.teardown_request
    def teardown(exc):
        if exc is not None:
            g.new_log.level = 'Error'

            """捕获异常信息"""
            if 1 == 1:
                # 使用 sys.exc_info() 获取更详细的异常信息
                # exc_type: 异常类型 (e.g., ValueError)
                # exc_value: 异常实例 (与 exc 参数相同)
                # exc_traceback: 回溯对象
                exc_type, exc_value, exc_traceback = sys.exc_info()

                # 使用 traceback.format_exception() 将异常信息格式化为字符串列表
                # 每个元素是一行，包含了完整的堆栈信息
                error_details_list = traceback.format_exception(exc_type, exc_value, exc_traceback)

                # 将列表拼接成一个完整的字符串
                full_error_string = "".join(error_details_list)

                # 保存至日志
                g.new_log.error_mag = full_error_string

            """保存日志"""
            db.session.add(g.new_log)
            db.session.commit()

        else:
            print("请求正常执行。")


# --- 在蓝图上记录这个设置函数 ---
# record_once 确保 setup_app_hooks 只被执行一次，即使蓝图被多次注册（在测试等场景中可能发生）
main_bp.record_once(setup_app_hooks)


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

    # inspector = inspect(db.engine)
    """插入初始角色"""
    if Role.query.first() is None:
        role_list = [
            {'name': 'Root', 'description': '超级管理员'},
            {'name': 'Admin', 'description': '管理员'},
            {'name': 'User', 'description': '用户'},
            {'name': 'Guest', 'description': '访客'}
        ]

        db.session.bulk_insert_mappings(Role, role_list)
        db.session.commit()

    """插入权限"""
    if Permission.query.first() is None:
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

    if ScheduleFunctions.query.first() is None:
        print('插入定时任务列表')
        function_list = [
            {'func_id': 'check_time', 'func': 'app.blueprints.main.routes:check_time', 'args': '',
             'f_trigger': 'interval', 'f_time': '0, 0, 10'},
        ]

        db.session.bulk_insert_mappings(ScheduleFunctions, function_list)
        db.session.commit()

    if NavbarUrls.query.first() is None:
        navbar_urls_list = [
            {'url': '/info_management/', 'name': '信息管理'},
        ]

        db.session.bulk_insert_mappings(NavbarUrls, navbar_urls_list)
        db.session.commit()

    return "数据库表创建成功！插入初始 Role 成功！"


@main_bp.route('/drop_tables/')
def drop_tables():
    db.drop_all()
    return "数据库表删除成功！"


@main_bp.route('/jobs')
def list_jobs():
    """查看所有已添加的定时任务"""
    jobs = aps.get_jobs()  # 获取调度器中的所有任务
    if not jobs:
        return jsonify({"status": "error", "msg": "没有任何任务被添加到调度器"}), 400

    # 整理任务信息（重点看 id、func、next_run_time）
    job_list = []
    for job in jobs:
        job_list.append({
            "job_id": job.id,
            "func_path": job.func_ref,  # 函数路径（确认是否是你要的函数）
            "trigger_type": str(job.trigger),  # 触发器类型（interval/cron）
            "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "无"  # 下次执行时间
        })
    return jsonify({"status": "success", "jobs": job_list})


# @aps.task('interval', id='check_time', seconds=5)
def check_time():
    print("API调用定时任务开始执行时间：{}".format(datetime.datetime.now()))
    print("定时任务 'check_time' 正在执行...")
