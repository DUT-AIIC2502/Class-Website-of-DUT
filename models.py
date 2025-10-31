"""定义数据模型"""
from flask_login import UserMixin, current_user
from ext import db, login_manager
# 直接从 sqlalchemy 导入，而不是通过 db 对象调用
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, inspect, Text, LargeBinary, Index, UniqueConstraint
from sqlalchemy.orm import relationship, backref, Mapped
from typing import List
# 日期类型
from datetime import datetime
# 生成随机数
import random

"""
反射表
"""
# 一个标志，用于确保反射只执行一次
_is_reflected = False


def reflect_db():
    """执行数据库反射，此函数应在应用启动时调用一次。"""
    global _is_reflected
    if not _is_reflected:
        print("Reflecting database tables...")
        db.reflect()
        _is_reflected = True
        print(f"Reflected tables: {list(db.metadata.tables.keys())}")


def refresh_db():
    """手动刷新数据库结构。"""
    global _is_reflected
    print("Refreshing database schema...")

    # 清除 SQLAlchemy 的检查器缓存
    inspector = inspect(db.engine)
    inspector.clear_cache()

    # 清除元数据并重新反射
    db.metadata.clear()
    db.reflect()

    _is_reflected = True  # 保持为 True，因为它已经被刷新了
    print(f"Refreshed tables: {list(db.metadata.tables.keys())}")


"""
以下模型为auth系统设计
"""


# Flask-Login 需要一个回调函数来从用户 ID 加载用户对象
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 用户-角色 多对多关联表
users_roles = db.Table(
    'users_roles',
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'))
)

# 权限-角色 多对多关联表
roles_permissions = db.Table(
    'roles_permissions',
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE')),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'))
)


class Permission(db.Model):
    __tablename__ = 'permissions'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(64), nullable=False)
    code: str = Column(String(32), unique=True, nullable=False)
    classification: str = Column(String(32), nullable=False)
    description: str = Column(db.String(255))

    def __repr__(self):
        return f'<Permission {self.name}>'


class Role(db.Model):
    __tablename__ = 'roles'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(64), unique=True, nullable=False)
    description: str = Column(String(255))

    # 注解这个字段是应该被映射为数据库列
    permissions: Mapped[List[Permission]] = relationship('Permission', secondary=roles_permissions,
                                                         backref=backref('roles', lazy='dynamic'))

    def __repr__(self):
        return f'<Role {self.name}>'

    def add_permission(self, permission):
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission):
        if permission in self.permissions:
            self.permissions.remove(permission)

    def has_permission(self, permission_name):
        return any(p.role_name == permission_name for p in self.permissions)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    real_name: str = Column(String(64), nullable=False)
    student_id: str = Column(String(64), nullable=False)
    password_hash: str = Column(String(255), nullable=False)
    telephone: str = Column(String(32))
    email: str = Column(String(64))
    create_time: datetime = Column(DateTime, default=datetime.now())
    status: bool = Column(Boolean, default=0, comment="0:禁用, 1:启用")

    roles: Mapped[List[Role]] = relationship('Role', secondary=users_roles,
                                             backref=backref('users', lazy='dynamic'))

    def __init__(self, student_id, real_name, password_hash):
        self.student_id = student_id
        self.real_name = real_name
        self.password_hash = password_hash

    def __repr__(self):
        return f'<User {self.real_name}>'

    # @property
    # def password(self):
    #     raise AttributeError('password is not a readable attribute')
    #
    # @password.setter
    # def password(self, password):
    #     self.password_hash = generate_password_hash(password)
    #
    # def verify_password(self, password):
    #     return check_password_hash(self.password_hash, password)

    def add_role(self, role):
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role):
        if role in self.roles:
            self.roles.remove(role)

    def has_role(self, role_name):
        return any(r.name == role_name for r in self.roles)

    def has_permission(self, permission_name):
        return any(role.has_permission(permission_name) for role in self.roles)


class LoginLogs(db.Model):
    __tablename__ = 'login_logs'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: int = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    ip_address: str = Column(String(64))
    login_time: datetime = Column(DateTime, default=datetime.now())

    def __init__(self, user_id, ip_address):
        self.user_id = user_id
        self.ip_address = ip_address


class CAPTCHA(db.Model):
    __tablename__ = 'CAPTCHA'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: int = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    user_name: str = Column(String(64))
    operation: str = Column(String(32))
    value: str = Column(String(32), nullable=False)
    create_time: datetime = Column(DateTime, default=datetime.now())

    def __init__(self, user_id, real_name, operation):
        # 生成随机的6位验证码
        random_int = random.randint(100000, 999999)

        # 生成数据
        self.user_id = user_id
        self.user_name = real_name
        self.operation = operation
        self.value = str(random_int)


"""
日志表
"""


