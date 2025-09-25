from flask import Flask, render_template, request, redirect, url_for
import pymysql.cursors
from translate import Translator

# 创建Flask对象
app = Flask(__name__)


class MyDB:
    """描述数据库的类"""
    host = 'localhost'
    user = 'root'
    pw = '12345qazxc'
    database = 'AIIC_student_info'


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


def tuple_to_list(target_tuple):
    """将任意维数的元组转化为列表"""
    result_list = []
    for item in target_tuple:
        if isinstance(item, tuple):
            result_list.append(tuple_to_list(item))
        else:
            result_list.append(item)
    return result_list


def mark_default(list_to_mark, mark_fields, type):
    """用于标记需要默认选中的复选框或下拉列表"""
    type_str = ''
    if type == 'checkbox':
        type_str = 'checked'
    elif type == 'select':
        type_str = 'selected'
    # 用于标记需要默认选中的复选框
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


@app.route('/', methods=['GET'])
def get_redirect():
    """跳转至需要的页面"""
    return redirect(url_for('info_management'), code=302, Response=None)


@app.route('/info_management', methods=['GET', 'POST'])
def info_management():
    """学生信息查询界面"""
    # 用来执行的mysql语句
    sql_str = ''

    # 数据库操作
    # 打开数据库连接
    db = pymysql.connect(host=MyDB.host,
                         user=MyDB.user,
                         password=MyDB.pw,
                         database=MyDB.database)

    # 使用cursor()方法创建一个游标对象cursor
    cursor = db.cursor()

    # 获取student_info_aiic2502的所有字段及中文名
    cursor.execute('select * from student_info_AIIC2502_field')
    result_field_tup = cursor.fetchall()

    if request.method == 'GET':

        # 需要被标记为默认选中的字段
        checkboxs_to_mark = ('name', 'student_id')
        # 将获取的二维数组转化为列表
        result_field_list = tuple_to_list(result_field_tup)
        # 标记默认复选框
        result_field_list = mark_default(result_field_list, checkboxs_to_mark, 'checkbox')

        # 关闭游标和数据库连接
        cursor.close()
        db.close()

        return render_template('info_management.html', fields=result_field_list)

    elif request.method == 'POST':
        # 获取表单数据
        form_get = request.form.to_dict()
        # 获取表单中选中的所有字段名
        fields = request.form.getlist('field_to_show')

        # 获取所有已有的名字、学号
        cursor.execute('select name, student_ID from student_info_aiic2502')
        result_basic_info = cursor.fetchall()  # 用于比对姓名、学号

        # 更新操作
        if form_get['method'] == 'update':
            # 限定只能选择一项
            if len(fields) != 1:
                return '<script> alert("更新时请只选择一个选项！");window.open("/");</script>'
            else:
                field = fields[0]        # 确定字段名

            # 针对“其他”字段，翻译字段名为英语，并为表添加相应内容
            if field == 'other':
                # 判断字段名是否重复
                for index in result_field_tup:
                    if form_get['other_field'] == index[1]:
                        return '<script> alert("字段名重复！");window.open("/");</script>'

                # 将“其他字段”翻译为英文，作为新的字段名
                field_name_ch = form_get['other_field']
                field_name_en = translate(field_name_ch)
                field = field_name_en       # 更新新的字段名

                # 1.为表student_info_AIIC2502添加字段
                sql_str = f"alter table student_info_AIIC2502 add {field_name_en} char(50) comment '{field_name_ch}';"
                cursor.execute(sql_str)
                # 2. 为表student_info_AIIC2502_field同步更新
                sql_str = f"insert into student_info_AIIC2502_field (field, field_name) " \
                          f"values ('{field_name_en}', '{field_name_ch}');"
                cursor.execute(sql_str)

            # 进行比对，避免重复输入
            method = 0  # 用于判断进行添加还是更新操作
            if len(result_basic_info) != 0:
                for index in range(len(result_basic_info)):
                    # 名字重复
                    if form_get['name'] == result_basic_info[index][0]:
                        # 未输入学号 或 学号重复
                        if form_get['student_id'] == '' or form_get['student_id'] == result_basic_info[index][1]:
                            method = 1
                        break
            # method为0则添加，1则修改
            field_value = form_get['field_value']
            if method == 0:
                # 若姓名没有重复，则添加数据
                sql_str = f"insert into student_info_aiic2502 (name, student_ID, {field}) " \
                          f"values ('{form_get['name']}', '{form_get['student_id']}', '{field_value}');"
            elif method == 1:
                # 若姓名重复，则更改数据
                sql_str = f"update student_info_aiic2502 set {field}='{field_value}' where name='{form_get['name']}'"
            cursor.execute(sql_str)

            # 数据提交
            db.commit()

            # 关闭游标和数据库连接
            cursor.close()
            db.close()

            return '<script> alert("已成功更新信息！");window.open("/");</script>'

        # 查询操作
        if form_get['method'] == 'select':
            # 需要被标记为默认选中复选框的字段，用来恢复查询前的页面
            checkboxs_to_mark = ()
            option_to_mark = (form_get['filed_to_select'], )

            # 处理得到本次选中的字段
            field_str = ''
            for index in range(len(fields)):
                # 将表单中选择的字段转化为符合mysql语法的字符串字符串
                field_str = field_str + fields[index] + ","

                # 标记本次选中的复选框
                checkboxs_to_mark += (fields[index], )

                # 将表单中选择的字段转化为中文
                for f in result_field_tup:
                    if f[0] == fields[index]:
                        fields[index] = f[1]
            field_str = field_str[:-1]

            # 标记选项，以恢复原来的表单
            # 将元组转化为列表
            result_field_list = tuple_to_list(result_field_tup)
            # 标记默认复选框
            result_field_list = mark_default(result_field_list, checkboxs_to_mark, 'checkbox')
            # 标记默认单选项
            result_field_list = mark_default(result_field_list, option_to_mark, 'select')

            # 判断是否要进行条件查询
            sql_str_where = ''
            if form_get['name'] != '' or form_get['student_id'] != '' \
                    or form_get['filed_to_select_value'] != '':
                sql_str_where = ' where '
                if form_get['name'] != '':
                    sql_str_where += f"name = '{form_get['name']}' "
                elif form_get['student_id'] != '':
                    sql_str_where += f"student_id = '{form_get['student_id']}' "
                elif form_get['filed_to_select_value'] != '':
                    sql_str_where += f"{form_get['filed_to_select']} = '{form_get['filed_to_select_value']}' "

            # 拼接字符串，进行查询操作
            sql_str = f"select {field_str} from student_info_aiic2502" + sql_str_where
            cursor.execute(sql_str)
            result_table = cursor.fetchall()

            # 关闭游标和数据库连接
            cursor.close()
            db.close()
            # 重新渲染页面
            return render_template('info_management.html', fields=result_field_list, table=result_table,
                                   field_select=fields, filed_to_select_value=form_get['filed_to_select_value'])

        # elif form_get['method'] == 'delete':
        #     return


