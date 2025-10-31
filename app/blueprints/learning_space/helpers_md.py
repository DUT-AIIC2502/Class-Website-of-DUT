from __future__ import annotations

import os
import re
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


def _protect_segments(html: str):
    """
    保护 code/pre/script/style 等片段，避免正则替换误伤。
    返回 (占位后的 html, 占位字典)
    """
    patterns = [
        (r'<pre\b[^>]*>[\s\S]*?<\/pre>', 'PRE'),
        (r'<code\b[^>]*>[\s\S]*?<\/code>', 'CODE'),
        (r'<script\b[^>]*>[\s\S]*?<\/script>', 'SCRIPT'),
        (r'<style\b[^>]*>[\s\S]*?<\/style>', 'STYLE'),
    ]
    stash = {}
    idx = 0
    def repl_factory(tag):
        nonlocal idx
        def _repl(m):
            nonlocal idx
            key = f"__PLACEHOLDER_{tag}_{idx}__"
            stash[key] = m.group(0)
            idx += 1
            return key
        return _repl
    for pat, tag in patterns:
        html = re.sub(pat, repl_factory(tag), html, flags=re.IGNORECASE)
    return html, stash


def _restore_segments(html: str, stash: dict):
    for key, val in stash.items():
        html = html.replace(key, val)
    return html


def _fix_unconverted_mark(html: str) -> str:
    """
    兜底把未被 pymdownx.mark 识别的 ==…== 转为 <mark>…</mark>。
    避免替换 code/pre/script/style 内部内容。
    """
    html, stash = _protect_segments(html)
    # 避免跨段落的贪婪匹配
    html = re.sub(r'==(.+?)==', r'<mark>\1</mark>', html, flags=re.DOTALL)
    html = _restore_segments(html, stash)
    return html


def _blockquote_to_admonition(html: str) -> str:
    """
    将以 @info/@note/@tip 开头的 blockquote 转换为标准 admonition 结构，支持嵌套。
    兼容两种写法：
      > @info
      > 内容...
    和
      > @info 自定义标题
      > 内容...
    """
    label_map = {
        'info': ('info', '信息'),
        'note': ('note', '笔记'),
        'tip':  ('tip',  '提示'),
    }

    # 先处理带标题的版本：@info 标题
    pat_title = re.compile(
        r'<blockquote>\s*<p>@(info|note|tip)\s+([^<]+?)</p>\s*([\s\S]*?)</blockquote>',
        flags=re.IGNORECASE
    )
    # 不带标题版本：仅 @info
    pat_plain = re.compile(
        r'<blockquote>\s*<p>@(info|note|tip)\s*</p>\s*([\s\S]*?)</blockquote>',
        flags=re.IGNORECASE
    )

    def repl_title(m):
        kind = m.group(1).lower()
        custom_title = m.group(2).strip()
        body = m.group(3)
        cls, _default = label_map.get(kind, ('note', '笔记'))
        return f'<div class="admonition {cls}"><p class="admonition-title">{custom_title}</p>{body}</div>'

    def repl_plain(m):
        kind = m.group(1).lower()
        body = m.group(2)
        cls, default_title = label_map.get(kind, ('note', '笔记'))
        return f'<div class="admonition {cls}"><p class="admonition-title">{default_title}</p>{body}</div>'

    # 递归/多轮替换，直到没有可替换的 blockquote（保证嵌套 blockquote 也被转为嵌套 admonition）
    prev = None
    while prev != html:
        prev = html
        html = re.sub(pat_title, repl_title, html)
        html = re.sub(pat_plain, repl_plain, html)

    return html


def _fix_math_block_dollars(html: str) -> str:
    """
    兜底把 html 中仍然保留的 $$…$$ 公式块替换为 arithmatex 块（MathJax v3 友好），
    以修复某些环境（尤其是引用块里）未正确被扩展捕获的问题。
    仅处理块级 $$…$$，不处理行内 $…$。
    """
    html, stash = _protect_segments(html)
    # 将 <p>$$\n ... \n$$</p> 等情况统一替换
    def repl_block(m):
        expr = m.group(1).strip()
        # 用 \[ \] 包裹，交由 MathJax 解析
        return f'<div class="arithmatex">\\[ {expr} \\]</div>'
    html = re.sub(r'\$\$\s*([\s\S]+?)\s*\$\$', repl_block, html)
    html = _restore_segments(html, stash)
    return html


def _postprocess_content(content_html: str) -> str:
    """
    综合美化与修复：加粗变红、兜底 == 下划线、blockquote -> admonition、修复 $$ 公式块。
    """
    content_html = _fix_unconverted_mark(content_html)
    content_html = _blockquote_to_admonition(content_html)
    content_html = _fix_math_block_dollars(content_html)
    return content_html


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
            'p',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'pre', 'code',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'span', 'div',
            'ul', 'ol', 'li',
            'details', 'summary',
            'br', 'hr',
            'mark',
            'blockquote'  # 允许 blockquote 通过，便于后续 @info/@note/@tip 转换为 admonition
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

    # 美化与修复（在 bleach 清洗之后进行后处理）
    clean_html = Markup(_postprocess_content(str(clean_html)))

    return Markup(clean_html), Markup(clean_toc)
