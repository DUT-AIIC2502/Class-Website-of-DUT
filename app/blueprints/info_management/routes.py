"""学生信息管理页面的蓝图"""
from flask import Blueprint, session
from flask import render_template, request, redirect, url_for
from sqlalchemy import text
import pickle
from translate import Translator

from dbconnection import db

# 定义蓝图
info_management_bp = Blueprint('info_management', __name__,
                               url_prefix='/info_management',
                               template_folder='templates')


@info_management_bp.route('/', methods=['GET', 'POST'])
def info_management():
    """学生信息查询界面"""
    # 标记详细信息页面只读
    session["whether_readonly"] = 1

    if 1 == 1:
        """获取目标表的表名和字段信息（字段、中文名）"""
        table_field = update_table_field()

    if request.method == 'GET':
        """加载页面"""

        if 1 == 1:
            """获取session中的值"""
            # 表单提交的值，主要为input的值
            form_get_default = {'filed_to_select': '', 'filed_to_select_value': ''}
            form_get_str = get_session_value("info_management_select_form_data")
            form_get = load_session_value(form_get_str, form_get_default)
            # 复选框选中的表单，默认为“姓名”、“学号”
            fields_str = get_session_value("info_management_select_fields_data")
            fields = load_session_value(fields_str, ['name', 'student_id'])
            # 搜索结果，以表格形式呈现给用户
            table_str = get_session_value("info_management_select_table_data")
            table = load_session_value(table_str)

        if 1 == 1:
            """标记复选框、下拉框默认值"""
            # 复选框默认或恢复选中的字段
            mark_list = [fields, 'checkbox']
            # 标记默认复选框
            table_field = mark_default(table_field, mark_list)

            # 下拉默认或恢复选中的字段
            mark_list = [[form_get['filed_to_select'], ], 'select']
            # 标记默认下拉框
            table_field = mark_default(table_field, mark_list)

        if 1 == 1:
            """将fields的每一项转化为中文"""
            for index in range(len(fields)):
                for row in table_field:
                    if fields[index] == row[0]:
                        fields[index] = row[1]
                        break

        return render_template('info_management.html',
                               fields=table_field,
                               table=table,
                               field_select=fields,
                               filed_to_select_value=form_get['filed_to_select_value'])

    elif request.method == 'POST':
        # 获取表单数据
        form_get = request.form.to_dict()

        if form_get['method'] == 'select':
            """查询操作"""
            table_name = get_session_value("table_name")
            # 获取表单中选中的所有字段名
            fields = request.form.getlist('field_to_show')

            if 1 == 1:
                """执行查询操作"""
                # 处理得到本次选中的字段，得到mysql字符串
                field_str = ''
                for f in fields:
                    # 将表单中选择的字段转化为符合mysql语法的字符串
                    field_str += f + ","
                field_str = field_str[:-1]

                # 判断是否要进行条件查询，并输入参数化占位符
                sql_where = ''
                field_to_select = form_get['filed_to_select']
                if form_get['name'] != '' or form_get['student_id'] != '' \
                        or form_get['filed_to_select_value'] != '':
                    sql_where = ' where '
                    if form_get['name'] != '':
                        sql_where += f"name = :name "
                    elif form_get['student_id'] != '':
                        sql_where += f"student_id = :student_id' "
                    elif form_get['filed_to_select_value'] != '':
                        sql_where += f"{field_to_select} = :{field_to_select} "

                # 拼接字符串，进行查询操作
                sql = f"select {field_str} from {table_name}" + sql_where
                result_proxy = db.session.execute(text(sql), {'name': form_get['name'],
                                                              'student_id': form_get['student_id'],
                                                              field_to_select: form_get['filed_to_select_value']})
                result_table = [list(row) for row in result_proxy.fetchall()]

            if 1 == 1:
                """将本次表单提交的数据保存至session"""
                # form_get
                form_get_str = pickle.dumps(form_get)
                session["info_management_select_form_data"] = form_get_str
                # fields
                fields_str = pickle.dumps(fields)
                session["info_management_select_fields_data"] = fields_str
                # table
                table_str = pickle.dumps(result_table)
                session["info_management_select_table_data"] = table_str

            # 重定向至GET
            return redirect("/info_management/", 302, Response=None)

        elif 'detail' in form_get['method']:
            """进入详情页面"""
            if 1 == 1:
                """更新session中的学号信息"""
                student_id_one = form_get['method'][7:]
                student_ids = [student_id_one]
                # 上传至session
                student_ids_str = pickle.dumps(student_ids)
                session["student_ids"] = student_ids_str

            return redirect(url_for("info_management.detail_info"))

        elif form_get["method"] == "insert_info":
            return redirect(url_for("info_management.insert_info"))

        elif form_get["method"] == "insert_field":
            return redirect(url_for("info_management.insert_field"))

        elif form_get["method"] == "delete_field":
            return redirect(url_for("info_management.delete_field"))

        elif form_get['method'] == 'delete':
            """进行删除操作"""
            if 1 == 1:
                """更新session中的学号信息"""
                # 将表单中复选框的选中信息形成列表，并上传至session
                student_ids = request.form.getlist('info_to_delete')
                student_ids_str = pickle.dumps(student_ids)
                session["student_ids"] = student_ids_str

            return redirect(url_for("info_management.auth_delete"))

        # elif form_get['method'] == 'import':
        #
        #     return


