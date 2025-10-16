insert into permissions (id, name, code, classification, description)
values  (1, '创建新用户', 'user_create', 'management', null),
        (2, '编辑用户信息', 'user_edit', 'management', null),
        (3, '删除用户', 'user_delete', 'management', null),
        (4, '查看用户列表', 'user_view', 'management', null),
        (5, '查看用户详细信息', 'user_view_detail', 'management', null),
        (6, '创建新角色', 'role_create', 'management', null),
        (7, '编辑角色信息和权限', 'role_edit', 'management', null),
        (8, '删除角色', 'role_delete', 'management', null),
        (9, '分配角色', 'role_assign', 'management', '将角色分配给用户或从用户移除角色'),
        (10, '管理权限本身', 'permission_manage', 'management', '通常只有超级管理员拥有'),
        (11, '修改系统全局配置', 'system_config_edit', 'management', null),
        (12, '查看系统日志', 'log_view', 'management', null);