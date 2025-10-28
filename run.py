"""运行应用"""
import os
from app import create_app
from config import RUN_SETTINGS_MAIN, RUN_SETTINGS_DEV
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建应用
app = create_app()

method = os.getenv('METHOD', 'dev')

if __name__ == '__main__':
    if method == 'master':
        app.run(**RUN_SETTINGS_MAIN)
    elif method == 'dev':
        app.run(**RUN_SETTINGS_DEV)
