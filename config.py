"""配置文件"""


class Config(object):
    # 数据库的配置
    DIALCT = "mysql"
    DRITVER = "pymysql"
    HOST = 'localhost'
    PORT = "3306"
    USERNAME = "root"
    PASSWORD = "12345qazxc"
    DATABASE = 'AIIC_student_info'

    SQLALCHEMY_DATABASE_URI = f"{DIALCT}+{DRITVER}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8"

    # 其他配置
    DEBUG = True
    # TESTING = False
    SESSION_KEY = '12345qazxc'
