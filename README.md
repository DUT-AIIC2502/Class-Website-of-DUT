# 班级网站

这是一个班级网站项目，提供信息化学生管理和丰富的学生服务。

# 安装和使用说明

## 安装步骤

1. 确保本地已安装了 git。
   - git 的安装：参考https://git-scm.com/book/zh/v2/%E8%B5%B7%E6%AD%A5-%E5%AE%89%E8%A3%85-Git。
2. 打开 cmd，切换到项目目录：`cd <你的项目的路径>`。
   - 注意：路径中最好不要有中文。
3. 从 Github 克隆项目到本地：`git clone https://github.com/DUT-AIIC2502/Class-Website-of-DUT.git`
4. 环境配置：
   1. python 库：
      1. 在 IDE 中运行终端，以下命令均在终端中运行（PowerShell环境）
      2. 用 python 自带的 venv 模块创建虚拟环境：`python -m venv venv`。
      3. 激活虚拟环境：`& .\venv\Scripts\activate`（成功后终端显示`(venv)`）
         - 如果激活失败，则大概率是因为 Windows PowerShell 执行策略限制，解决方法如下：
           1. 以管理员身份运行 PowerShell。
           2. 修改执行策略（临时或永久）：`Set-ExecutionPolicy RemoteSigned`。
           3. 按提示，输入`Y`确认。
           4. 再次尝试在项目目录激活虚拟环境。
        - 如果以上步骤不能解决问题，请自行查找资料解决。
      4. 下载项目所需的包：`pip install -r requirements.txt`
   2. 数据库：本项目使用 MySQL 作为数据库，使用前需要下载，并在 config.py 文件中进行数据库配置。
      1. 安装 MySQL：参考https://zhuanlan.zhihu.com/p/654087404。
         - 初始化用户密码时，需要设置为：`123456`。
      2. 使用 IDE 的数据库扩展，与本地的数据库建立连接。
         - 如果你的 root 用户的密码不是`123456`，请修改为`123456`，以免不得不修改配置文件。
      3. 新建数据库：`CREATE DATABASE CLASS_WEBSITE DEFAULT CHARACTER SET = 'utf8mb4';`
         - ！！！注意：数据库的名称为`CLASS_WEBSITE`，较之前版本有变更。
      4. 创建表`student_info`：相应语句位于`static/data/create_tables.sql`
         - 说明：第一次运行应用时，程序会自动创建大部分表，只有这个表需要手动创建。
         - 数据源：出于保护隐私需要，学生信息不提供给所有开发者。如要使用“学生信息管理”功能，可自行为`student_info`表插入数据。

## 使用方法

1. 使你的版本最新：`git fetch <remote>`，其中`<remote>`为你设置的连接的远程仓库的名称，一般为`origin`。
2. 分支操作：
   1. 如果你是用户，请切换分支到 master：`git checkout master`。
      - master 为主分支，包含成熟的应用。
      - 请不要随意提交更新至 master。
   2. 如果你是开发者，请切换分支到 dev：`git checkout dev`。
3. 在 run.py 文件中，设置运行环境。
   - 修改变量`branch`，如果是生产环境，则设置为`"main"`；如果是开发环境，则设置为`"dev"`。
4. 启动 run.py，即可在本地/局域网部署网站。
   - 通过终端启动应用：`python run.py`。
   - 关闭应用：按快捷键`Ctrl+C`。

# 项目结构和文件组织

## 项目结构

