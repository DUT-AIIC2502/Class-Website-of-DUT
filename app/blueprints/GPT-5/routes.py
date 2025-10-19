from flask import Blueprint, current_app, request, render_template, jsonify
from common.openai_service import OpenAIService


new_bp = Blueprint('new', __name__,
                   url_prefix='/new',
                   template_folder='templates')


@new_bp.route('/', methods=['GET', 'POST'])
def new_function():
    # 演示：如果在配置中启用了 GPT-5 并提供了 API key，则调用 OpenAI
    if request.method == 'POST':
        # 从表单或 JSON 中读取 prompt
        if request.is_json:
            prompt = request.json.get('prompt')
        else:
            prompt = request.form.get('prompt')

        enable = current_app.config.get('ENABLE_GPT5', False)
        api_key = current_app.config.get('OPENAI_API_KEY') or None

        if not enable:
            return jsonify({'ok': False, 'error': 'GPT-5 功能未启用（ENABLE_GPT5=False）'}), 400

        svc = OpenAIService(api_key=api_key, model='gpt-5')
        if not svc.available():
            return jsonify({'ok': False, 'error': 'OpenAI SDK 不可用或未配置 API Key'}), 500

        result = svc.chat(prompt or 'Hello from demo')
        if result is None:
            return jsonify({'ok': False, 'error': '调用 GPT-5 失败或返回为空'}), 500

        return jsonify({'ok': True, 'result': result})

    # GET: 返回一个简单的示例页面（如果存在模板）
    try:
        return render_template('new_blueprint/new_heml.html')
    except Exception:
        # 模板可能不存在，返回简单说明
        return "New blueprint - send POST with 'prompt' to get GPT-5 response"


@new_bp.get('/gpt5/status')
def gpt5_status():
    """返回当前 GPT-5 开关状态。
    注意：这是运行时内存态，重启进程后将回到默认配置。
    """
    enabled = current_app.config.get('ENABLE_GPT5', False)
    return jsonify({'ok': True, 'enable_gpt5': bool(enabled)})


@new_bp.post('/gpt5/toggle')
def gpt5_toggle():
    """切换或设置 GPT-5 开关状态。
    接受 JSON 或表单：{"enable_gpt5": true/false}
    """
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        value = payload.get('enable_gpt5')
    else:
        value = request.form.get('enable_gpt5')

    # 将入参转为布尔值
    if isinstance(value, str):
        value_lower = value.strip().lower()
        if value_lower in ('1', 'true', 'yes', 'on'):
            enabled = True
        elif value_lower in ('0', 'false', 'no', 'off', ''):
            enabled = False
        else:
            return jsonify({'ok': False, 'error': '非法参数：enable_gpt5'}), 400
    else:
        enabled = bool(value)

    current_app.config['ENABLE_GPT5'] = enabled
    return jsonify({'ok': True, 'enable_gpt5': enabled})
