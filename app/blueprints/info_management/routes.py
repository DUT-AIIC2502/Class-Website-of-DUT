"""学生信息管理页面的蓝图"""
from flask import Blueprint, session, jsonify, \
    render_template, request, redirect, url_for, send_file
from flask_login import login_required
from sqlalchemy import text, types
import pickle
import pandas as pd
import re
import io
from translate import Translator

from ext import db, base
from functions import get_session_value, load_session_value, dynamic_query_builder
from decorators import role_required
from models import refresh_db

# 定义蓝图
info_management_bp = Blueprint('info_management', __name__,
                               url_prefix='/info_management',
                               template_folder='templates')


@info_management_bp.before_request
def before_request():
    """当 session 过期后，重新刷新"""
    if get_session_value('table_name') is None:
        return "<script> alert('session已过期，请从主页重新进入页面。');window.open('/home/');</script>"


@info_management_bp.route('/', methods=['GET', 'POST'])
@role_required('Admin', 'Root')
def info_management():
    """学生信息查询界面"""
    """初始化一些数据"""
    if 1 == 1:
        # 获取表名
        table_name = get_session_value('table_name')
        # 获取目标表的表名和字段信息（字段、中文名），用于渲染复选框
        table_field = update_table_field()[2:]
        # 标记详细信息页面只读
        session["whether_readonly"] = 1

    if request.method == 'GET':
        """获取session中的值"""
        if 1 == 1:
            # 表单提交的值，主要为input的值
            # form_get_default = {'filter_field': '', 'filter_field_value': ''}
            form_get_str = get_session_value("form_get")
            form_get = load_session_value(form_get_str, {'filter_field': 'name'})
            # 复选框选中的表单，默认为“姓名”、“学号”
            fields_str = get_session_value("fields_to_select")
            fields = load_session_value(fields_str, ['name', 'student_id'])
            # 搜索结果，以表格形式呈现给用户
            table_paging_str = get_session_value("table_paging")
            table_paging = load_session_value(table_paging_str)

        """标记复选框、下拉框默认值"""
        if 1 == 1:
            # 复选框默认或恢复选中的字段
            mark_list = [fields, 'checkbox']
            # 标记默认复选框
            table_field = mark_default(table_field, mark_list)

            # 下拉默认或恢复选中的字段
            mark_list = [[form_get['filter_field'], ], 'select']
            # 标记默认下拉框
            table_field = mark_default(table_field, mark_list)

        """将fields的每一项转化为中文"""
        if 1 == 1:
            for index in range(len(fields)):
                for row in table_field:
                    if fields[index] == row[0]:
                        fields[index] = row[1]
                        break

        """数据分页"""
        if 1 == 1:
            page_number = get_session_value('page_number', 1)
            page_current = get_session_value('page_current', 1)
            if table_paging is not None:
                table = table_paging[page_current % page_number - 1]
            else:
                table = None

        return render_template('info_management.html',
                               **form_get,
                               fields=table_field,
                               table=table,
                               field_selected=fields,
                               page_current=page_current,
                               page_number=page_number)

    elif request.method == 'POST':
        # 获取表单数据
        form_get = request.form.to_dict()

        # 获取表对应的 ORM 类
        if table_name in db.metadata.tables.keys():
            StudentInfo: db.Model = getattr(base.classes, table_name)
        else:
            return '要查找的表不存在！'

        if form_get['method'] == 'select':  # 查询操作
            """执行查询操作"""
            if 1 == 1:
                # 获取id和表单中选中的所有字段名
                fields_to_select = ['id', ]
                for element in request.form.getlist('field_to_show'):
                    fields_to_select.append(element)

                # 查询条件字典
                filters = {}
                if form_get['name'] != '':
                    filters['name'] = {'op': 'like', 'value': form_get['name']}
                if form_get['student_id'] != '':
                    filters['student_id'] = {'op': 'like', 'value': form_get['student_id']}
                if form_get['filter_field_value'] != '':
                    filters[form_get['filter_field']] = \
                        {'op': 'like', 'value': form_get['filter_field_value']}

                # 执行查询操作
                result_table = dynamic_query_builder(StudentInfo, fields_to_select, filters)

                # 将查询结果的每一项替换为list
                for index in range(len(result_table)):
                    result_table[index] = list(result_table[index])

            """敏感数据脱敏"""
            if 1 == 1:
                # 需要被隐藏的字段
                fields_to_hide = ['student_id']
                # 这些字段对应的索引
                index_list = []
                for index in range(len(fields_to_select)):
                    if fields_to_select[index] in fields_to_hide:
                        index_list.append(index)

                # 将敏感数据替换为 *
                for row in result_table:
                    for index in index_list:
                        row[index] = '*' * len(row[index])

            """数据分页"""
            if 1 == 1:
                # 每页呈现的数据数
                length = 20
                # 总页数
                page_number = len(result_table) // length + 1

                # 将结果分开
                table_paging = []
                row = 0
                if page_number > 1:
                    for index in range(page_number-1):
                        table_paging.append(result_table[row:row+length])
                        row += length
                table_paging.append(result_table[row:])

            """将本次表单提交的数据保存至session"""
            if 1 == 1:
                # 表单提交的值
                form_get_str = pickle.dumps(form_get)
                session["form_get"] = form_get_str
                # 需要查询并在表格中展示的字段
                fields_to_select_str = pickle.dumps(fields_to_select)
                session["fields_to_select"] = fields_to_select_str
                # 待展示的数据（已完成分页）
                table_paging_str = pickle.dumps(table_paging)
                session["table_paging"] = table_paging_str
                # 总页数
                session['page_number'] = page_number
                # 当前页数
                session['page_current'] = 1

            # 重定向至GET
            return redirect("/info_management/")

        elif form_get['method'] == 'last_page':  # 上一页
            session['page_current'] = session['page_current'] % session['page_number'] - 1
            return redirect("/info_management/#pages")

        elif form_get['method'] == 'next_page':  # 下一页
            session['page_current'] = session['page_current'] % session['page_number'] + 1
            return redirect("/info_management/#pages")

        elif 'detail' in form_get['method']:  # 进入详情页面
            """更新session中的学号信息"""
            if 1 == 1:
                id_one = int(re.findall(r'\d+', form_get['method'])[0])
                ids = [id_one]
                # 上传至session
                ids_str = pickle.dumps(ids)
                session["ids"] = ids_str

            return redirect(url_for("info_management.detail_info"))

        elif form_get["method"] == "insert_info":  # 插入一条信息
            return redirect(url_for("info_management.insert_info"))

        elif form_get["method"] == "insert_field":  # 插入一个字段
            return redirect(url_for("info_management.insert_field"))

        elif form_get["method"] == "delete_field":  # 删除一个字段
            return redirect(url_for("info_management.delete_field"))

        elif form_get['method'] == 'delete':  # 删除选中项
            """更新session中的学号信息"""
            if 1 == 1:
                # 将表单中复选框的选中信息形成列表，并上传至session
                ids = request.form.getlist('info_to_delete')
                ids_str = pickle.dumps(ids)
                session["ids"] = ids_str

            return redirect(url_for("info_management.auth_delete"))

        elif form_get['method'] == 'import':
            return redirect(url_for("info_management.import_file"))

        elif form_get['method'] == 'export':
            # 从数据库获取数据
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, db.engine)

            # 创建内存文件对象
            output = io.BytesIO()

            # 使用pandas将数据写入Excel
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=table_name, index=False)

            output.seek(0)

            # 返回文件下载
            return send_file(
                output,    # 文件路径或文件类对象
                as_attachment=True,    # 是否作为附件下载（默认为False）
                download_name=f'{table_name}.xlsx',    # 下载时建议的文件名
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )


