import os
import bleach
from markdown import Markdown
from markupsafe import Markup

from flask import Blueprint, request, render_template, redirect, url_for, session, g

from decorators import role_required

learning_space_bp = Blueprint('learning_space', __name__,
                   url_prefix='/learning_space',
                   template_folder='templates')


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
    

@learning_space_bp.route('/study_notes/', methods=['GET', 'POST'])
@role_required("User")
def study_notes():
    """
    学习笔记主页
    """
    # 从数据库中获取已有的笔记，并制成 list
    if 1 == 1:
        pass

    if request.method == 'GET':
        # 如果没有指定书籍，显示学习笔记主页
        return render_template('learning_space/study_notes.html')
        
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.study_notes'))
    

@learning_space_bp.route('/study_notes/<book>/', methods=['GET', 'POST'])
@role_required("User")
def study_notes_of_book(book):
    """
    指定书籍的学习笔记页面
    """
    def render_markdown_file(md_dir: str, fname: str) -> tuple[Markup, Markup]:
        """读取并把 markdown 转为安全的 HTML，返回 (content_html, toc_html)"""

        # 读取 markdown 文件
        if 1 == 1:
            path = os.path.join(MD_DIR, fname)
            # 检查文件是否存在
            if not os.path.exists(path):
                return Markup("<p>未找到文档。</p>"), Markup("")

            # 读取 markdown 文件内容
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()

        # 使用 markdown 转换，启用 fenced_code、codehilite 等扩展
        if 1 == 1:
            md = Markdown(
                extensions=[
                    'fenced_code',        # 支持代码块
                    'codehilite',         # 代码高亮（Pygments）
                    'tables',             # 表格支持
                    'toc',                # 目录支持
                    'sane_lists',
                    'attr_list',
                    'md_in_html',
                    'pymdownx.arithmatex' # LaTeX 包装（配合 MathJax）
                ],
                extension_configs={
                    'pymdownx.arithmatex': {'generic': True},
                    'toc': {
                        'permalink': True,
                        'toc_depth': '2-4'
                    },
                    'codehilite': {
                        'guess_lang': False,
                        'noclasses': False
                    }
                }
            )
            html = md.convert(text)
            toc_html_raw = md.toc  # <div class="toc">...</div>

        # 清理 HTML
        if 1 == 1:
            # 定义允许的 HTML 标签
            allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', # 标题
                'pre', 'code',  # 代码块与行内代码
                'table', 'thead', 'tbody', 'tr', 'th', 'td', # 表格
                'span', 'div',  # 保留 codehilite 与 arithmatex 的包装
                'ul', 'ol', 'li' # 目录需要
            ]
            # 扩展允许的 HTML 属性
            allowed_attrs = dict(bleach.sanitizer.ALLOWED_ATTRIBUTES)
            allowed_attrs.update({
                'code': ['class'],
                'pre':  ['class'],
                'span': ['class'],
                'div':  ['class'],
                'a':    ['href', 'title', 'rel'],
                'h1': ['id'], 'h2': ['id'], 'h3': ['id'], 'h4': ['id'], 'h5': ['id'], 'h6': ['id']  # TOC 锚点
            })
            # 清理 HTML
            clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
            clean_toc = bleach.clean(toc_html_raw, tags=allowed_tags, attributes=allowed_attrs)

        return Markup(clean_html), Markup(clean_toc)

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
                content, toc_html = render_markdown_file(MD_DIR, f'{book}.md')
                return render_template(
                    'learning_space/study_notes_md.html',
                    book=book,
                    content=content,
                    toc_html=toc_html
                )

            else:
                # 如果书籍参数不认识，重定向回学习笔记主页
                return redirect(url_for('learning_space.study_notes'))
        
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.study_notes'))
