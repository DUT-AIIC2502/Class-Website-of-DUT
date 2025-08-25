import pymysql.cursors

db = pymysql.connect(host='localhost',
                     user='root',
                     password='12345qazxc',
                     database='AIIC_student_info')

print('数据库连接成功！')
db.close()
print('数据库已关闭')
