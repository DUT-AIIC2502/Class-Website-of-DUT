from . import main_bp

import traceback
from flask import request, session, g, current_app, url_for
from sqlalchemy import text

from ext import db
from models import Logs
from config import Config
from common.flask_func import get_user_info, get_services


def setup_app_hooks(state):
    """
    这个函数将在蓝图被注册到应用时调用。
    在这里，我们可以为 app 添加钩子。
    :param state:
    :return:
    """
    app = state.app

    """
    以下函数用于记录日志
    """


    @app.before_request
    def before():
        """
        在每个请求之前执行
        1. 检查会话是否过期
        2. 初始化 g.new_log 和 g.param 以供后续使用
        3. 记录请求的基本信息
        """
        # 检查会话是否过期
        if "/home/" in request.url or "/auth/" in request.url or "/static/" in request.url:
            # 允许无条件访问这些路径
            pass
        else:
            # 检查会话是否过期，如果过期，清理会话
            keep_keys = ('captcha_id', 'captcha_time_key', 'form_get', 'user_id', 'table_name')
            has_keep_key = any(session.get(k) is not None for k in keep_keys)
            if not has_keep_key:
                session.clear()  # 关键：清除遗留的会话数据
                return f"<script>alert('会话已过期，请重新登录。');window.open('{ url_for('main.home') }','_top');</script>"

        # 初始化日志对象和参数字典，排除静态文件请求
        if 'statics' not in request.url:
            g.new_log = Logs()  # 初始化日志对象
            g.param = {}        # 初始化参数字典
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
        """
        正常请求处理完成后执行
        1. 设置响应头以防止缓存
        2. 更新日志级别为 Info（如果不是 Error）
        3. 记录会话信息和操作参数
        """
        # 禁止缓存，防止浏览器展示过期页面中的旧用户信息
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        # 如果 g.new_log 不存在直接返回
        if not getattr(g, 'new_log', None):
            return response

        # 只有在 teardown 没把级别设为 Error 时才设为 Info
        if getattr(g.new_log, 'level', None) != 'Error':
            g.new_log.level = 'Info'

        # 记录 session 中的信息与操作参数
        session_dict = dict(session)
        my_session_dict = {k: v for k, v in session_dict.items() if isinstance(k, str) and not k.startswith('_')}

        g.param['session'] = my_session_dict
        g.new_log.oper_param = str(g.param)

        # 尝试保存日志，发生异常则回滚但不抛出
        try:
            db.session.add(g.new_log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return response

    @app.teardown_request
    def teardown(exc):
        """
        请求结束时捕获异常并记录完整堆栈。
        teardown 在 after_request 之后运行；如果发生异常，在这里设置 level 和 error_msg 并尝试保存。
        """
        if exc is not None:
            # 确保 g.new_log 存在
            if not getattr(g, 'new_log', None):
                g.new_log = Logs()

            g.new_log.level = 'Error'

            """捕获异常信息"""
            if 1 == 1:
                # 获取完整堆栈信息和简短描述
                full_trace = traceback.format_exc()
                short_desc = f"{type(exc).__name__}: {str(exc)}"

                # # 将异常信息放入 oper_param 里便于查询（可选）
                # g.param.setdefault('exception', {})['short'] = short_desc
                # g.param.setdefault('exception', {})['traceback'] = full_trace
                # g.new_log.oper_param = str(g.param)

                # models.Logs 字段名为 error_msg，务必使用正确字段
                g.new_log.error_full_trace = full_trace
                g.new_log.error_short_desc = short_desc

            # 尝试保存日志（安全提交/回滚）
            try:
                db.session.add(g.new_log)
                db.session.commit()
            except Exception:
                db.session.rollback()

        else:
            print("请求正常执行。")

    @app.context_processor
    def inject_global_params():
        """
        在模板中注入全局变量 services 和 user_info
        """
        if db:
            result_services = db.session.execute(text(
                f"""
                SELECT 1 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = '{Config.DATABASE}'
                  AND TABLE_NAME = 'services'
                """
            )).first()

            result_user_info = db.session.execute(text(
                f"""
                SELECT 1 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = '{Config.DATABASE}'
                  AND TABLE_NAME = 'users'
                """
            )).first()

            if result_services is not None:
                services = get_services()
            else:
                services = {}

            if result_user_info is not None:
                # 仅在已登录时返回用户信息
                if session.get('user_id'):
                    user_info = get_user_info()
                else:
                    user_info = {}
            else:
                user_info = {}
        else:
            services = {}
            user_info = {}

        return {
            "services": services,
            "user_info": user_info
        }


# --- 在蓝图上记录这个设置函数 ---
# record_once 确保 setup_app_hooks 只被执行一次，即使蓝图在测试等场景中可能被多次注册
main_bp.record_once(setup_app_hooks)


def get_current_view_function_name():
    """
    获取当前视图函数的名称
    """
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