```
Class-Website-of-DUT/
├─ .gitignore                     # 忽略不提交的文件/目录（如 venv、.env）
├─ config.py                      # 应用配置（建议使用类 + 环境变量注入敏感值）
├─ decorators.py                  # 自定义装饰器（权限、缓存、日志等复用函数）
├─ ext.py                         # 第三方扩展初始化（db, apscheduler 等实例）
├─ models.py                      # ORM 模型 / 数据表定义
├─ README.md                      # 项目说明、安装与使用文档
├─ requirements.txt               # 依赖列表（pip install -r requirements.txt）
├─ run.py                         # 启动脚本（读取配置并运行 app，避免放业务逻辑）
│
├─ app/                           # 应用包：业务代码、蓝图、模板
│  ├─ __init__.py                 # 应用工厂和蓝图注册点
│  │
│  ├─ blueprints/                 # 按功能拆分的蓝图目录（每个蓝图自包含路由与模板）
│  │  ├─ __init__.py              # 蓝图统一注册（可为空或导入各蓝图）
│  │  │
│  │  ├─ auth/                    # 用户认证与管理
│  │  │  ├─ __init__.py
│  │  │  ├─ routes.py             # 登录/注册/权限等视图（业务逻辑应调用 service/common）
│  │  │  └─ templates/auth/       # auth 相关模板（login、register、用户详情等）
│  │  │
│  │  ├─ count_inform/            # 统计/通知相关蓝图
│  │  │  ├─ __init__.py
│  │  │  ├─ routes.py
│  │  │  └─ templates/count_inform/
│  │  │
│  │  ├─ info_management/         # 学生信息管理核心功能
│  │  │  ├─ __init__.py
│  │  │  ├─ routes.py             # 查询、导入、字段管理等视图
│  │  │  └─ templates/info_management/
│  │  │     ├─ info_management.html
│  │  │     └─ ...                # 详情/导入/字段操作模板
│  │  │
│  │  ├─ main/                    # 主页与系统初始化相关路由
│  │  │  ├─ __init__.py
│  │  │  ├─ routes.py             # create_tables、home、静态资源接口等
│  │  │  └─ templates/main/
│  │  │     └─ home.html
│  │  │
│  │  └─ new_blueprint/           # 示例/新模块占位（便于复制模板创建新功能）
│  │     ├─ __init__.py
│  │     ├─ routes.py
│  │     └─ templates/new_blueprint/
│  │
│  └─ templates/                  # 全局模板（如 base.html：布局、导航等）
│     └─ base.html
│
├─ common/                        # 公共工具与服务（供各蓝图复用）
│  ├─ __init__.py
│  ├─ flask_func.py               # 常用 Flask 辅助函数（获取用户信息、会话处理等）
│  └─ send_message.py             # 消息/通知发送封装
│
├─ others/                        # 非核心文件（任务清单、临时脚本）
│  ├─ bug列表.xlsx                # 问题/需求清单（建议移到 issue tracker）
│  └─ test.py                     # 辅助脚本（临时性）
│
├─ static/                        # 静态资源（前端样式、图片、以及静态 SQL）
│  ├─ CSS/
│  │  ├─ style.css
│  │  └─ ...                      # 各页面样式
│  ├─ images/
│  │  └─ ...                      # 图标资源（用于界面）
│  └─ sql/                        # 初始化 SQL 文件（create_tables、roles、permissions 等）
│     ├─ create_tables.sql
│     ├─ permissions.sql
│     ├─ roles.sql
│     ├─ schedule_functions.sql
│     └─ services.sql
│
└─ venv/                          # 本地虚拟环境（应加入 .gitignore，不提交到仓库）      
```

# 贡献指南

## 如何为项目做出贡献？

登录github：参考https://blog.csdn.net/emem_0724/article/details/148242376。

（以下步骤中的 git 操作可用任意 IDE 的图形化界面执行）

1. 了解项目
   1. 阅读项目的文档和代码，了解项目的目标、架构和设计原则。
   2. 参与项目的讨论和会议，与项目成员交流。
2. 找到贡献的机会
   1. 查看项目的问题跟踪器，找到你可以解决的问题。
   2. 注意项目的未来计划和里程碑，看看哪些功能你可以贡献。
3. 贡献代码
   1. 切换分支为 dev：`git checkout dev`。
   2. 确保你的代码为最新：`git fetch https://github.com/DUT-AIIC2502/Class-Website-of-DUT.git`。
   3. 在本地开发和测试你的代码。
   4. 提交 Pull Request：`git push origin dev`。

### 约定与最佳实践

- 配置与密钥：
  - 在 config.py 中使用类与默认值，敏感变量通过 .env（开发）或环境变量（生产）注入。
  - .env 放在 .gitignore 中，不要提交到版本库。
- 数据库：
  <!-- - 使用迁移工具（Flask-Migrate / Alembic）管理 schema，更改需生成 migration 并提交。 -->
  - 将创建表的 SQL 放到 static/data，说明何时需要手动执行（README 已有说明）。
- 代码风格：
  - 遵循 PEP8，函数/模块命名使用 snake_case，类使用 PascalCase。
  - 在重大改动前在 dev 分支开发并通过测试后发 PR 到主干分支（dev -> main/master）。
- 提交与分支策略：
  - 保持 master/main 用于生产，dev 用于日常开发。Feature 分支以 feature/xxx 命名。
- 文档与注释：
  - 每个蓝图、视图函数和复杂模块要有简短说明，接口和参数在 docs 中记录。
- 测试覆盖：
  - 关键业务模块（auth、info_management）需有单元测试与集成测试；数据库相关操作使用测试数据库或 mock。

## 提交问题和拉取请求的流程

1. 提交问题（Submitting Issues）
   1. 使用明确、具体的标题描述问题。
   2. 提供问题的详细描述，包括重现步骤、预期行为和实际行为。
   3. 如果可能，附加屏幕截图或动画来说明问题。