@info_management_bp.route('/insert_info/', methods=['GET', 'POST'])
@login_required
def insert_info():
    """添加单条信息页面"""

    """从session获取信息"""
    if 1 == 1:
        # 表名
        table_name = get_session_value("table_name")
        # 表的字段信息
        talbe_field_str = get_session_value("table_field")
        table_field = load_session_value(talbe_field_str)[2:]

    if request.method == "GET":
        # 设置学生编号为空
        id_one = None
        session['ids'] = None

        return render_template('detail_info.html',
                               fields_values=table_field,
                               id=id_one)

    elif request.method == "POST":
        # 获取表单数据
        form_get = request.form.to_dict()
        # 获取表
        StudentInfo: db.Model = base.classes[table_name]

        """检查学号是否重复"""
        if 1 == 1:
            # 获取所有的学号信息
            query_result = dynamic_query_builder(StudentInfo, ['student_id'], {})
            for row in query_result:
                if form_get["student_id"] == row[0]:
                    return f"<script> alert('学号重复！！！请重新输入。');" \
                           f"window.open('{url_for('info_management.insert_info')}');</script>"

        """执行插入操作"""
        if 1 == 1:
            new_student_info = StudentInfo(class_name=get_session_value('class_name'))
            for filed in table_field:
                setattr(new_student_info, filed[0], form_get[filed[0]])
            db.session.add(new_student_info)
            db.session.commit()

        """将新插入的学号上传至session"""
        if 1 == 1:
            # 获取新插入的数据的 id
            retrieved_student = db.session.query(StudentInfo) \
                .filter(StudentInfo.student_id == form_get['student_id']).first()
            id_one = retrieved_student.id
            ids = [id_one]
            # 上传至session
            ids_str = pickle.dumps(ids)
            session["ids"] = ids_str

            # 清除查询结果
            session['table_paging'] = None

        return redirect(url_for("info_management.detail_info"))


