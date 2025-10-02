from flask import session
import pickle


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
