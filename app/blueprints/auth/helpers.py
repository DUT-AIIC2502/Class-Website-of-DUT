import time
from common.flask_func import get_session_value


def captcha_time_to_wait():
    """验证是否 1min 内重复发送验证码"""
    last_sent = get_session_value('captcha_time_key', None)
    now = int(time.time())
    if last_sent and now - int(last_sent) < 60:
        wait = 60 - (now - int(last_sent))
        return wait
    else:
        return 0
    

def get_top_role(user_roles):
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
    return max(user_roles, key=lambda task: user_level[task])