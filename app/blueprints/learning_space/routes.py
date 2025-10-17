from flask import Blueprint, request, render_template, redirect, url_for, session, g

from decorators import role_required

learning_space_bp = Blueprint('learning_space', __name__,
                   url_prefix='/learning_space',
                   template_folder='templates')


@learning_space_bp.route('/', methods=['GET', 'POST'])
@role_required("User")
def home():
    if request.method == 'GET':
        # 显示学习空间主页
        return render_template('learning_space/home.html')
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.home'))
    

@learning_space_bp.route('/study_notes/', methods=['GET', 'POST'])
@role_required("User")
def study_notes():
    if request.method == 'GET':
        # 从查询字符串读取 ?book=math_analysis
        book = request.args.get('book', None, type=str)
        
        if book is None:
            # 如果没有指定书籍，显示学习笔记主页
            return render_template('learning_space/study_notes.html')
        else:
            # 根据指定的书籍显示对应的笔记页面
            if book == 'math_analysis':
                return render_template('learning_space/study_notes_math_analysis.html')
            
            else:
                # 如果书籍参数不认识，重定向回学习笔记主页
                return redirect(url_for('learning_space.study_notes'))
        
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.study_notes'))
