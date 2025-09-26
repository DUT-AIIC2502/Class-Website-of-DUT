"""学生信息管理页面的蓝图"""
from flask import Blueprint, session
from flask import render_template, request, redirect, url_for
from sqlalchemy import text
from translate import Translator


from dbconnection import db

# 定义蓝图
info_management_bp = Blueprint('info_management', __name__,
                               url_prefix='/info_management',
                               template_folder='templates')


@info_management_bp.route('/', methods=['GET', 'POST'])
def info_management():
    """学生信息查询界面"""
    table_name = "student_info_AIIC2502"

    # 获取student_info_aiic2502的所有字段及中文名
    sql = f"select * from {table_name}_field"
    result_proxy = db.session.execute(text(sql))
    result_field = [list(row) for row in result_proxy.fetchall()]

    if request.method == 'GET':
        """加载页面"""
        # 需要被标记为默认选中的字段
        checkboxs_to_mark = ('name', 'student_id')
        # 标记默认复选框
        result_field = mark_default(result_field, checkboxs_to_mark, 'checkbox')

        return render_template('info_management.html', fields=result_field)

    elif request.method == 'POST':
        # 获取表单数据
        form_get = request.form.to_dict()

        # 获取所有已有的名字、学号
        sql = f"select name, student_ID from {table_name}"
        result_proxy = db.session.execute(text(sql))
        result_basic_info = [list(row) for row in result_proxy.fetchall()]  # 用于比对姓名、学号

        # 查询操作
        if form_get['method'] == 'select':
            # 获取表单中选中的所有字段名
            fields = request.form.getlist('field_to_show')

            # 需要被标记为默认选中复选框的字段，用来恢复查询前的页面
            checkboxs_to_mark = ()
            option_to_mark = (form_get['filed_to_select'],)

            # 处理得到本次选中的字段
            field_str = ''
            for index in range(len(fields)):
                # 将表单中选择的字段转化为符合mysql语法的字符串字符串
                field_str = field_str + fields[index] + ","

                # 标记本次选中的复选框
                checkboxs_to_mark += (fields[index],)

                # 将表单中选择的字段转化为中文
                for f in result_field:
                    if f[0] == fields[index]:
                        fields[index] = f[1]
            field_str = field_str[:-1]

            # 标记选项，以恢复原来的表单
            # 标记默认复选框
            result_field = mark_default(result_field, checkboxs_to_mark, 'checkbox')
            # 标记默认单选项
            result_field = mark_default(result_field, option_to_mark, 'select')

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
            # 重新渲染页面
            return render_template('info_management.html', fields=result_field, table=result_table,
                                   field_select=fields, filed_to_select_value=form_get['filed_to_select_value'])

        elif form_get['method'] == 'delete':
            # 将表单中复选框的选中信息转化为mysql语句
            infos = request.form.getlist('field_to_show')
            # 储存选中的学生的学号
            student_ids_str = ''

            for row in infos:
                student_ids_str += f"{row}, "
            student_ids_str = student_ids_str[:-2]

            return redirect(f"/info_management/{student_ids_str}/0/")


# @info_management_bp.route('/authenticate/<student_ids>/<if_authenticate>')
# def authenticate_few(if_authenticate):
#     table_name = "student_info_AIIC2502"
#     """确认删除页面"""
#     if if_authenticate == '0':
#         return render_template('authenticate_few.html')
#
#     elif if_authenticate == '1':
#         # 产生待执行的mysql语句
#         sql = f"delete from {table_name} where student_id = :student_id"
#
#         return redirect(url_for('info_management'), code=302, Response=None)


