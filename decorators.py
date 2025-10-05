from functools import wraps
from flask import abort
from flask_login import current_user, login_required


def permission_required(*required_permissions, any_of=False):
    """
    检查用户是否拥有指定的权限。

    :param required_permissions: 一个或多个权限名称的元组。
    :param any_of: 如果为 True，用户只需拥有其中任意一个权限即可；
                   如果为 False (默认)，用户必须拥有所有指定的权限。
    """

    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized

            user_permissions = [p.name for role in current_user.roles for p in role.permissions]

            if any_of:
                # 检查是否拥有任意一个权限
                has_permission = any(p in user_permissions for p in required_permissions)
            else:
                # 检查是否拥有所有权限
                has_permission = all(p in user_permissions for p in required_permissions)

            if not has_permission:
                abort(403)  # Forbidden
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def role_required(*required_roles):
    """
    一个自定义装饰器，用于检查用户是否具有特定角色。
    """
    def decorator(f):
        @login_required
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized

            user_roles = [role.name for role in current_user.roles]

            has_permission = 0
            # 检查用户角色是否满足要求
            for role in required_roles:
                if role in user_roles:
                    has_permission = 1

            if has_permission == 0:
                # 如果权限不足，返回 403 Forbidden 错误
                abort(403)

            return f(*args, **kwargs)

        return decorated_function
    return decorator
