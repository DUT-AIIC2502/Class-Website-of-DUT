"""定义数据模型"""
from flask_login import UserMixin
from ext import db, login_manager
# 直接从 sqlalchemy 导入，而不是通过 db 对象调用
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref, Mapped
from typing import List
# 日期类型
from datetime import datetime


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
    create_time: datetime = Column(DateTime, default=datetime.now)
    status: bool = Column(Boolean, default=1, comment="0:禁用, 1:启用")

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
    login_time: datetime = Column(DateTime, default=datetime.now)

    def __init__(self, user_id, ip_address):
        self.user_id = user_id
        self.ip_address = ip_address