@info_management_bp.route('/insert_info/', methods=['GET', 'POST'])
def insert_info():
    """添加单条信息页面"""
    if 1 == 1:
        """从session获取信息"""
        # 表名
        table_name = get_session_value("table_name")
        # 表的字段信息
        talbe_field_str = get_session_value("table_field")
        table_field = load_session_value(talbe_field_str)

    if request.method == "GET":
        # 设置学号为空
        student_id = None

        return render_template('detail_info.html',
                               fields_values=table_field,
                               student_id=student_id)

    elif request.method == "POST":
        # 获取表单数据
        form_get = request.form.to_dict()

        if 1 == 1:
            """检查学号是否重复"""
            # 获取所有的学号信息
            sql = f"select student_id from {table_name}"
            result_proxy = db.session.execute(text(sql))
            result_student_ids = [list(row) for row in result_proxy.fetchall()]

            for row in result_student_ids:
                if form_get["student_id"] == row[0]:
                    return f"<script> alert('学号重复！！！请重新输入。');" \
                           f"window.open('{url_for('info_management.insert_info')}');</script>"

        if 1 == 1:
            """执行插入操作"""
            sql_value = ""
            for field in table_field:
                sql_value += f"'{form_get[field[0]]}', "
            sql_value = sql_value[:-2]

            sql = f"insert into {table_name} values ({sql_value})"
            db.session.execute(text(sql))
            db.session.commit()

        if 1 == 1:
            """将新插入的学号上传至session"""
            """更新session中的学号信息"""
            student_id = form_get['student_id']
            student_ids = [student_id]
            # 上传至session
            student_ids_str = pickle.dumps(student_ids)
            session["student_ids"] = student_ids_str

        return redirect(url_for("info_management.detail_info"))


@info_management_bp.route('/insert_field/', methods=['GET', 'POST'])
def insert_field():
    if 1 == 1:
        """从session获取信息"""
        # 表名
        table_name = get_session_value("table_name")
        # 表的字段信息
        talbe_field_str = get_session_value("table_field")
        table_field = load_session_value(talbe_field_str)

    if request.method == "GET":
        if 1 == 1:
            """生成现有字段的展示字符串"""
            table_field_str = ''
            for field in table_field:
                table_field_str += f"{field[1]}，"
            table_field_str = table_field_str[:-1]

        return render_template("insert_field.html",
                               table_fields=table_field_str)

    elif request.method == "POST":
        # 获取表单数据
        form_get = request.form.to_dict()

        if 1 == 1:
            """判断字段名是否重复"""
            for field in table_field:
                if form_get["field_to_insert"] == field[1]:
                    return f"<script> alert('字段名重复！');" \
                           f"window.open('{url_for('info_management.insert_field')}');</script>"

        if 1 == 1:
            """将字段名翻译为英文，作为新的字段"""
            field_name_ch = form_get['field_to_insert']
            field_name_en = translate(field_name_ch)
            # # 新的字段信息
            # new_field = [field_name_en, field_name_ch]

        if 1 == 1:
            """执行添加字段操作"""
            # 1. 为目标表添加字段
            sql = f"alter table {table_name} add {field_name_en} char(50) comment '{field_name_ch}';"
            db.session.execute(text(sql))
            db.session.commit()

            # 2. 为目标表的字段表同步更新
            sql = f"insert into {table_name}_field (field, field_name) " \
                  f"values ('{field_name_en}', '{field_name_ch}');"
            db.session.execute(text(sql))
            db.session.commit()

        if 1 == 1:
            """设置字段的默认值"""
            default_value = ''
            if form_get['field_default_value']:
                default_value = form_get['field_default_value']

            sql = f"update {table_name} set {field_name_en}={default_value}"
            db.session.execute(text(sql))
            db.session.commit()

        if 1 == 1:
            """更新session中的字段信息"""
            update_table_field()

        return redirect(url_for("info_management.insert_field"))


