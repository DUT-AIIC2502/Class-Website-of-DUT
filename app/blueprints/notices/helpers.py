from datetime import datetime


def _split_iso_datetime(iso_str: str):
    """
    将 ISO8601 时间字符串（如"2025-10-23T15:00:00+08:00"）拆分为 (YYYY-MM-DD, HH:MM)。
    解析失败返回 ("", "")。支持带 Z 的 UTC 标记。
    """

    # 预处理数据
    if 1 == 1:
        # 处理 None 或非字符串输入
        if not iso_str or not isinstance(iso_str, str):
            return "", ""
        s = iso_str.strip() # 去除首尾空白
        # 处理 UTC 标记
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

    # 解析并拆分为字符串
    try:
        dt = datetime.fromisoformat(s)
        return dt.date().isoformat(), dt.strftime("%H:%M")  
    except Exception:
        # 如果是只有日期的情形
        try:
            d = datetime.fromisoformat(s + "T00:00:00").date()
            return d.isoformat(), ""
        except Exception:
            return "", ""


def _inject_datetime_inputs(key_info: dict) -> dict:
    """
    在 key_info 中注入 HTML 表单可直接使用的日期/时间字段：
    - start_date_input, start_time_input
    - end_date_input, end_time_input
    - deadline_date_input, deadline_time_input
    """
    ki = dict(key_info or {})
    sd, st = _split_iso_datetime(ki.get("start_time"))
    ed, et = _split_iso_datetime(ki.get("end_time"))
    dd, dtm = _split_iso_datetime(ki.get("deadline"))
    ki["start_date_input"], ki["start_time_input"] = sd, st
    ki["end_date_input"], ki["end_time_input"] = ed, et
    ki["deadline_date_input"], ki["deadline_time_input"] = dd, dtm
    return ki


def _get_datetime_str(date: str, time: str) -> str:
    """
    根据 HTML 表单的日期和时间输入，生成可读性强的日期时间字符串。
    若仅有日期则返回仅含日期的字符串；若两者皆无则返回空字符串。
    """
    if date and time:
        date_list = date.split("-")
        time_list = time.split(":")
        date_now_year = datetime.now().year
        if date_list[0] == str(date_now_year):
            date = f"{int(date_list[1])}月{int(date_list[2])}日"
        else:
            date = f"{int(date_list[0])}年{int(date_list[1])}月{int(date_list[2])}日"
        time = f"{int(time_list[0])}:{int(time_list[1]):02d}"

        return f"{date} {time}"
    
    elif date:
        date_list = date.split("-")
        date_now_year = datetime.now().year
        if date_list[0] == str(date_now_year):
            date = f"{int(date_list[1])}月{int(date_list[2])}日"
        else:
            date = f"{int(date_list[0])}年{int(date_list[1])}月{int(date_list[2])}日"
        return date
    else:
        return ""
