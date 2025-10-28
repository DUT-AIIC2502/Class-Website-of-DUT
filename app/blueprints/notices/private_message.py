from . import notices_bp
from .helpers import exchange_students, get_common_students

import pickle, re, time, random
from flask import render_template, request, session, g, url_for, redirect
from flask_login import current_user

from common.flask_func import load_session_value, get_session_value
from common.QQ_operation import send_private_msg

"""
使用到 session 的键：
- table_name：学生信息表的表名（字符串）
- chose_students：已选择发送私人消息的学生列表（pickled bytes，二维数组，每个元素为[id, name, QQ_id]）
- not_chose_students：未选择发送私人消息的学生列表（pickled bytes，二维数组，每个元素为[id, name, QQ_id]）
- form_get：上次提交的表单数据（pickled bytes，字典）
"""


@notices_bp.route('/private_message/', methods=['GET', 'POST'])
def private_message():
    # 获取 session 中的已选择和未选择学生列表，默认为空列表和所有学生列表
    if 1 == 1:
        chose_students = load_session_value(get_session_value('chose_students'), [])
        not_chose_students = load_session_value(get_session_value('not_chose_students'), g.all_students)

    if request.method == 'GET':
        return render_template(
            'notices/private_message.html',
            **load_session_value(get_session_value('form_get'), {}),
            chose_students=chose_students,
            not_chose_students=not_chose_students
        )

    elif request.method == 'POST':
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
                return f"<script>alert('请选择要发送信息的同学！');window.history.back();</script>"

            # 组织并发送消息
            message_str = f"【来自：{current_user.real_name}】{form_get['message']}"
            message = [
                {
                    "type": "text",
                    "data": {
                        "text": message_str,
                    }
                }
            ]

            for student in chose_students:
                # 在发送私人消息前加入随机等待，防止短时间大量请求（随机 0.5 - 1.5 秒）
                delay = random.uniform(0.5, 1.5)
                time.sleep(delay)
                result = send_private_msg(student[2], message)

            return f"<script> alert('{result}');window.open('{url_for('notices.private_message')}');</script>"

        return redirect(f"{url_for('notices.private_message')}#result")


@notices_bp.route('/private_message/relay/', methods=['GET', 'POST'])
def relay():
    if request.method == 'GET':
        return render_template("notices/relay.html")

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
                session['chose_students'] = pickle.dumps(common_students)
                session['not_chose_students'] = pickle.dumps(missing_students)
            elif form_get['method'] == 'no':
                session['chose_students'] = pickle.dumps(missing_students)
                session['not_chose_students'] = pickle.dumps(common_students)

        return redirect(url_for('notices.private_message'))
    

@notices_bp.route('/private_message/names/', methods=['GET', 'POST'])
def names():
    if request.method == 'GET':
        return render_template("notices/names.html")
    
    elif request.method == 'POST':
        form_get = request.form.to_dict()

        # 获取分隔符
        if 1 == 1:
            if form_get['delimiter'] == 'line_break':
                delimiter = '\n'
            elif form_get['delimiter'] == 'comma':
                delimiter = '，'

        # 提取消息中的姓名，得到名单列表
        if 1 == 1:
            print(form_get['message'])
            names_list = form_get['message'].split(delimiter)
            print(names_list)
            # 去除空字符串和换行符
            names_list = [name.strip() for name in names_list if name.strip() != '']
            print(names_list)

            common_students, missing_students = get_common_students(names_list)
        
        # 将结果上传至session
        if 1 == 1:
            session['chose_students'] = pickle.dumps(common_students)
            session['not_chose_students'] = pickle.dumps(missing_students)

        return redirect(url_for('notices.private_message'))
    
