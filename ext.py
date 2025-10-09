from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from sqlalchemy.ext.automap import automap_base


"""
初始化 db
"""
db = SQLAlchemy()

"""
配置 LoginManager，以实现在打开页面前验证是否登录
"""
# 初始化 LoginManager
login_manager = LoginManager()
# 设置登录页面的端点（URL），当未登录用户访问受保护页面时，会被重定向到这里
login_manager.login_view = '/auth/login/'
# 可选：自定义闪现消息
login_manager.login_message = '请先登录以访问该页面。'

"""初始化 AutomapBase"""
base = automap_base()

"""初始化 APScheduler"""
aps = APScheduler()
