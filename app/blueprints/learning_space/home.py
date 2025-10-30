from . import learning_space_bp

from flask import request, render_template, redirect, url_for

from decorators import role_required


@learning_space_bp.route('/', methods=['GET', 'POST'])
@role_required("User")
def home():
    """
    学习空间主页
    """
    if request.method == 'GET':
        # 显示学习空间主页
        return render_template('learning_space/home.html')
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.home'))