@info_management_bp.route('/delete_field/', methods=['GET', 'POST'])
def delete_field():
    if 1 == 1:
        """从session获取信息"""
        # 表名
        table_name = get_session_value("table_name")
        # 表的字段信息
        talbe_field_str = get_session_value("table_field")
        table_field = load_session_value(talbe_field_str)

    if request.method == "GET":
        return render_template("delete_field.html",
                               fields=table_field)

    elif request.method == "POST":
        # 获取表单数据
        form_get = request.form.to_dict()

        if 1 == 1:
            """得到要删除的字段的信息"""
            field_en = form_get["field_to_delete"]

        if 1 == 1:
            """执行删除字段操作"""
            # 1. 为目标表删除字段
            sql = f"alter table {table_name} drop {field_en}"
            db.session.execute(text(sql))
            db.session.commit()

            # 2. 为目标表的字段表同步更新
            sql = f"delete from {table_name}_field where field='{field_en}'"
            db.session.execute(text(sql))
            db.session.commit()

        if 1 == 1:
            """更新session中的字段信息"""
            update_table_field()

        return redirect(url_for("info_management.delete_field"))


@info_management_bp.route('/detail_info/', methods=['GET', 'POST'])
def detail_info():
    """单个学生的详细信息页面"""

    if 1 == 1:
        """从session获取信息"""
        # 表名
        table_name = get_session_value("table_name")
        # 表的字段信息
        talbe_field_str = get_session_value("table_field")
        table_field = load_session_value(talbe_field_str)
        # 单个学号
        student_ids_str = get_session_value("student_ids")
        student_ids = load_session_value(student_ids_str)
        student_id = student_ids[0]

    if request.method == 'GET':
        """进入页面"""
        if 1 == 1:
            """根据session['whether_readonly']的值来标记只读状态"""
            if_readonly = 'readonly'
            print(session['whether_readonly'])
            if session['whether_readonly'] == 1:
                # 默认只读
                pass
            elif session['whether_readonly'] == 0:
                if_readonly = ''

        if 1 == 1:
            """从数据库获取某个学生的详细信息，并制成符合传输规范的列表"""
            # 查询该学生的详细信息
            sql = f"select * from {table_name} where student_id = '{student_id}'"
            result_proxy = db.session.execute(text(sql))
            result_student = [list(row) for row in result_proxy.fetchall()][0]

            # 用来渲染前端的数组，默认只读
            fields_values = []
            for index in range(len(result_student)):
                row = [table_field[index][0], table_field[index][1],
                       result_student[index]]
                fields_values.append(row)

        return render_template('detail_info.html',
                               fields_values=fields_values,
                               student_id=student_id,
                               if_readonly=if_readonly)

    elif request.method == 'POST':
        """提交表单后刷新页面"""
        # 获取表单数据
        form_get = request.form.to_dict()

        if 1 == 1:
            """通过“锁定”/“解锁”按钮，切换只读状态"""
            if form_get['method'] == 'unlock':
                session["whether_readonly"] = 0
            elif form_get['method'] == 'lock':
                session["whether_readonly"] = 1

        if form_get['method'] == 'update':
            """进行更新操作"""
            # 产生待执行的mysql语句
            sql = f'update {table_name} set '
            for field in table_field:
                field_str = field[0]
                sql += f"{field_str}='{form_get[field_str]}', "
            sql = sql[:-2]
            # 添加更新条件
            sql += f" where student_id='{student_id}'"
            # 执行并提交更新操作
            db.session.execute(text(sql))
            db.session.commit()

        # 进行删除操作
        elif form_get['method'] == 'delete':
            """点击时，跳转至确认页面"""
            return redirect(url_for("info_management.auth_delete"))

        return redirect(url_for("info_management.detail_info"), 302, Response=None)


