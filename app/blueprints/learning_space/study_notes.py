from . import learning_space_bp
from .helpers_md import get_chapters_for_book, render_markdown_file
from .helpers_db import get_all_books

import os
import pickle
from flask import request, render_template, redirect, url_for, session

from decorators import role_required


@learning_space_bp.route('/study_notes/', methods=['GET', 'POST'])
@role_required("User")
def study_notes():
    """
    学习笔记主页
    """
    # 从数据库中获取已有的笔记，并制成 list
    all_books = get_all_books()
    session['all_books'] = pickle.dumps(all_books)

    if request.method == 'GET':
        # 如果没有指定书籍，显示学习笔记主页
        return render_template('learning_space/study_notes.html', all_books=all_books)
        
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.study_notes'))


@learning_space_bp.route('/study_notes/<book>/<chapter_now>/', methods=['GET', 'POST'])
@role_required("User")
def study_notes_of_book(book, chapter_now):
    """
    指定书籍的学习笔记页面
    :param book: 书籍标识符
    :param chapter: 章节标识符
    """
    if request.method == 'GET':
        if book is None:
            # 如果没有指定书籍，显示学习笔记主页
            return redirect(url_for('learning_space.study_notes'))
        if chapter_now is None:
            # 如果没有指定章节，重定向回书籍主页
            return redirect(url_for('learning_space.study_notes_of_book', book=book, chapter='introduction'))

        MD_DIR = os.path.join(os.path.dirname(__file__), 'markdowns', book)

        # 获取该书籍的章节列表
        chapters = get_chapters_for_book(book)
        # 获取当前章节的内容和目录
        content, toc_html = render_markdown_file(MD_DIR, f'{chapter_now}.md')

        return render_template(
            'learning_space/study_notes_of_book.html',
            all_books=pickle.loads(session.get('all_books', pickle.dumps([]))),
            book=book,
            chapter_now=chapter_now,
            chapters=chapters,
            content=content,
            toc_html=toc_html
        )
        
    elif request.method == 'POST':
        # 处理表单提交
        return redirect(url_for('learning_space.study_notes'))


