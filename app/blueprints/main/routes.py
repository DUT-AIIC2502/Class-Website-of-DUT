import sys
import traceback
import datetime

from flask import Blueprint, redirect, render_template, session, request, jsonify, g, current_app, send_file
from io import BytesIO  # 用于将二进制数据转换为文件流
from pathlib import Path
from sqlalchemy import text

from ext import db, aps
from common.flask_func import get_user_info, get_services
from models import Role, Permission, Logs, ScheduleFunctions, Services
from config import Config

main_bp = Blueprint('main', __name__,
                    template_folder='templates')


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
        my_session_dict = {k: v for k, v in session_dict.items() if isinstance(k, str) and not k.startswith('_')}

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

    """
    以下函数用来渲染模板
    """

    @app.context_processor
    def inject_global_params():
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
                user_info = get_user_info()
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


@main_bp.route('/')
def main():
    return redirect('/create_tables/')


@main_bp.route('/home/')
def home():
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

    return render_template('main/home.html')


@main_bp.route('/create_tables/')
def create_tables():
    """创建数据库中的表"""
    def execute_sql_file_mysql(sql_file_path):
        """
        执行 mysql 命令
        :param sql_file_path: sql 文件路径
        :return:
        """

        # 1. 读取.sql文件并处理（拆分语句，过滤空行和注释）
        sql_content = Path(sql_file_path).read_text(encoding='utf-8')
        # 按分号拆分语句（简单处理，复杂场景需优化）
        sql_statements = [
            stmt.strip() for stmt in sql_content.split(';')
            if stmt.strip() and not stmt.strip().startswith('--')
        ]

        # 3. 逐条执行SQL语句
        for stmt in sql_statements:
            db.session.execute(text(stmt))
        # 4. 提交事务
        db.session.commit()
        print(f"SQL文件 {sql_file_path} 执行成功")

    """插入初始角色"""
    if Role.query.first() is None:
        execute_sql_file_mysql('static/data/roles.sql')

    """插入权限"""
    if Permission.query.first() is None:
        execute_sql_file_mysql('static/data/permissions.sql')

    if ScheduleFunctions.query.first() is None:
        execute_sql_file_mysql('static/data/schedule_functions.sql')

    if Services.query.first() is None:
        execute_sql_file_mysql('static/data/services.sql')

    return redirect('/home/')


@main_bp.route('/icon/<int:image_id>')
def get_icon(image_id):
    """
    这是关键的路由！
    它根据提供的 image_id 从数据库中获取图片数据，
    并将其作为图片文件发送给浏览器。
    """
    # 从数据库中查询指定 ID 的图片
    service = Services.query.get_or_404(image_id)

    # 使用 send_file 函数发送图片数据
    # BytesIO(image.data) 将二进制数据包装成一个类似文件的对象
    # mimetype=image.mimetype 告诉浏览器这是什么类型的文件，以便正确渲染
    # download_name=image.filename 提供一个默认的下载文件名 (如果用户右键保存)
    return send_file(
        BytesIO(service.icon),
        mimetype=service.mimetype,
        download_name=service.full_name
    )


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
