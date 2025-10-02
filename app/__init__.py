from flask import Flask
from ext import db, login_manager


def create_app():
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

    return app
