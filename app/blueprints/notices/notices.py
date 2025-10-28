from . import notices_bp

from flask import render_template, request, session, g

from ext import db, base
from common.flask_func import get_session_value

"""
使用到 session 的键：
- table_name：学生信息表的表名（字符串）
"""


@notices_bp.before_request
def before():
    # 获取表对应的 ORM 类
    table_name = get_session_value('table_name')
    if table_name in db.metadata.tables.keys():
        StudentInfo = getattr(base.classes, table_name)
        g.info_table = StudentInfo

        """获取包含所有学生的列表"""
        if 1 == 1:
            retrieved_students = db.session.query(StudentInfo).with_entities(StudentInfo.id, StudentInfo.name, StudentInfo.QQ_id).all()
            all_students = []  # 包括学生的id、姓名、QQ号
            for student in retrieved_students:
                all_students.append([student.id, student.name, student.QQ_id])

            g.all_students = all_students
    else:
        return "你查找的表不存在。"


@notices_bp.route('/', methods=['GET', 'POST'])
def home():
    # 清理 session 中的数据
    if 1 == 1:
        session.pop('origin_message', None)
        session.pop('key_info', None)
        session.pop('message_to_send', None)
        session.pop('chose_students', None)
        session.pop('not_chose_students', None)

    if request.method == 'POST':
        # 处理表单提交
        pass
    return render_template('notices/home.html')