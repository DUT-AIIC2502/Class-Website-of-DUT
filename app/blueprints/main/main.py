from . import main_bp

import datetime
from io import BytesIO
from pathlib import Path
from flask import render_template, session, redirect, send_file, jsonify
from sqlalchemy import text

from ext import db, aps
from models import Role, Permission, ScheduleFunctions, Services


@main_bp.route('/')
def main():
    return redirect('/create_tables/')


@main_bp.route('/home/')
def home():
    """初始化某些数据"""
    # 仅在已登录时初始化
    if session.get('user_id'):
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
        execute_sql_file_mysql('static/sql/roles.sql')

    """插入权限"""
    if Permission.query.first() is None:
        execute_sql_file_mysql('static/sql/permissions.sql')

    """插入定时任务"""
    if ScheduleFunctions.query.first() is None:
        pass
        # execute_sql_file_mysql('static/sql/schedule_functions.sql')

    if Services.query.first() is None:
        execute_sql_file_mysql('static/sql/services.sql')

    return redirect('/home/')


@main_bp.route('/icon/<int:image_id>')
def get_icon(image_id):
    """
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


@main_bp.route('/jobs/')
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
