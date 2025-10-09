import re
import os
import sys

from flask import Flask
from sqlalchemy import text, inspect

from ext import db, login_manager, base, aps
from models import ScheduleFunctions


def create_app():
    """应用工厂"""
    print("--- 调试信息 ---")
    print(f"当前工作目录 (os.getcwd()): {os.getcwd()}")
    print(f"Python 模块搜索路径 (sys.path): {sys.path}")
    print("------------------")

    def add_jobs_from_config(config):
        """从配置中加载并添加任务到调度器"""
        for task in config:
            try:
                # 检查任务是否已存在，如果存在则先移除
                if aps.get_job(task['id']):
                    aps.remove_job(task['id'])

                # 添加任务
                aps.add_job(**task)
                app.logger.info(f"任务 '{task['id']}' 已添加/更新到调度器。")
            except Exception as e:
                app.logger.error(f"添加任务 '{task.get('id')}' 失败: {e}")

    def get_schedule_config():
        sql = "SELECT func_id, func, args, f_trigger, f_time FROM schedule_functions"
        schedule_functions = db.session.execute(text(sql))

        config = []
        for row in schedule_functions:
            func_id = row[0]
            func = row[1]
            args = row[2]
            trigger = row[3]
            time = row[4]

            new_config = {
                'id': func_id,  # 任务的唯一ID
                'func': func,  # 函数路径，格式为 '模块名:函数名'
                'args': (),
                'trigger': trigger,  # 触发器类型：interval, cron, date
            }

            """处理参数列表"""
            if args is not None or args == '':
                pass

            """处理时间设置"""
            time_str = re.findall(r'\d+', time)
            time_list = []
            for time in time_str:
                time_list.append(int(time))

            if trigger == 'interval':
                if time_list[0] != 0:
                    new_config['hours'] = time_list[0]
                if time_list[1] != 0:
                    new_config['minutes'] = time_list[1]
                if time_list[2] != 0:
                    new_config['seconds'] = time_list[2]
            elif trigger == 'cron':
                if time_list[0] != 0:
                    new_config['hour'] = time_list[0]
                if time_list[1] != 0:
                    new_config['minute'] = time_list[1]
                if time_list[2] != 0:
                    new_config['second'] = time_list[2]

            config.append(new_config)

        return config

    # 创建应用实例
    app = Flask(__name__, static_url_path='/static', static_folder='../static')
    # 进行配置
    app.config.from_object('config.Config')
    # 设置session密钥
    app.secret_key = app.config['SESSION_KEY']

    # 初始化数据库实例
    db.init_app(app)
    # 初始化LoginManager实例
    login_manager.init_app(app)

    # 导入蓝图
    from app.blueprints.main.routes import main_bp
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.info_management.routes import info_management_bp

    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(info_management_bp)

    with app.app_context():
        """反射数据库中需要的表"""
        from models import reflect_db
        reflect_db()  # 调用函数执行反射

        # 将 Base 与已反射的 metadata 绑定，为 db.metadata 中的所有表（如 'products'）自动创建 ORM 类
        base.prepare(autoload_with=db.engine)
        inspector = inspect(db.engine)

    """构造调度器"""
    if inspector.has_table(ScheduleFunctions.__tablename__):
        # 启动调度器
        aps.init_app(app)  # 将 scheduler 与 Flask app 绑定
        aps.start()
        app.logger.info("后台调度器已启动。")

        with app.app_context():
            # 从配置添加任务
            task_config = get_schedule_config()
            add_jobs_from_config(task_config)

    return app