2. 提交拉取请求（Submitting Pull Requests）
   1. 使用清晰的标题描述拉取请求的目的。
   2. 在描述中详细说明你的更改和这些更改的必要性。
   3. 确保你的代码符合项目的编码标准和风格指南。

# 许可证

详见 LICENSE.txt 文件

# 数据类型说明

注意：以下内容可能存在错误！

1. `session`：类似于字典，有以下键：

   1. info_management系统
      1. `table_name`：储存表名
      2. `table_field`：储存该表的字段信息(字段、中文名)
         对应`table_field`
      3. `form_get`：储存“info_management”执行搜索操作时，提交的表单值
         对应`form_get`
      4. `fields_to_select`：复选框选中的字段
         对应`fields`
      5. `table`：搜索结果表
         对应`table`
      6. `whether_readonly`：int，标记是否只读。0：可编辑。1：只读。
      7. `student_ids`：学号列表，其中学号以str类型储存

   2. auth系统
      1. `user_info`：dict，储存以下信息
         1. `id`：数据库中的id
         2. `user_id`：实际上为学号
         3. `user_name`：用户的真实姓名
         4. `user_top_role`：用户的最顶级身份，用于展示
         5. `user_roles`：一维list，用户的所有身份
      2. `user_id`：学号，用于标定详细页面
      3. `form_get`：dict，保存表单数据，用于渲染页面
      4. `captcha_id`：int，用于匹配验证码
      5. `whether_hidden`：int，用于判断是否需要隐藏“学号”输入框

2. `sql`：string类型，用于储存需要执行的 mysql 语句。

3. `mark_list`：list，用于标记需要默认选中的项。
有2项：`mark_list[0]`为一个一维元组，包含需要被默认选中的选项；
`mark_list[1]`为string，包含对应的属性值。

`checkboxs_to_mark`和`option_to_mark`：一维tuple，用于标记。

## info_management.bp部分

### 关于 info_management.html 的数据

#### 后端

##### `GET`部分

1. `result_field`：二维list，储存数据表的字段数据。

| \        | 0   | 1   | ... | n   |
|----------|-----|-----|-----|-----|
| 0（字段）    |     |     |     |     |
| 1（字段中文名） |     |     |     |     |

##### `POST`部分

1. `form_get`：dict，是将表单提交的数据转化为 python 的 dict。其中，关于复选框的值是错误的。
2. `fileds`：一维list，包含表单选中的所有字段（English）。之后，转化为中文名，传输给前端，用于渲染查询结果的表头。
3. `infos`：一维list，包含表格表单选中的所有信息（学号）。
4. `table_field`：二维list，从数据库获取，储存数据表的字段和字段名。
5. `result_basic_info`：二维tuple，从数据库获取，包含所有学生的姓名、学号信息。
6. `result_table`：二维tuple，从数据库获取，包含查询结果，每一个元素都是一名学生的信息。

#### 渲染部分

1. `fileds`：对应`result_field_list`
   
| \                     | fileds.0 | fileds.1 | ... | fileds.n |
|-----------------------|----------|----------|-----|----------|
| row.0（字段）             |          |          |     |          |
| row.1（字段名）            |          |          |     |          |
| row.2（标记：复选框是否需要默认选择） |          |          |     |          |
| rwo.3（标记：下拉框是否需要默认选择） |          |          |     |       

2. `field_selected`：对应`fields`，一维list，包含选中的字段

3. `table`：对应`result_table`

| \               | table.0 | table.1 | ... | table.i |
|-----------------|---------|---------|-----|---------|
| row_value.0（姓名） |         |         |     |         |
| row_value.1（学号） |         |         |     |         |
| ...             |         |         |     |         |
| row_value.j     |         |         |     |       


### 前端传入（表单）

1. `request.form`：ImmutableMultiDict，包含表单中的各项数据，`name`和`value`一一对应。


### 关于 detail_info 的数据

1. `result_student`：是一个一维

#### 前端传入（表单）

#### 后端渲染
1. `fields_values`：应当是一个二维列表

| \                  | fields_values.0 | fields_values.1 | ... | fields_values.n |
|--------------------|-----------------|-----------------|-----|-----------------|
| field.0（字段）        |                 |                 |     |                 |
| field.1（字段名）       |                 |                 |     |                 |
| field.2（字段的值）      |                 |                 |     |                 |

[//]: # (| field.3（标记：是否需要锁定） |                 |                 |     |                 |)

### 关于 auth_delete 的数据

1. `result_student`：二维list，每一项包括：（姓名，学号）
