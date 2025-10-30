from __future__ import annotations

import os
import bleach
from markdown import Markdown
from markupsafe import Markup
from typing import List, Dict, Optional
from models import db, StudyBook, ChapterNode


def _build_path(node: ChapterNode, current_page_slug: Optional[str]) -> Optional[str]:
    """
    生成与前端一致的相对 path：
    - 章节页面节点：/{slug}/
    - 非页面（锚点）节点：/{最近的页面slug}/#{anchor}
    - 纯分组节点（无页面且无锚点）返回 None（前端不渲染成链接）
    """
    if node.is_page:
        return f"/{node.slug}/"
    # 作为锚点
    anchor = node.anchor_slug or node.slug
    if current_page_slug and anchor:
        return f"/{current_page_slug}/#{anchor}"
    return None


def _node_to_dict(node: ChapterNode, current_page_slug: Optional[str]) -> Dict:
    # 若命中页面节点，更新当前页面 slug
    next_page_slug = node.slug if node.is_page else current_page_slug
    d: Dict = {
        "id": node.slug,                  # 使用 slug 作为稳定 id
        "title": node.title,
    }
    path = _build_path(node, current_page_slug)
    if path:
        d["path"] = path
    # children
    if node.children:
        d["children"] = [_node_to_dict(child, next_page_slug) for child in node.children]
    return d


def get_chapters_for_book(book_slug: str) -> List[Dict]:
    """
    输入书籍 slug，返回 chapters 列表（与前端期望结构一致）
    """
    book: StudyBook | None = StudyBook.query.filter_by(slug=book_slug).first()
    if not book:
        return []

    # 取整棵树（根：parent_id is NULL），按 display_order 已在关系中排序
    roots: List[ChapterNode] = ChapterNode.query.filter_by(book_id=book.id, parent_id=None) \
        .order_by(ChapterNode.display_order, ChapterNode.id).all()

    chapters: List[Dict] = [_node_to_dict(root, current_page_slug=None) for root in roots]
    return chapters


# 可选：初始化样例数据（开发期）
def seed_book_limit() -> None:
    """
    示例：构造与当前 math_analysis-limit.md 对应的一棵树
    book.slug = 'math_analysis'
    """
    book = StudyBook.query.filter_by(slug='math_analysis').first()
    if not book:
        book = StudyBook(slug='math_analysis', title='数学分析')
        db.session.add(book)
        db.session.flush()

    # 卷
    vol1 = ChapterNode(book_id=book.id, parent_id=None, title='数学分析（第一册）', slug='introduction', is_page=True, node_type='volume', display_order=1)
    db.session.add(vol1)

    # 第1章：极限（页面）
    ch1 = ChapterNode(book_id=book.id, parent=vol1, title='第1章：极限', slug='limit', is_page=True, node_type='chapter', display_order=1)
    db.session.add(ch1)

    # 1.1、1.2、1.3（锚点）
    s11 = ChapterNode(book_id=book.id, parent=ch1, title='1.1 实数', slug='real-numbers', is_page=False, anchor_slug='real-numbers', node_type='section', display_order=1)
    s12 = ChapterNode(book_id=book.id, parent=ch1, title='1.2 数列极限', slug='sequence-limits', is_page=False, anchor_slug='sequence-limits', node_type='section', display_order=2)
    s13 = ChapterNode(book_id=book.id, parent=ch1, title='1.3 函数极限', slug='function-limits', is_page=False, anchor_slug='function-limits', node_type='section', display_order=3)
    db.session.add_all([s11, s12, s13])

    db.session.commit()


def render_markdown_file(md_dir: str, fname: str) -> tuple[Markup, Markup]:
    """
    读取并把 markdown 转为安全的 HTML，返回 (content_html, toc_html)
    
    :param md_dir: markdown 文件所在目录
    :param fname: markdown 文件名
    :return: (content_html, toc_html)
    其中 content_html 是转换后的 HTML 内容，toc_html 是生成的目录 HTML
    """

    # 读取 markdown 文件
    if 1 == 1:
        path = os.path.join(md_dir, fname)
        if not os.path.exists(path):
            return Markup("<p>未找到文档。</p>"), Markup("")

        # 读取 markdown 文件内容
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

    # 使用 markdown 转换，启用 fenced_code、codehilit 等扩展和 callout 相关扩展
    if 1 == 1:
        md = Markdown(
            extensions=[
                'fenced_code',          # 支持代码块
                'codehilite',           # 代码高亮（Pygments）
                'tables',               # 表格支持
                'toc',                  # 目录支持
                'sane_lists',           # 允许更安全的列表
                'attr_list',            # 支持给元素添加属性，如 {.class #id}
                'md_in_html',           # 允许在 HTML 中使用 markdown 语法
                'pymdownx.arithmatex',  # 数学公式支持
                'admonition',           # !!! note / !!! warning / !!! tip ...
                'pymdownx.details',     # ??? note 折叠式提示块
                'pymdownx.superfences', # 让提示块内可嵌套代码块等
                'pymdownx.mark'         # 支持 ==mark== 语法（将生成 <mark> 标签）
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
        toc_html_raw = md.toc

    # 清理 HTML：允许 callout 所需标签与 class
    if 1 == 1:
        # 定义允许的 HTML 标签
        allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
            'p',  # 关键：允许段落标签，否则会被转义为文本 “<p>”
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'pre', 'code',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'span', 'div',
            'ul', 'ol', 'li',
            'details', 'summary',
            'br', 'hr',
            'mark'   # 允许 <mark>，用于 ==text== 转换
        ]
        # 去重，保持稳定
        allowed_tags = sorted(set(allowed_tags))

        # 扩展允许的 HTML 属性
        allowed_attrs = dict(bleach.sanitizer.ALLOWED_ATTRIBUTES)
        allowed_attrs.update({
            'code': ['class'],
            'pre':  ['class'],
            'span': ['class'],
            'div':  ['class'],     # admonition 会生成 <div class="admonition note"> ...
            'p':    ['class'],     # <p class="admonition-title">Title</p>
            'a':    ['href', 'title', 'rel'],
            'h1': ['id'], 'h2': ['id'], 'h3': ['id'], 'h4': ['id'], 'h5': ['id'], 'h6': ['id'],
            'details': ['class', 'open'],
            'summary': ['class'], 
            'mark': ['class']    # 允许 <mark> 的 class 属性
        })
        # 清理 HTML
        clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
        clean_toc = bleach.clean(toc_html_raw, tags=allowed_tags, attributes=allowed_attrs)

    return Markup(clean_html), Markup(clean_toc)
