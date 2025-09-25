# 应用功能

1. 为数据库添加数据：

    输入姓名/学号，然后在下面的输入框内输入/选择对应的“字段”，即可将相应的数据插入对应的字段

2. 在数据库中查询数据：

   输入姓名，选中复选框，点击查询，即可得到相应的表格。



# 数据类型说明

1. `sql_str`：string类型，用于储存需要执行的 mysql 语句。

2. `checkboxs_to_mark`和`option_to_mark`：一维tuple，用于标记需要被默认选中的选项。

## 关于 info_management.html 的数据

#### `GET`部分

1. `result_field_tup`：二维tuple，储存数据表的字段数据。

   - `result_field_list`：二维list

| \        | 0   | 1   | ... | n   |
|----------|-----|-----|-----|-----|
| 0（字段）    |     |     |     |     |
| 1（字段中文名） |     |     |     |     |

#### `POST`部分

1. `form_get`：dict，是将表单提交的数据转化为 python 的 dict。
2. `fileds`：一维list，包含表单选中的所有字段（English）。之后，转化为中文名，传输给前端，用于渲染查询结果的表头。
3. `result_field_tup`：二维tuple，从数据库获取，储存数据表的字段和字段名。
4. `result_basic_info`：二维tuple，从数据库获取，包含所有学生的姓名、学号信息。
5. `result_table`：二维tuple，从数据库获取，包含查询结果，每一个元素都是一名学生的信息。

### 前端传入（表单）

1. `request.form`：ImmutableMultiDict，包含表单中的各项数据，`name`和`value`一一对应。

### 后端渲染

1. `fileds`：对应`result_field_list`
   
| \                     | fileds.0 | fileds.1 | ... | fileds.n |
|-----------------------|----------|----------|-----|----------|
| row.0（字段）             |          |          |     |          |
| row.1（字段名）            |          |          |     |          |
| row.2（标记：复选框是否需要默认选择） |          |          |     |          |
| rwo.3（标记：下拉框是否需要默认选择） |          |          |     |       

2. `table`：对应`result_table`

| \               | table.0 | table.1 | ... | table.i |
|-----------------|---------|---------|-----|---------|
| row_value.0（姓名） |         |         |     |         |
| row_value.1（学号） |         |         |     |         |
| ...             |         |         |     |         |
| row_value.j     |         |         |     |       



## 关于 student_info 的数据

1. `result_student`：是一个一维

### 前端传入（表单）

### 后端渲染
1. `fields_values`：应当是一个二维列表

| \                  | fields_values.0 | fields_values.1 | ... | fields_values.n |
|--------------------|-----------------|-----------------|-----|-----------------|
| field.0（字段）        |                 |                 |     |                 |
| field.1（字段名）       |                 |                 |     |                 |
| field.2（字段的值）      |                 |                 |     |                 |

[//]: # (| field.3（标记：是否需要锁定） |                 |                 |     |                 |)



# 疑惑

1. 使用form+button无法成功跳转页面