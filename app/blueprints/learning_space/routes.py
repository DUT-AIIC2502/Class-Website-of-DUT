import os
import markdown
import bleach
from markupsafe import Markup

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
        # 如果没有指定书籍，显示学习笔记主页
        return render_template('learning_space/study_notes.html')
        
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.study_notes'))
    

@learning_space_bp.route('/study_notes/<book>/', methods=['GET', 'POST'])
@role_required("User")
def study_notes_of_book(book):
    def render_markdown_file(fname: str) -> Markup:
        """读取并把 markdown 转为安全的 HTML（返回 Markup 可直接在模板用 |safe 输出）"""
        path = os.path.join(MD_DIR, fname)
        if not os.path.exists(path):
            return Markup("<p>未找到文档。</p>")

        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        # 使用 markdown 转换，启用 fenced_code、codehilite 等扩展
        html = markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables', 'toc'])

        # 将 frozenset 转为 list 或使用集合并集
        allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + ['h1', 'h2', 'h3', 'pre', 'code', 'table', 'thead', 'tbody', 'tr', 'th', 'td']
        allowed_attrs = dict(bleach.sanitizer.ALLOWED_ATTRIBUTES)
        allowed_attrs.update({'code': ['class'], 'span': ['class'], 'a': ['href', 'title', 'rel']})

        clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
        return Markup(clean_html)

    if request.method == 'GET':
        if book is None:
            # 如果没有指定书籍，显示学习笔记主页
            return redirect(url_for('learning_space.study_notes'))
        else:
            """从数据库搜索具有的笔记列表"""
            if 1 == 1:
                notes_list = ['math_analysis', ]

            MD_DIR = os.path.join(os.path.dirname(__file__), 'templates', 'learning_space', 'md')  # 放.md的目录（可自定义）

            # 根据指定的书籍显示对应的笔记页面
            if book in notes_list:
                content = render_markdown_file(f'{book}.md')
                return render_template('learning_space/study_notes_md.html', book=book, content=content)

            else:
                # 如果书籍参数不认识，重定向回学习笔记主页
                return redirect(url_for('learning_space.study_notes'))
        
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.study_notes'))
