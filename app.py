from flask import Flask, render_template, request, redirect
import pymysql.cursors

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # 获取表单数据
        if 1 == 1:
            student = dict()
            student['name'] = request.form.get('name')
            student['sex'] = request.form.get('sex')

        # 数据库操作
        if 1 == 1:
            # 打开数据库连接
            db = pymysql.connect(host='localhost',
                                 user='root',
                                 password='12345qazxc',
                                 database='AIIC_student_info')

            # 使用cursor()方法创建一个游标对象cursor
            cursor = db.cursor()

            # 先获取表格中的已有数据，并储存起来
            # 所有字段
            cursor.execute('select * from student_info_AIIC2502_field')
            result_field = cursor.fetchall()[0]
            # 各字段下的所有数据
            cursor.execute('select * from student_info_aiic2502')
            result_info = cursor.fetchall()

            # 进行比对，避免重复输入
            method1 = 0     # 用于判断进行添加还是更新操作
            method2 = 0     # 用于判断是否需要添加新的字段
            if len(result_info) != 0:
                for i in range(len(result_info)):
                    # 名字重复
                    if student['name'] == result_info[i][0]:
                        # if student['student']
                        method1 = 1
                        break
            # method为0则添加，1则修改
            sql_str = ''
            if method1 == 0:
                # 若姓名没有重复，则添加数据
                sql_str = f"insert into student_info_aiic2502 (name, sex) values ('{student['name']}', '{student['sex']}');"
            elif method1 == 1:
                # 若姓名重复，则更改数据
                sql_str = f"update student_info_aiic2502 set sex='{student['sex']}' where name='{student['name']}'"
            cursor.execute(sql_str)

            # 数据提交
            db.commit()

            # 关闭游标和数据库连接
            cursor.close()
            db.close()

        # 重定向到同一页
        return redirect(request.url)
    else:
        return render_template('home.html')


# @app.route('/management_system/', methods=['POST'])
# def submit():
#     name = request.form.get('name')
#     sex = request.form.get('sex')
#     return f'提交成功'


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