@info_management_bp.route('/insert_field/', methods=['GET', 'POST'])
@login_required
def insert_field():
    """从session获取信息"""
    if 1 == 1:
        # 表名
        table_name = get_session_value("table_name")
        # 表的字段信息
        talbe_field_str = get_session_value("table_field")
        table_field = load_session_value(talbe_field_str)[2:]

    if request.method == "GET":
        """生成现有字段的展示字符串"""
        if 1 == 1:
            table_field_str = ''
            for field in table_field:
                table_field_str += f"{field[1]}，"
            table_field_str = table_field_str[:-1]

        return render_template("insert_field.html",
                               table_fields=table_field_str)

    elif request.method == "POST":
        # 获取表单数据
        form_get = request.form.to_dict()

        """判断字段名是否重复"""
        if 1 == 1:
            for field in table_field:
                if form_get["field_to_insert"] == field[1]:
                    return f"<script> alert('字段名重复！');" \
                           f"window.open('{url_for('info_management.insert_field')}');</script>"

        """将字段名翻译为英文，作为新的字段"""
        if 1 == 1:
            field_name_ch = form_get['field_to_insert']
            field_name_en = translate(field_name_ch)

        """执行添加字段操作"""
        if 1 == 1:
            # 为目标表添加字段
            sql = f"alter table {table_name} add :field_name_en char(50) comment ':field_name_ch';"
            db.session.execute(text(sql), {'field_name_en': field_name_en, 'field_name_ch': field_name_ch})
            db.session.commit()

        """设置字段的默认值"""
        if 1 == 1:
            default_value = ''
            if form_get['field_default_value']:
                default_value = form_get['field_default_value']

            sql = f"update {table_name} set :field_name_en=:default_value"
            db.session.execute(text(sql), {'field_name_en': field_name_en, 'default_value': default_value})
            db.session.commit()

        """更新session中的字段信息、反射"""
        if 1 == 1:
            update_table_field()
            refresh_db()

        return redirect(url_for("info_management.insert_field"))


@info_management_bp.route('/delete_field/', methods=['GET', 'POST'])
@login_required
def delete_field():
    """删除单条字段"""

    """从session获取信息"""
    if 1 == 1:
        # 表名
        table_name = get_session_value("table_name")
        # 表的字段信息
        talbe_field_str = get_session_value("table_field")
        table_field = load_session_value(talbe_field_str)[2:]

    if request.method == "GET":
        return render_template("delete_field.html",
                               fields=table_field)

    elif request.method == "POST":
        # 获取表单数据
        form_get = request.form.to_dict()

        """得到要删除的字段的信息"""
        field_en = form_get["field_to_delete"]

        """执行删除字段操作"""
        if 1 == 1:
            # 为目标表删除字段
            sql = f"alter table {table_name} drop {field_en}"
            db.session.execute(text(sql))
            db.session.commit()

        """更新session中的字段信息"""
        update_table_field()

        return redirect(url_for("info_management.delete_field"))


