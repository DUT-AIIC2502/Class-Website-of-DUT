from flask import Flask, render_template, request, redirect
import pymysql.cursors
from translate import Translator

# 创建Flask对象
app = Flask(__name__)


def translate(chinese_str):
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


@app.route('/', methods=['GET', 'POST'])
def form():
    sql_str = ''

    if request.method == 'POST':
        # 获取表单数据
        student = request.form.to_dict()

        # 数据库操作
        # 更新操作
        if student['method'] == 'update':
            # 打开数据库连接
            db = pymysql.connect(host='localhost',
                                 user='root',
                                 password='12345qazxc',
                                 database='AIIC_student_info')

            # 使用cursor()方法创建一个游标对象cursor
            cursor = db.cursor()

            # 获取student_info_aiic2502的所有字段及中文名
            cursor.execute('select * from student_info_AIIC2502_field')
            result_field = cursor.fetchall()
            # 所有已有的名字、学号
            cursor.execute('select name, student_ID from student_info_aiic2502')
            result_info = cursor.fetchall()     # 用于比对姓名、学号

            # 限定只能选择一项
            field = request.form.getlist('field')
            if len(field) != 1:
                return '<script> alert("更新时请只选择一个选项！");window.open("/");</script>'
            else:
                field = field[0]        # 确定字段名

            # 针对“其他”字段，翻译字段名为英语，并为表添加相应内容
            if field == 'other':
                # 判断字段名是否重复
                for i in result_field:
                    if student['other_field'] == i[1]:
                        return '<script> alert("字段名重复！");window.open("/");</script>'

                # 将“其他字段”翻译为英文，作为新的字段名
                field_name_ch = student['other_field']
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
            if len(result_info) != 0:
                for i in range(len(result_info)):
                    # 名字重复
                    if student['name'] == result_info[i][0]:
                        # 未输入学号 或 学号重复
                        if student['student_id'] == '' or student['student_id'] == result_info[i][1]:
                            method = 1
                        break
            # method为0则添加，1则修改
            field_value = student['field_value']
            if method == 0:
                # 若姓名没有重复，则添加数据
                sql_str = f"insert into student_info_aiic2502 (name, student_ID, {field}) " \
                          f"values ('{student['name']}', {student['student_id']}, '{field_value}');"
            elif method == 1:
                # 若姓名重复，则更改数据
                # 字符串
                if isinstance(field_value, str):
                    sql_str = f"update student_info_aiic2502 set {field}='{field_value}' where name='{student['name']}'"
                # 数字
                elif isinstance(field_value, int):
                    sql_str = f"update student_info_aiic2502 set {field}={field_value} where name='{student['name']}'"

            cursor.execute(sql_str)

            # 数据提交
            db.commit()

            # 关闭游标和数据库连接
            cursor.close()
            db.close()

            return '<script> alert("已成功更新信息！");window.open("/");</script>'

        # 查询操作
        elif student['method'] == 'select':
            # 重定向到同一页
            return redirect(request.url)

    else:
        # 获取表格student_info_aiic2502的所有字段，用以渲染网页
        # 打开数据库连接
        db = pymysql.connect(host='localhost',
                             user='root',
                             password='12345qazxc',
                             database='AIIC_student_info')

        # 使用cursor()方法创建一个游标对象cursor
        cursor = db.cursor()
        # 获取所有字段
        cursor.execute('select * from student_info_AIIC2502_field')
        result_field = cursor.fetchall()

        # 关闭游标和数据库连接
        cursor.close()
        db.close()

        return render_template('home.html', fields=result_field, field='字段')


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
