create table CLASS_WEBSITE.student_info
(
    id                 int auto_increment
        primary key,
    class_name         varchar(30) null comment '班级',
    name               varchar(50) null comment '姓名',
    student_id         varchar(50) null comment '学号',
    sex                varchar(10) null comment '性别',
    political_identity varchar(50) null comment '政治身份',
    dormitory          varchar(50) null comment '寝室',
    telephone          varchar(20) null comment '手机号',
    constraint student_id
        unique (student_id)
)
    comment '学生信息';