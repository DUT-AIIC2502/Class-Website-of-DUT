import os, json, httpx

long_text = "未来书院形象片演员招募通知 \n" \
"亲爱的同学们：\n" \
"未来书院形象片即将开拍！现面向书院全体大一同学招募出镜演员，用你的风采，共同讲述书院故事。\n" \
"【拍摄安排】\n" \
"拍摄地点： 未来书院（1舍）\n" \
"招募时段与人数：\n" \
"上午场： 10:00 - 12:00，需8人\n" \
"下午场A： 13:30 - 15:30，需8人\n" \
"下午场B： 15:30 - 17:30，需8人\n" \
"【重要说明】\n" \
"本次拍摄与周六的团校培训时间不冲突，辅导员老师将统一协调，请有团校培训任务的同学无需担心，放心报名！\n" \
"【报名方式】\n" \
"我们期待你的加入！请尽快扫描下方二维码进入招募群，并修改群昵称为“姓名+报名时段”（如：王小明-上午场）。名额有限，先到先得！\n" \
"用镜头记录美好，未来书院因你更精彩！\n" \
"\n" \
"有机会登上学院、学院及其他官方平台的大屏幕，快快报名参加吧！\n"

def main(text):
    base_url = (os.getenv("VOLCENGINE_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
    api_key = (os.getenv("VOLCENGINE_API_KEY") or "").strip()
    endpoint_id = (os.getenv("VOLCENGINE_ENDPOINT_ID") or "").strip()

    print(f"BASE_URL={base_url}")
    print(f"ENDPOINT_ID startswith ep-: {endpoint_id.startswith('ep-')}")
    print(f"API_KEY present: {bool(api_key)}")

    if not api_key or not endpoint_id.startswith("ep-"):
        raise SystemExit("环境变量不完整，检查 VOLCENGINE_API_KEY / VOLCENGINE_ENDPOINT_ID")

    if 1 == 1:
        system_prompt = (
            "你是信息抽取助手。请从中文活动通知原文中抽取关键信息并只严格输出 JSON 对象。\n"
            "字段与要求：\n"
            "- title: 通知标题，简要概括\n"
            "- theme: 活动主题，若无可留空\n"
            "- start_time: ISO 8601，如 2025-10-23T15:00:00+08:00；若只给出日期，时间可用 00:00:00\n"
            "- end_time: ISO 8601；若无则为 null\n"
            "- location: 活动地点，无则空字符串\n"
            "- participants: 参与人员（人群或名单）\n"
            "- organizer: 组织者，无则为 null\n"
            "- contact: 联系方式（电话/微信/邮箱），无则为 null\n"
            "- deadline: 报名截止时间（ISO 8601），无则为 null\n"
            "- raw_time_text: 原文中与时间相关的关键短语，尽量原样摘录，找不到则为 null\n"
            "- notes: 备注或注意事项，无则为 null\n"
            "- details: 详细说明，使用单个字符串，按行分点（用换行分隔），行首使用“- ”标志。要求不与以上字段重复，且剔除无用信息（如客套话等）\n"
            "- confidence: 0~1 的置信度（浮点数）\n"
            "规则：\n"
            "1) 严格输出一个 JSON 对象，不要添加解释或多余文本。\n"
            "2) 所有日期时间尽量解析为含 +08:00 时区的 ISO 8601；实在无法解析则置为 null 并在 notes 中说明。\n"
            "3) 若字段缺失，用空字符串或 null（见上）。\n"
        )

        user_prompt = (
            "原始文本：\n"
            f"{text}\n\n"
            "请按上述字段与要求输出 JSON 对象。"
        )

    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": endpoint_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "top_p": 1.0,
        # 如果报 400 且提示不支持 json_object，请注释下一行后重试
        # "response_format": {"type": "json_object"},
    }

    # 禁用系统代理，避免被无效代理劫持；如需代理，请自行设置 proxies 参数
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=30.0)
    with httpx.Client(timeout=timeout, trust_env=False) as client:
        print("→ 发起请求...")
        resp = client.post(url, headers=headers, json=payload)
        print(f"HTTP {resp.status_code}")
        try:
            data = resp.json()
        except Exception:
            print("响应文本：", resp.text[:500])
            resp.raise_for_status()
            return

    if resp.status_code >= 400:
        print("错误详情：", json.dumps(data, ensure_ascii=False, indent=2))
        raise SystemExit("冒烟测试失败")

    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        print("响应 JSON：", json.dumps(data, ensure_ascii=False, indent=2))
        raise SystemExit("响应格式异常")
    print("模型输出：", content)
    print("✅ 连接正常（若输出为“pong”更佳）")

if __name__ == "__main__":
    main(long_text)