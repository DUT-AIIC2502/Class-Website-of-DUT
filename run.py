"""运行应用"""
from app import create_app

# 创建应用
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