@info_management_bp.route('/detail_info/', methods=['GET', 'POST'])
@login_required
def detail_info():
    """单个学生的详细信息页面"""

    """从session获取信息"""
    if 1 == 1:
        # 表名
        table_name = get_session_value("table_name")
        # 表的字段信息
        talbe_field_str = get_session_value("table_field")
        table_field = load_session_value(talbe_field_str)[2:]
        # 单个学号
        ids_str = get_session_value("ids")
        ids = load_session_value(ids_str)
        id_one = ids[0]

    # 获取表
    StudentInfo: db.Model = base.classes[table_name]
    # 查询该学生的详细信息
    retrieved_student = db.session.query(StudentInfo).filter(StudentInfo.id == id_one).first()

    if request.method == 'GET':
        """进入页面"""

        """根据session['whether_readonly']的值来标记只读状态"""
        if 1 == 1:
            # 默认只读
            if_readonly = 'readonly'
            if session['whether_readonly'] == 0:
                if_readonly = ''

        """从数据库获取某个学生的详细信息，并制成符合传输规范的列表"""
        if 1 == 1:
            # 用来渲染前端的数组，默认只读
            fields_values = []
            for field in table_field:
                row = [field[0], field[1], getattr(retrieved_student, field[0])]
                fields_values.append(row)

        return render_template('detail_info.html',
                               fields_values=fields_values,
                               id=id_one,
                               if_readonly=if_readonly)

    elif request.method == 'POST':
        """提交表单后刷新页面"""
        # 获取表单数据
        form_get = request.form.to_dict()

        """通过“锁定”/“解锁”按钮，切换只读状态"""
        if 1 == 1:
            if form_get['method'] == 'unlock':
                session["whether_readonly"] = 0
            elif form_get['method'] == 'lock':
                session["whether_readonly"] = 1

        if form_get['method'] == 'update':  # 更新
            for field in table_field:
                setattr(retrieved_student, field[0], form_get[field[0]])
            db.session.commit()

            # 清除查询结果
            session['table_paging'] = None

        elif form_get['method'] == 'delete':  # 删除
            """点击时，跳转至确认页面"""
            return redirect(url_for("info_management.auth_delete"))

        return redirect(url_for("info_management.detail_info"), 302, Response=None)


@info_management_bp.route('/auth_delete/', methods=['get', 'post'])
@login_required
def auth_delete():
    """确认是否删除"""
    """从session获取信息"""
    if 1 == 1:
        # 表名
        table_name = get_session_value("table_name")
        # id 集合
        ids_str = get_session_value("ids")
        ids = load_session_value(ids_str)

    """获取 id 对应的学生信息"""
    if 1 == 1:
        StudentInfo: db.Model = base.classes[table_name]
        retrieved_student = []
        for id_one in ids:
            retrieved_student.append(db.session.query(StudentInfo).filter(StudentInfo.id == id_one).first())

        # # 将学号信息转化为mysql语句
        # sql_student_id = ''
        # for student_id in ids:
        #     sql_student_id += f"'{student_id}', "
        # sql_student_id = sql_student_id[:-2]
        # # 获取条件语句
        # sql_where = f"where student_id in ({sql_student_id})"

    if request.method == 'GET':
        """确认删除页面"""

        # """获取学号对应的学生信息"""
        # if 1 == 1:
        #     # 拼接字符串，进行查询操作
        #     sql = f"select name, student_id from {table_name} {sql_where}"
        #     result_proxy = db.session.execute(text(sql))
        #     result_student = [list(row) for row in result_proxy.fetchall()]

        """获取用于渲染html的数据"""
        if 1 == 1:
            # 选中的学生姓名
            student_name = ''
            for student in retrieved_student:
                student_name += student.name + '，'
            student_name = student_name[:-1]

        return render_template('auth_delete.html', student_name=student_name)

    elif request.method == 'POST':
        """执行删除操作"""
        if 1 == 1:
            for student in retrieved_student:
                db.session.delete(student)
            db.session.commit()

        """清除 session 中的数据"""
        if 1 == 1:
            session['ids'] = None
            session['table_paging'] = None

        return redirect(url_for('info_management.info_management'), code=302, Response=None)