@app.route('/info_management/<if_authenticate>')
def authenticate_few(if_authenticate):
    """确认删除页面"""
    if if_authenticate == '0':
        return render_template('authenticate_few.html')

    elif if_authenticate == '1':
        # 数据库操作
        # 打开数据库连接
        db = pymysql.connect(host=MyDB.host,
                             user=MyDB.user,
                             password=MyDB.pw,
                             database=MyDB.database)

        # 使用cursor()方法创建一个游标对象cursor
        cursor = db.cursor()

        # # 产生待执行的mysql语句
        # sql_str = f"delete from student_info_aiic2502 where student_id='{student_id}'"
        # cursor.execute(sql_str)

        # 关闭游标和数据库连接
        cursor.close()
        db.commit()
        db.close()
        return redirect(url_for('info_management'), code=302, Response=None)


def select_to_show(cursor, student_id, result_field_tup):
    """从数据库获取某个学生的详细信息，并制成符合传输规范的列表"""
    # 查询该学生的详细信息
    sql_str = f"select * from student_info_aiic2502 where student_id = '{student_id}'"
    cursor.execute(sql_str)
    result_student = cursor.fetchall()[0]

    # 用来渲染前端的数组，默认只读
    fields_values = []
    for index in range(len(result_student)):
        row = [result_field_tup[index][0], result_field_tup[index][1],
               result_student[index]]
        fields_values.append(row)

    return fields_values


