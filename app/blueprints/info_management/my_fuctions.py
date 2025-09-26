# from translate import Translator
#
#
# def translate(chinese_str):
#     """将中文翻译为特定格式的英文，用于将字段的中文名转化为字段"""
#     translator = Translator(from_lang='Chinese', to_lang='English')
#     translation_1 = translator.translate(chinese_str)
#
#     # 将首字母改为小写
#     if not translation_1:
#         translation_2 = translation_1
#     else:
#         translation_2 = translation_1[0].lower() + translation_1[1:]
#
#     # 将空格替换为下划线
#     translation_3 = translation_2.replace(" ", "_")
#     return translation_3
#
#
# def tuple_to_list(target_tuple):
#     """将任意维数的元组转化为列表"""
#     result_list = []
#     for item in target_tuple:
#         if isinstance(item, tuple):
#             result_list.append(tuple_to_list(item))
#         else:
#             result_list.append(item)
#     return result_list
#
#
# def mark_default(list_to_mark, mark_fields, op_type):
#     """用于标记需要默认选中的复选框或下拉列表"""
#     type_str = ''
#     if op_type == 'checkbox':
#         type_str = 'checked'
#     elif op_type == 'select':
#         type_str = 'selected'
#     # 用于标记需要默认选中的复选框
#     result = []
#     for item in list_to_mark:
#         item.append('')
#         for field in mark_fields:
#             if item[0] == field:
#                 item[-1] = type_str
#                 break
#         # 将此列表添加到总列表中
#         result.append(item)
#     return result
#
#
# def select_to_show(my_db, student_id, result_field_tup):
#     """从数据库获取某个学生的详细信息，并制成符合传输规范的列表"""
#     # 查询该学生的详细信息
#     sql = "select * from student_info_aiic2502 where student_id = :student_id"
#     result_student = my_db.session.execute(sql, {'student_id': student_id})
#
#     # 用来渲染前端的数组，默认只读
#     fields_values = []
#     for index in range(len(result_student)):
#         row = [result_field_tup[index][0], result_field_tup[index][1],
#                result_student[index]]
#         fields_values.append(row)
#
#     return fields_values
