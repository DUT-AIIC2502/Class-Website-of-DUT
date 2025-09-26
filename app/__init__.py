from flask import Flask
from dbconnection import db


def create_app():
    # 创建应用实例
    app = Flask(__name__, static_url_path='/static', static_folder='../static')
    # 进行配置
    app.config.from_object('config.Config')
    # 设置session密钥
    app.secret_key = app.config['SESSION_KEY']

    # 初始化数据库实例
    db.init_app(app)

    # 导入蓝图
    from app.blueprints.main.routes import main_bp
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.info_management.routes import info_management_bp

    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(info_management_bp)

    return app


# def create_db(app):
#     db = SQLAlchemy(app)
#
#     # 将对象序列化为字符串
#     db_str = pickle.dumps(db)
#     # 储存在会话中
#     session['db'] = db_str
#
#     return db

