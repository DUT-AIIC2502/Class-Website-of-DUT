# 测试蓝图
from flask import Flask, Blueprint, request

app = Flask(__name__)

# 最简单的蓝图测试
bp = Blueprint('test', __name__)


@bp.route('/test')  # 测试蓝图路由
def test():
    return "Blueprint OK"


app.register_blueprint(bp)

if __name__ == '__main__':
    app.run(debug=True)