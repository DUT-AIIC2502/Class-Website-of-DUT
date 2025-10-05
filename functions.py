from flask import session
from flask_login import current_user
from sqlalchemy import and_
import pickle

from ext import db


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


def get_user_info():
    """获取用户的各种信息，用于渲染网页"""
    user_info = {}
    if current_user.is_authenticated:

        """获取用户的最高等级"""
        if 1 == 1:
            user_roles = [role.name for role in current_user.roles]
            user_level = {
                "Root": 4,
                "Admin": 3,
                "User": 2,
                "Guest": 1
            }

            # 使用 max() 和 key 参数来找到最重要的任务
            # key=lambda task: user_level[task] 的意思是：
            # 对于 todo_list 中的每一个 task（任务），
            # 使用 user_level[task] 得到它的重要性数值，
            # 然后 max() 函数就根据这些数值进行比较。
            user_top_role = max(user_roles, key=lambda task: user_level[task])

        """将用户信息以 dict 的形式储存"""
        if 1 == 1:
            user_info = {
                'id': current_user.id,
                'user_id': current_user.student_id,  # 这里的 user_id 实际上为学号
                'user_name': current_user.real_name,
                'telephone': current_user.telephone,
                'email': current_user.email,
                'create_time': current_user.create_time,
                'status': current_user.status,
                'user_top_role': user_top_role,
                'user_roles': user_roles
            }

    return user_info


def dynamic_query_builder(model, fields_to_select, filters):
    """
    一个通用的动态查询构建器。

    :param model: SQLAlchemy 的模型类 (例如 Product)。
    :param fields_to_select: 要查询的字段名列表 (例如 ['id', 'name'])。
    :param filters: 查询条件字典。
                    格式1 (简单等值): {'field_name': 'value'}
                    格式2 (复杂操作): {'field_name': {'op': 'operator', 'value': 'value'}}
                        支持的 'op': 'eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'like'
    :return: 查询结果的列表。
    """
    try:
        # --- 第 1 步: 动态构建投影 (选择要查询的字段) ---
        # 使用列表推导式和 getattr 安全地获取列对象
        # getattr(model, field) 等价于 model.field
        columns_to_select = [getattr(model, field) for field in fields_to_select]

        # 使用 db.session.query() 并解包列对象列表来创建基础查询
        # 这会生成 "SELECT field1, field2, ... FROM table"
        query = db.session.query(*columns_to_select)

        # --- 第 2 步: 动态构建过滤条件 ---
        # 用于存储单个布尔表达式的列表，例如 [Product.price > 100, Product.category == 'Electronics']
        conditions = []

        # 映射操作符字符串到 lambda 函数，lambda 会返回 SQLAlchemy 表达式
        op_mapping = {
            'eq': lambda col, val: col == val,
            'ne': lambda col, val: col != val,
            'gt': lambda col, val: col > val,
            'lt': lambda col, val: col < val,
            'gte': lambda col, val: col >= val,
            'lte': lambda col, val: col <= val,
            'like': lambda col, val: col.like(f'%{val}%'),
        }

        for field_name, value_info in filters.items():
            # 安全地获取列对象，如果字段不存在会抛出 AttributeError
            column = getattr(model, field_name)

            # 检查是简单查询还是复杂查询
            if isinstance(value_info, dict) and 'op' in value_info and 'value' in value_info:
                op = value_info['op']
                val = value_info['value']
                if op in op_mapping:
                    # 调用 lambda 函数生成表达式并添加到 conditions 列表
                    conditions.append(op_mapping[op](column, val))
                else:
                    raise ValueError(f"不支持的操作符: {op}")
            else:
                # 默认使用 '==' 操作
                conditions.append(column == value_info)

        # --- 第 3 步: 组合并执行查询 ---
        # 如果有条件，使用 and_(*conditions) 将所有条件用 AND 连接起来
        # and_(*conditions) 会将 [cond1, cond2] 转换为 cond1 AND cond2
        if conditions:
            query = query.filter(and_(*conditions))

        # 执行查询并返回结果
        return query.all()

    except AttributeError as e:
        # 处理无效的字段名
        raise ValueError(f"模型 {model.__name__} 中不存在字段: {e}")
    except Exception as e:
        # 处理其他可能的错误
        raise ValueError(f"构建查询时发生错误: {e}")
