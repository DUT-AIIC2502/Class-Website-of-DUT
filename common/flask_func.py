from flask import session
from flask_login import current_user
from sqlalchemy import and_, text
import pickle

from ext import db


def is_session_key_empty(key):
    """检查 session 键是否为空；不把数字 0 或 False 当作“空”"""
    if key not in session:
        return True

    value = session.get(key, None)

    # None
    if value is None:
        return True

    # 空字符串或仅空白
    if isinstance(value, str) and value.strip() == '':
        return True

    # 空的容器类型
    if isinstance(value, (list, dict, set, tuple)) and len(value) == 0:
        return True

    # 注意：不把 0 或 False 视为空值
    return False


def get_session_value(key, default=None):
    """安全获取 session 值；当键不存在或“空值”时返回默认值"""
    if is_session_key_empty(key):
        return default
    return session[key]


def load_session_value(value, default=None):
    """从 pickled bytes 还原；异常时返回默认值，避免抛错"""
    if value is None:
        return default
    try:
        if isinstance(value, (bytes, bytearray)):
            return pickle.loads(value)
        # 非 bytes 一律返回默认值，避免执行任意反序列化
        return default
    except Exception:
        return default


def get_user_info():
    """获取用户信息（与 session 双重校验，避免过期后残留显示）"""
    user_info = {}

    # 要求：session 中存在 user_id 且与 current_user 一致
    session_user_id = session.get('user_id')
    if not session_user_id:
        return user_info
    if not current_user.is_authenticated:
        return user_info

    # 若两者不一致，认为会话失效/脏数据，不返回任何用户信息
    try:
        if str(session_user_id) != str(getattr(current_user, 'student_id', None)):
            return user_info
    except Exception:
        return user_info

    # 角色与最高等级容错
    user_roles = []
    try:
        user_roles = [role.name for role in getattr(current_user, 'roles', []) if hasattr(role, 'name')]
    except Exception:
        user_roles = []

    user_level = {"Root": 4, "Admin": 3, "User": 2, "Guest": 1}
    user_top_role = 'Guest'
    if user_roles:
        # 过滤未知 role，防止 KeyError
        valid_roles = [r for r in user_roles if r in user_level]
        if valid_roles:
            user_top_role = max(valid_roles, key=lambda r: user_level[r])

    user_info = {
        'id': getattr(current_user, 'id', None),
        'user_id': getattr(current_user, 'student_id', None),  # 实为学号
        'user_name': getattr(current_user, 'real_name', None),
        'telephone': getattr(current_user, 'telephone', None),
        'email': getattr(current_user, 'email', None),
        'create_time': getattr(current_user, 'create_time', None),
        'status': getattr(current_user, 'status', None),
        'user_top_role': user_top_role,
        'user_roles': user_roles
    }
    return user_info


def get_services():
    """获取数据库中储存的所有服务；异常时返回空列表，确保类型一致"""
    try:
        sql = "SELECT * FROM services"
        services_result = db.session.execute(text(sql))
        return [dict(row) for row in services_result.mappings()]
    except Exception:
        return []


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

        conditions = []
        for field_name, value_info in (filters or {}).items():
            column = getattr(model, field_name)

            # 检查是简单查询还是复杂查询
            if isinstance(value_info, dict) and 'op' in value_info and 'value' in value_info:
                op = value_info['op']
                value = value_info['value']
                if op not in op_mapping:
                    raise ValueError(f"不支持的操作符: {op}")
                conditions.append(op_mapping[op](column, value))
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
