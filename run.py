"""运行应用"""
from app import create_app
from config import RUN_SETTINGS_MAIN, RUN_SETTINGS_DEV

# 创建应用
app = create_app()

# 运行环境。如果是生产环境，则设置为"main"；如果是开发环境，则设置为"dev"
branch = 'dev'

if __name__ == '__main__':
    if branch == 'main':
        app.run(**RUN_SETTINGS_MAIN)
    elif branch == 'dev':
        app.run(**RUN_SETTINGS_DEV)
