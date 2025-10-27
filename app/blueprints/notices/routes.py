import re
import json
import pickle
import time
import random

from flask import Blueprint, request, redirect, render_template, url_for, session, g
from flask_login import current_user
from dotenv import load_dotenv

from ext import db, base
from common.flask_func import get_session_value, load_session_value
from common.ai_func import get_key_info
from common.QQ_operation import send_group_msg, send_private_msg
from .helpers import _inject_datetime_inputs, _get_datetime_str

load_dotenv()

notices_bp = Blueprint('notices', __name__,
                       url_prefix='/notices',
                       template_folder='templates')

"""
使用到 session 的键：
- origin_message：用户提交的原始活动通知文本（字符串）
- key_info：提取出的关键信息（pickled bytes）
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

    if request.method == 'POST':
        # 处理表单提交
        pass
    return render_template('notices/home.html')


@notices_bp.route('/new_notices/', methods=['GET', 'POST'])
def new_notices():
    if request.method == 'GET':
        # 获取 session 中的值
        if 1 == 1:
            origin_message = get_session_value('origin_message', default='')
            key_info = load_session_value(get_session_value('key_info', default={}))
            message_to_send = get_session_value('message_to_send', default='')

        return render_template('notices/new_notices.html', origin_message=origin_message, key_info=key_info, message_to_send=message_to_send)

    elif request.method == 'POST':
        form_get = request.form.to_dict()

        if form_get['method'] == "submit_origin_message":
            # 解析原始信息，提取关键信息
            if 1 == 1:
                origin_message = form_get.get('origin_message', '').strip()
                if origin_message:
                    try:
                        key_info = get_key_info(origin_message) # json
                        key_info = json.loads(key_info)         # dict
                        print("提取的关键信息：", key_info)
                        # 注入表单可用的日期/时间字段
                        key_info = _inject_datetime_inputs(key_info)
                    except Exception as e:
                        return f"<script>alert('解析超时或失败，请稍后重试（{type(e).__name__}）。');window.history.back();</script>"
                else:
                    return "<script>alert('请输入活动通知文本！');window.history.back();</script>"
                
            # session 操作
            if 1 == 1:
                session['origin_message'] = origin_message
                session['key_info'] = pickle.dumps(key_info)
                session.pop('message_to_send', None)  # 清除之前生成的通知文本（如果有）
        
        elif form_get['method'] == "generate_notice":
            # 根据填入的数据，生成新的活动通知文本
            message_to_send = ""

            # 组织文本内容
            if 1 == 1:
                if form_get.get('tags'):
                    if form_get.get('tags') == 'activity':
                        message_to_send += f"【活动通知】\n"
                    elif form_get.get('tags') == 'course':
                        message_to_send += f"【课程通知】\n"
                if form_get.get('title'):
                    message_to_send += f"『{form_get.get('title')}』\n"

                order = 0
                if form_get.get('theme'):
                    order += 1
                    message_to_send += f"{order}. 主题：{form_get.get('theme')}\n"

                # 处理时间信息
                if 1 == 1:
                    # 将时间信息处理为易读的字符串
                    if form_get.get('start_date'):
                        start_datetime = _get_datetime_str(form_get.get('start_date'), form_get.get('start_time'))
                    if form_get.get('end_date'):
                        end_datetime = _get_datetime_str(form_get.get('end_date'), form_get.get('end_time'))
                    # 拼接时间信息
                    order += 1
                    if form_get.get('start_date') and form_get.get('end_date'):
                        message_to_send += f"{order}. 时间：{start_datetime} - {end_datetime}\n"
                    elif form_get.get('start_date'):
                        message_to_send += f"{order}. 开始时间：{start_datetime}\n"
                    else:
                        message_to_send += f"{order}. 时间：{form_get['raw_time_text']}\n"

                if form_get.get('location'):
                    order += 1
                    message_to_send += f"{order}. 地点：{form_get.get('location')}\n"

                if form_get.get('participants'):
                    order += 1
                    message_to_send += f"{order}. 参与人员：{form_get.get('participants')}\n"

                if form_get.get('organizer'):
                    order += 1
                    message_to_send += f"{order}. 组织者：{form_get.get('organizer')}\n"

                if form_get.get('contact'):
                    order += 1
                    message_to_send += f"{order}. 联系方式：{form_get.get('contact')}\n"

                if form_get.get('registration'):
                    order += 1
                    message_to_send += f"{order}. 报名方式：{form_get.get('registration')}\n"   

                if form_get.get('deadline_date') and form_get.get('deadline_time'):
                    order += 1
                    deadline_time = _get_datetime_str(form_get.get('deadline_date'), form_get.get('deadline_time'))
                    message_to_send += f"{order}. 报名截止时间：{deadline_time}\n"

                if form_get.get('details'):
                    order += 1
                    message_to_send += f"{order}. 详细说明：\n"
                    details_lines = form_get.get('details').strip().splitlines()
                    for line in details_lines:
                        message_to_send += f"        {line}\n"

                if form_get.get('other_info'):
                    order += 1
                    message_to_send += f"{order}. 其他信息：\n"
                    other_info_lines = form_get.get('other_info').strip().splitlines()
                    for line in other_info_lines:
                        message_to_send += f"        {line}\n"

            # 将文本上传至 session，供显示使用
            if 1 == 1:
                session['message_to_send'] = message_to_send

        elif form_get['method'] == 'publish_notice':
            group_id = form_get['group']

            message_str = form_get['preview']
            user = current_user.real_name if current_user.is_authenticated else "匿名用户"
            message_str = f"【来自：{user}】{message_str}"
            message_dict = [
                {
                    "type": "text",
                    "data": {
                        "text": message_str,
                    }
                }
            ]

            status = send_group_msg(group_id, message_dict)
            print("发送状态：", status)

            return f"<script>alert('活动通知已发送！');window.location.href='{url_for('notices.home')}';</script>"

        return redirect(url_for('notices.new_notices'))


@notices_bp.route('/private_message/', methods=['GET', 'POST'])
def private_message():
    if 1 == 1:
        """声明使用到的 session 键"""
        chose_students = load_session_value(get_session_value('chose_students'), {})
        not_chose_students = load_session_value(get_session_value('not_chose_students'), g.all_students)

    if request.method == 'GET':
        return render_template(
            'notices/private_message.html',
            **load_session_value(get_session_value('form_get'), {}),
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
                    new_original_list = [s for s in new_original_list if s[0] != s_id]
                    if s_id == original_list[index][0]:
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
                send_private_msg(student[2], message)

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