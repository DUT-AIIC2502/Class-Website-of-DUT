"""运行应用"""
from app import create_app

# 创建应用
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
