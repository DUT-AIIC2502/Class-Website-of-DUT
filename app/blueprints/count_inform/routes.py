import re
import pickle

from flask import Blueprint, request, render_template, redirect, url_for, session, g
from flask_login import current_user

from ext import db, base
from common.flask_func import get_session_value, load_session_value
from decorators import role_required
from common.send_message import send_qq_message

count_inform_bp = Blueprint('count_inform', __name__,
                            url_prefix='/count_inform',
                            template_folder='templates')

"""
"""




@count_inform_bp.before_request
@role_required('User')
def before():
    # 获取表对应的 ORM 类
    table_name = get_session_value('table_name')
    if table_name in db.metadata.tables.keys():
        StudentInfo: db.Model = getattr(base.classes, table_name)
        g.info_table = StudentInfo
    else:
        return "表不存在"

    """获取包含所有学生的列表"""
    if 1 == 1:
        retrieved_students = db.session.query(StudentInfo).with_entities(StudentInfo.id, StudentInfo.name).all()
        all_students = []  # 包括学生的id、姓名
        for student in retrieved_students:
            all_students.append([student.id, student.name])

        g.all_students = all_students


@count_inform_bp.route('/', methods=['GET', 'POST'])
@role_required('User')
def home():
    if 1 == 1:
        """声明使用到的 session 键"""
        description = get_session_value('description')

        chose_students = load_session_value(get_session_value('chose_students'))
        not_chose_students = load_session_value(get_session_value('not_chose_students'))

    if request.method == 'GET':
        """预览选择的学生"""

        return render_template(
            "count_inform/home.html",
            **load_session_value(get_session_value('form_get'), {}),
            description=description,
            chose_students=chose_students,
            not_chose_students=not_chose_students
        )

    elif request.method == 'POST':
        def exchange_students(s_ids, original_list, changed_list, original_status=1):
            """
            将选中的学生移出原来的组。

            :param original_status: 状态
            :param s_ids: 待移出的学生的 id 列表。
            :param original_list: 该学生原来所在的列表。
            :param changed_list: 该学生将去的列表。
            :return: None
            """

            new_original_list = original_list
            new_changed_list = changed_list
            for index in range(len(original_list)):
                for s_id in s_ids:
                    new_original_list = [student for student in new_original_list if student[0] != s_id]
                    if s_id == original_list[index][0]:
                        print("匹配成功")
                        new_changed_list.append(original_list[index])

            if original_status == 0:
                session['chose_students'] = pickle.dumps(new_original_list)
                session['not_chose_students'] = pickle.dumps(new_changed_list)
            else:
                session['not_chose_students'] = pickle.dumps(new_original_list)
                session['chose_students'] = pickle.dumps(new_changed_list)

            return None

        """获取并上传表单提交的数据"""
        if 1 == 1:
            form_get = request.form.to_dict()
            session['form_get'] = pickle.dumps(form_get)

        if 'one' in form_get['method']:
            student_ids_str = re.findall(r"\d+", form_get['method'])
            student_ids = [int(student_id) for student_id in student_ids_str]
            if "remove_one" in form_get['method']:
                exchange_students(student_ids, chose_students, not_chose_students, 0)
            elif "add_one" in form_get['method']:
                exchange_students(student_ids, not_chose_students, chose_students, 1)

        elif 'chose' in form_get['method']:
            if "remove" in form_get['method']:
                student_ids_str = request.form.getlist('students_to_remove')
                student_ids = [int(student_id) for student_id in student_ids_str]
                exchange_students(student_ids, chose_students, not_chose_students, 0)
            elif "add" in form_get['method']:
                student_ids_str = request.form.getlist('students_to_add')
                student_ids = [int(student_id) for student_id in student_ids_str]
                exchange_students(student_ids, not_chose_students, chose_students, 1)

        elif form_get['method'] == 'send_message':
            if len(chose_students) == 0:
                return f"<script> alert('请选择要发送信息的同学！');window.open('{url_for('count_inform.home')}');</script>"

            message = f"【自动消息】【来自：{current_user.real_name}】{form_get['message']}"

            if form_get['send_way'] == 'by_admin':
                pass

            if form_get['send_way'] == 'by_myself':
                for student in chose_students:
                    if current_user.real_name != student[1]:
                        send_qq_message(student[1], message)

        return redirect(f"{url_for('count_inform.home')}#result")


@count_inform_bp.route('/relay/', methods=['GET', 'POST'])
def relay():
    if request.method == 'GET':
        return render_template("count_inform/relay.html")

    elif request.method == 'POST':
        form_get = request.form.to_dict()

        """将接受的 message 转化为学生列表，并比对交集"""
        if 1 == 1:
            have_students_name = re.findall(r"\d+\.([\u4e00-\u9fa5]{2,4})", form_get['message'], flags=0)

            # 获取所有学生的姓名
            all_students = g.all_students
            all_students_name = [row[1] for row in all_students]

            # 转化为集合，方便比较
            # 警告！！！此步骤会丢失重名的同学
            all_students_name_set = set(all_students_name)
            have_students_name_set = set(have_students_name)

            common_set = have_students_name_set & all_students_name_set

        """将结果转化为id+姓名的二维数组"""
        if 1 == 1:
            common_students = []
            index_to_pop = []
            # 根据子集保存
            for element in common_set:
                for index in range(len(all_students)):
                    if element == all_students[index][1]:
                        common_students.append(all_students[index])
                        index_to_pop.append(index)
            # 删除
            index_to_pop.sort()
            index_to_pop = sorted(index_to_pop, reverse=True)
            for index in index_to_pop:
                all_students.pop(index)
            missing_students = all_students

        """将结果上传至session"""
        if 1 == 1:
            if form_get['method'] == 'yes':
                session['description'] = "你已选中参与接龙的同学："
                session['chose_students'] = pickle.dumps(common_students)
                session['not_chose_students'] = pickle.dumps(missing_students)
            elif form_get['method'] == 'no':
                session['description'] = "你已选中未参与接龙的同学。"
                session['chose_students'] = pickle.dumps(missing_students)
                session['not_chose_students'] = pickle.dumps(common_students)

        return redirect(url_for('count_inform.home'))
