insert into schedule_functions (id, func_id, func, args, f_trigger, f_time)
values  (1, 'check_time', 'app.blueprints.main.routes:check_time', '', 'interval', '0, 0, 10');