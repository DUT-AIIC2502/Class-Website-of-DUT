# 应用功能

1. 为数据库添加数据：

    输入姓名/学号，然后在下面的输入框内输入/选择对应的“字段”，即可将相应的数据插入对应的字段

2. 在数据库中查询数据：

   输入姓名，选中复选框，点击查询，即可得到相应的表格。



# 数据类型说明

1. `session`：类似于字典，有以下键：

   1. `table_name`：储存表名
   2. `table_field`：储存该表的字段信息(字段、中文名)
      对应`table_field`
   3. `info_management_select_form_data`：储存“info_management”执行搜索操作时，提交的表单值
      对应`form_get`
   4. `info_management_select_fields_data`：复选框选中的字段
      对应`fields`
   5. `info_management_select_table_data`：搜索结果表
      对应`table`
   6. `whether_readonly`：int，标记是否只读。0：可编辑。1：只读。
   7. `student_ids`：学号列表，其中学号以str类型储存

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

2. `field_select`：对应`fields`，一维list，包含选中的字段

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

# 疑惑

1. 使用form+button无法成功跳转页面