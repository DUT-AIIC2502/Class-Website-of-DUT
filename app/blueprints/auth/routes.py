"""注册界面蓝图"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__,
                    url_prefix='/auth',
                    template_folder='templates')


@auth_bp.route('/')
def login():
    return 'hello'