@app.route('/info_management/student_info/<student_id>', methods=['GET', 'POST'])
def student_info(student_id):
    """学生信息的详细界面"""
    # 数据库操作
    # 打开数据库连接
    db = pymysql.connect(host=MyDB.host,
                         user=MyDB.user,
                         password=MyDB.pw,
                         database=MyDB.database)

    # 使用cursor()方法创建一个游标对象cursor
    cursor = db.cursor()

    # 获取student_info_aiic2502的所有字段及中文名
    cursor.execute('select * from student_info_AIIC2502_field')
    result_field_tup = cursor.fetchall()

    if request.method == 'GET':
        """进入页面"""
        # 标记为锁定
        if_readonly = 'readonly'

        # 获得用来渲染前端的数组
        fields_values = select_to_show(cursor, student_id, result_field_tup)

        # 关闭游标和数据库连接
        cursor.close()
        db.close()
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
                cursor.execute('select name, student_ID from student_info_aiic2502')
                result_basic_info = cursor.fetchall()  # 用于比对姓名、学号

                # 检查学号是否重复
                for row in result_basic_info:
                    if form_get['student_id'] == row[1]:
                        return "学号重复，请重新输入！！！"

            # 产生待执行的mysql语句
            sql_str = 'update student_info_aiic2502 set '
            for field in result_field_tup:
                field_str = field[0]
                sql_str += f"{field_str}='{form_get[field_str]}', "
            sql_str = sql_str[:-2]
            # 添加更新条件
            sql_str += f" where student_id='{student_id}'"

            cursor.execute(sql_str)

        # 进行删除操作
        elif form_get['method'] == 'delete_all':
            """点击时，跳转至确认页面"""
            # 关闭游标和数据库连接
            cursor.close()
            db.close()
            return render_template('authenticate_one.html', student_id=student_id)

            # elif authenticate == 1:
            #     """在确认页面确认后，再次点击，执行删除操作"""

        # 更新学号
        student_id = form_get['student_id']
        # 进行查询操作，并形成列表
        fields_values = select_to_show(cursor, student_id, result_field_tup)

        # 关闭游标和数据库连接
        cursor.close()
        db.commit()
        db.close()
        return render_template('student_info.html', fields_values=fields_values,
                               student_id=student_id, if_readonly=if_readonly)


@app.route('/info_management/student_info/<student_id>/<if_authenticate>', methods=['get', 'post'])
def authenticate_one(student_id, if_authenticate):
    """确认删除页面"""
    if if_authenticate == '0':
        return render_template('authenticate_one.html', student_id=student_id)

    elif if_authenticate == '1':
        # 数据库操作
        # 打开数据库连接
        db = pymysql.connect(host=MyDB.host,
                             user=MyDB.user,
                             password=MyDB.pw,
                             database=MyDB.database)

        # 使用cursor()方法创建一个游标对象cursor
        cursor = db.cursor()

        # 产生待执行的mysql语句
        sql_str = f"delete from student_info_aiic2502 where student_id='{student_id}'"
        cursor.execute(sql_str)

        # 关闭游标和数据库连接
        cursor.close()
        db.commit()
        db.close()
        return redirect(url_for('info_management'), code=302, Response=None)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