@info_management_bp.route('/auth_delete/', methods=['get', 'post'])
def auth_delete():
    if 1 == 1:
        """从session获取信息"""
        # 表名
        table_name = get_session_value("table_name")
        # # 表的字段信息
        # talbe_field_str = get_session_value("table_field")
        # table_field = load_session_value(talbe_field_str)
        # 学号集合
        student_ids_str = get_session_value("student_ids")
        student_ids = load_session_value(student_ids_str)

    if 1 == 1:
        """获取学号对应的学生信息"""
        # 将学号信息转化为mysql语句
        sql_student_id = ''
        for student_id in student_ids:
            sql_student_id += f"'{student_id}', "
        sql_student_id = sql_student_id[:-2]
        # 获取条件语句
        sql_where = f"where student_id in ({sql_student_id})"

    """确认删除页面"""
    if request.method == 'GET':
        if 1 == 1:
            """获取学号对应的学生信息"""
            # 拼接字符串，进行查询操作
            sql = f"select name, student_id from {table_name} {sql_where}"
            result_proxy = db.session.execute(text(sql))
            result_student = [list(row) for row in result_proxy.fetchall()]

        if 1 == 1:
            """获取用于渲染html的数据"""
            # 选中的学生姓名
            student_name = ''
            for row in result_student:
                student_name += row[0] + '，'
            student_name = student_name[:-1]

        return render_template('auth_delete.html', student_name=student_name)

    elif request.method == 'POST':
        if 1 == 1:
            """执行删除操作"""
            sql = f"delete from {table_name} {sql_where}"
            db.session.execute(text(sql))
            db.session.commit()

        return redirect(url_for('info_management.info_management'), code=302, Response=None)


def translate(chinese_str):
    """将中文翻译为特定格式的英文，用于将字段的中文名转化为字段"""
    translator = Translator(from_lang='Chinese', to_lang='English')
    translation_1 = translator.translate(chinese_str)

    # 将首字母改为小写
    if not translation_1:
        translation_2 = translation_1
    else:
        translation_2 = translation_1[0].lower() + translation_1[1:]

    # 将空格替换为下划线
    translation_3 = translation_2.replace(" ", "_")
    return translation_3


# def tuple_to_list(target_tuple):
#     """将任意维数的元组转化为列表"""
#     result_list = []
#     for item in target_tuple:
#         if isinstance(item, tuple):
#             result_list.append(tuple_to_list(item))
#         else:
#             result_list.append(item)
#     return result_list


def mark_default(list_to_mark, mark_fields):
    """用于标记需要默认选中的复选框或下拉列表，会为每一行的列表新增一项"""
    op_type = mark_fields[1]
    type_str = ''
    if op_type == 'checkbox':
        type_str = 'checked'
    elif op_type == 'select':
        type_str = 'selected'
    # 用于标记需要默认选中的选项
    result = []
    for item in list_to_mark:
        item.append('')
        for field in mark_fields[0]:
            if item[0] == field:
                item[-1] = type_str
                break
        # 将此列表添加到总列表中
        result.append(item)
    return result


def is_session_key_empty(key):
    """检查session中特定键是否为空"""
    if key not in session:
        return True

    value = session[key]

    # 检查各种空值情况
    if value is None:
        return True
    elif isinstance(value, str) and value.strip() == '':
        return True
    elif isinstance(value, (list, dict)) and len(value) == 0:
        return True
    elif value == '' or value == 0 or value is False:
        return True

    return False


def get_session_value(key, default=None):
    """安全获取session值，如果为空返回默认值"""
    if is_session_key_empty(key):
        return default
    return session[key]


def load_session_value(value, default=None):
    if value is None:
        return default
    else:
        result = pickle.loads(value)
        return result


def update_table_field():
    # 获取表名
    table_name = get_session_value("table_name")
    # 查询表的字段信息
    sql = f"select * from {table_name}_field"
    result_proxy = db.session.execute(text(sql))
    table_field = [list(row) for row in result_proxy.fetchall()]
    # 上传至session
    result_field_str = pickle.dumps(table_field)
    session["table_field"] = result_field_str

    return table_field