class Logs(db.Model):
    __tablename__ = 'logs'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    # 日志等级：“Info”、“Warn”、“Error”，需单独输入
    level: str = Column(String(16), nullable=False)
    # 用户信息（直接由 current_user 对象生成）
    user_id: int = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    user_name: str = Column(String(64))
    user_role: str = Column(String(32))
    # 请求信息
    req_method: str = Column(String(16))            # 请求方法
    req_url: str = Column(String(255))              # 请求URL
    req_ip_address: str = Column(String(64))        # 请求IP地址
    # 操作相关信息
    oper_function: str = Column(String(64))         # 操作名称，一般为函数名
    oper_time: datetime = Column(DateTime, default=datetime.now())  # 操作时间（自动生成）
    oper_param: str = Column(Text)                  # 操作参数，包括 session、form_get，使用 jsonify 格式化
    # 错误信息
    error_short_desc: str = Column(String(255))     # 错误简短描述
    error_full_trace: str = Column(Text)            # 错误完整堆栈

    def __init__(self):
        if current_user.is_authenticated:
            self.user_id = current_user.id
            self.user_name = current_user.real_name
            user_roles = [role.name for role in current_user.roles]
            user_level = {
                "Root": 4,
                "Admin": 3,
                "User": 2,
                "Guest": 1
            }
            self.user_role = max(user_roles, key=lambda task: user_level[task])


"""
定时任务函数表
"""


class ScheduleFunctions(db.Model):
    __tablename__ = 'schedule_functions'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    func_id: str = Column(String(64), nullable=False, comment="任务的唯一ID")
    func: str = Column(String(64), nullable=False, comment="函数路径")  # 格式为“模块名:函数名”
    args: str = Column(String(255), comment="参数")  # 格式为“参数1,, 参数2,, ...”，之后转化为元组形式，按照顺序对应待执行函数的参数
    f_trigger: str = Column(String(64), comment="触发器类型", default='interval')  # interval, cron, date
    f_time: str = Column(String(64), nullable=False, comment="时间设置")  # 格式为“x, x, x”，分别对应“hour(s), minute(s), second(s)”

    def __init__(self):
        pass


"""
导航栏展示表
"""


class Services(db.Model):
    __tablename__ = 'services'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    order: int = Column(Integer, nullable=False, comment="显示顺序，数字越小越靠前")
    url: str = Column(String(64), nullable=False, comment="url路径")
    name: str = Column(String(64), nullable=False, comment="该url对应的功能")
    full_name: str = Column(String(64), nullable=False, comment="该url对应的功能全称")
    description: str = Column(String(255), comment="描述")
    file_name: str = Column(String(255), comment="图标文件名")
    # mimetype = db.Column(String(16))  # 存储图片的 MIME 类型，如 'image/png'
    # icon = Column(LargeBinary(16777216), comment="图标")


# =============== 学习笔记：书籍与章节结构 ===============

class StudyBook(db.Model):
    __tablename__ = 'study_books'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    # 建议与 URL 中 <book> 一致，作为稳定标识
    slug: str = Column(String(64), unique=True, nullable=False, index=True)
    title: str = Column(String(128), nullable=False)
    category: str = Column(String(64), nullable=False)  # 书籍类别（如数学、物理、计算机科学）
    description: str = Column(String(255))
    display_order: int = Column(Integer, default=0)     # 显示顺序
    is_published: bool = Column(Boolean, default=True)  # 是否发布
    created_at: DateTime = Column(DateTime, default=datetime.now)
    updated_at: DateTime = Column(DateTime, default=datetime.now, onupdate=datetime.now)    # 更新时间

    # 反向：book.nodes
    nodes: Mapped[list["ChapterNode"]] = relationship(
        "ChapterNode",
        backref=backref("book", lazy="joined"),
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<StudyBook slug={self.slug} title={self.title!r}>"


class ChapterNode(db.Model):
    __tablename__ = 'study_chapter_nodes'
    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # 所属书
    book_id: int = Column(Integer, ForeignKey('study_books.id', ondelete='CASCADE'), nullable=False, index=True)
    # 父节点（自引用）
    parent_id: int | None = Column(Integer, ForeignKey('study_chapter_nodes.id', ondelete='CASCADE'), nullable=True, index=True)

    # 展示标题与排序
    title: str = Column(String(128), nullable=False)
    display_order: int = Column(Integer, default=0, index=True)

    # 用于路径/锚点的短标识（仅字母数字与连字符，示例：limit、real-numbers）
    slug: str = Column(String(128), nullable=False)

    # 是否是页面节点（章节页面），否则为仅锚点/分组节点
    is_page: bool = Column(Boolean, default=False)
    # 作为锚点时使用（为空时退回 slug）
    anchor_slug: str | None = Column(String(128), nullable=True)

    # 可选：类型标记（volume/chapter/section/subsection…）
    node_type: str = Column(String(32), default='section')

    # 自引用 children
    children: Mapped[list["ChapterNode"]] = relationship(
        "ChapterNode",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ChapterNode.display_order"
    )

    __table_args__ = (
        # 同一本书内，父节点下 slug 唯一，便于生成稳定路径
        UniqueConstraint('book_id', 'parent_id', 'slug', name='uq_book_parent_slug'),
        Index('ix_book_parent_order', 'book_id', 'parent_id', 'display_order'),
    )

    def __repr__(self):
        return f"<ChapterNode book_id={self.book_id} title={self.title!r} slug={self.slug} is_page={self.is_page}>"