@info_management_bp.route('/import_file/', methods=['get', 'post'])
@login_required
def import_file():
    if request.method == "GET":
        return render_template("import_file.html")

    elif request.method == "POST":
        """安全验证"""
        if 1 == 1:
            if 'file' not in request.files:
                return f"<script> alert('没有选择文件！');" \
                       f"window.open('{url_for('info_management.import_file')}');</script>"

            # 获取上传的FileStorage对象
            file = request.files['file']

            if file.filename == '':
                return f"<script> alert('没有选择文件！');" \
                       f"window.open('{url_for('info_management.import_file')}');</script>"

            # 验证文件类型为excel
            if not file.filename.endswith(('.xlsx', '.xls')):
                return jsonify({'error': '只支持Excel文件'}), 400

        table_name = get_session_value("table_name")
        """读取excel文件，并与数据库的表的字段匹配"""
        if 1 == 1:
            # 使用pandas读取文件，df是二维表结构
            df = pd.read_excel(file, header=0)

            """将表格的列名与数据库表的字段名匹配"""
            if 1 == 1:
                # 读取表格第一行
                first_row = pd.read_excel(file, nrows=0)

                # 将中文名和英文名信息分离， 用fields储存表的字段信息（英文+中文）
                fields = []
                for column in first_row:
                    # 提取中文
                    field_ch = re.findall(r'[\u4e00-\u9fa5]+', column)[0]
                    # 提取英文和下划线
                    field_en = re.findall(r'[a-zA-Z_]+', column)[0]
                    fields.append([field_en, field_ch])

                    # 确保Excel中的字段名与数据库表字段名匹配
                    # 如果需要，可以在这里重命名DataFrame的列以匹配数据库表
                    df.rename(columns={column: field_en}, inplace=True)

        """将数据导入MySQL数据库表"""
        if 1 == 1:
            form_get = request.form.to_dict()
            method = form_get['method']

            # if_exists='append' 表示在现有数据后追加；'replace' 表示替换整个表
            # df格式使engine对表的大小写敏感，要改为小写
            df.to_sql(table_name.lower(),
                      con=db.engine,
                      if_exists=method,
                      index=False,
                      dtype=types.String(length=20))

        """为每一个字段添加备注"""
        if 1 == 1:
            for field in fields:
                sql = f"alter table {table_name} change {field[0]} {field[0]} char(20) comment '{field[1]}';"
                db.session.execute(text(sql))
                db.session.commit()

            # 更新table_field
            update_table_field()

        return f"<script> alert('导入成功！');" \
               f"window.open('{url_for('info_management.import_file')}');</script>"


def update_table_field():
    # 获取表名
    table_name = get_session_value("table_name")
    # 查询表的所有信息
    sql = f"SHOW FULL COLUMNS FROM {table_name}"
    result_proxy = db.session.execute(text(sql))
    table_full_info = [list(row) for row in result_proxy.fetchall()]

    # 获取字段名和备注
    table_field = []
    for row in table_full_info:
        table_field.append([row[0], row[8]])

    # 上传至session
    result_field_str = pickle.dumps(table_field)
    session["table_field"] = result_field_str

    return table_field


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


def export_table_to_excel(table_name, output_file=None):
    """导出数据库表为 Excel 文件"""
    if output_file is None:
        output_file = f'{table_name}.xlsx'

    # 使用 Flask-SQLAlchemy 的引擎
    df = pd.read_sql(f"SELECT * FROM {table_name}", con=db.engine)
    df.to_excel(output_file, index=False)

    return output_file