@info_management_bp.route('/student_info/<student_id>/', methods=['GET', 'POST'])
def student_info(student_id):
    table_name = "student_info_AIIC2502"
    """学生信息的详细界面"""
    # 获取student_info_aiic2502的所有字段及中文名
    sql = f"select * from {table_name}_field"
    result_proxy = db.session.execute(text(sql))
    result_field_tup = [list(row) for row in result_proxy.fetchall()]

    if request.method == 'GET':
        """进入页面"""
        # 标记为锁定
        if_readonly = 'readonly'

        # 获得用来渲染前端的数组
        fields_values = select_to_show(db, student_id, result_field_tup)
        return render_template('student_info.html', fields_values=fields_values,
                               student_id=student_id, if_readonly=if_readonly)

    elif request.method == 'POST':
        """提交表单后刷新页面"""
        # 获取表单数据
        form_get = request.form.to_dict()

        # 默认可编辑
        if_readonly = ''
        # 标记锁定状态
        if form_get['method'] == 'unlock':
            if_readonly = ''
        elif form_get['method'] == 'lock':
            if_readonly = 'readonly'

        # 进行更新操作
        elif form_get['method'] == 'update':
            if student_id != form_get['student_id']:
                """若修改了学号，则需要检查学号是否与已有的重复"""
                # 获取所有已有的名字、学号
                sql = f'select name, student_ID from {table_name}'
                result_proxy = db.session.execute(text(sql))
                result_basic_info = [list(row) for row in result_proxy.fetchall()]  # 用于比对姓名、学号

                # 检查学号是否重复
                for row in result_basic_info:
                    if form_get['student_id'] == row[1]:
                        return "学号重复，请重新输入！！！"

            # 产生待执行的mysql语句
            sql = 'update student_info_aiic2502 set '
            for field in result_field_tup:
                field_str = field[0]
                sql += f"{field_str}='{form_get[field_str]}', "
            sql = sql[:-2]
            # 添加更新条件
            sql += f" where student_id='{student_id}'"

            # 执行并提交更新操作
            db.session.execute(text(sql))
            db.session.commit()

        # 进行删除操作
        elif form_get['method'] == 'delete_all':
            """点击时，跳转至确认页面"""
            return render_template('authenticate_one.html', student_id=student_id)

        # 更新学号
        student_id = form_get['student_id']
        # 进行查询操作，并形成列表
        fields_values = select_to_show(db, student_id, result_field_tup)

        return render_template('student_info.html', fields_values=fields_values,
                               student_id=student_id, if_readonly=if_readonly)


@info_management_bp.route('/student_info/<student_id>/<if_authenticate>/', methods=['get', 'post'])
def authenticate_one(student_id, if_authenticate):
    """确认删除页面"""
    if if_authenticate == '0':
        return render_template('authenticate_one.html', student_id=student_id)

    elif if_authenticate == '1':
        # 执行的mysql语句
        sql = f"delete from student_info_aiic2502 where student_id=:student_id"
        db.session.execute(text(sql), {'student_id': student_id})
        db.session.commit()
        return redirect(url_for('info_management'), code=302, Response=None)


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


def mark_default(list_to_mark, mark_fields, op_type):
    """用于标记需要默认选中的复选框或下拉列表"""
    type_str = ''
    if op_type == 'checkbox':
        type_str = 'checked'
    elif op_type == 'select':
        type_str = 'selected'
    # 用于标记需要默认选中的选项
    result = []
    for item in list_to_mark:
        item.append('')
        for field in mark_fields:
            if item[0] == field:
                item[-1] = type_str
                break
        # 将此列表添加到总列表中
        result.append(item)
    return result


def select_to_show(my_db, student_id, result_field_tup):
    """从数据库获取某个学生的详细信息，并制成符合传输规范的列表"""
    # 查询该学生的详细信息
    sql = "select * from student_info_aiic2502 where student_id = :student_id"
    result_proxy = my_db.session.execute(text(sql), {'student_id': student_id})
    result_student = [list(row) for row in result_proxy.fetchall()]

    # 用来渲染前端的数组，默认只读
    fields_values = []
    for index in range(len(result_student)):
        row = [result_field_tup[index][0], result_field_tup[index][1],
               result_student[index]]
        fields_values.append(row)

    return fields_values
