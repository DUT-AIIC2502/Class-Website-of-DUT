from flask import Flask
from ext import db, login_manager, base


def create_app():
    """应用工厂"""
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

    with app.app_context():
        """反射数据库中需要的表"""
        from models import reflect_db
        reflect_db()  # 调用函数执行反射

        # 将 Base 与已反射的 metadata 绑定，为 db.metadata 中的所有表（如 'products'）自动创建 ORM 类
        base.prepare(autoload_with=db.engine)

    # 导入蓝图
    from app.blueprints.main.routes import main_bp
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.info_management.routes import info_management_bp

    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(info_management_bp)

    return app
