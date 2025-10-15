"""配置文件"""
from datetime import timedelta


class Config(object):
    # 数据库的配置
    DIALCT = "mysql"
    DRITVER = "pymysql"
    HOST = 'localhost'
    PORT = "3306"
    USERNAME = "root"
    PASSWORD = "123456"
    DATABASE = 'CLASS_WEBSITE'

    SQLALCHEMY_DATABASE_URI = f"{DIALCT}+{DRITVER}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8"

    # 调度器的配置
    SCHEDULER_API_ENABLED = True  # 启用 API
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'  # 设置时区
    SCHEDULER_EXECUTORS = {'default': {'type': 'threadpool', 'max_workers': 10}}  # 配置执行器

    # 其他配置
    # DEBUG = True
    SESSION_KEY = '123456'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=10)


# 开发服务器运行参数
RUN_SETTINGS_MAIN = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'use_reloader': False
}

RUN_SETTINGS_DEV = {
    'host': '127.0.0.1',
    'port': 5001,
    'debug': True,
    'use_reloader': False
}
