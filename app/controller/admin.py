from app import app
from app import db
from app import utility
from app import admin_permission, agent_permission, seller_permission,admin_agent_permission

from app.model.role import Role
from app.model.admin import Admin
from app.model.card import Card
from app.model.cardtype import CardType
from app.model.client import Client
from app.model.log import Log
from app.model.operatelog import OperateLog
from app.model.card import Card
from app.model.user import User
from app.model.software import Software
from app.model.rechargelog import RechargeLog

from flask_login import current_user
from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import render_template

from flask_login import login_required
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from datetime import timedelta


@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def admin():
    if request.method == 'GET':
        softwares = db.session.query(Software).join(Software.admins).filter(Admin.id == current_user.id).all()
        return render_template('admin.html', softwares=softwares)


@app.route('/admin/edit', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def admin_edit():
    args = utility.get_args(request)
    id = args.get('id', "")

    softwares = db.session.query(Software).join(Software.admins).filter(Admin.id == current_user.id).all()

    admin = None
    if admin_permission.can():
        admin = Admin.query.filter_by(id=id).first()
    else:
        admin = db.session.query(Admin).filter(Admin.superior_id == current_user.id).first()

    if admin is None:
        return redirect(url_for('admin'))

    return render_template('admin_edit.html', admin=admin, softwares=softwares)


@app.route('/admin/query', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def admin_query():
    args = utility.get_args(request)
    draw = args.get('draw', "")  # 这个值作者会直接返回给前台
    start = args.get('start', "")  # 从多少开始
    length = args.get('length', "")  # 数据长度
    search = args.get('search[value]', "")  # 获取前台传过来的过滤条件
    order_column = args.get('order[0][column]', "")  # 哪一列排序，从0开始
    order_dir = args.get('order[0][dir]', "")  # asc desc 升序或者降序

    Superior = db.aliased(Admin)

    admins = []
    recordsTotal = 0
    if admin_permission.can():
        # Left join
        admins = db.session.query(Admin, Superior).join(Superior, Admin.superior, isouter=True).join(Admin.softwares).filter(
            func.CONCAT_WS(',', Admin.user_name, Superior.user_name, Software.name)
                .like('%' + search + '%')
        ).order_by(text(str(int(order_column) + 1) + " " + order_dir)).offset(start).limit(length).all()

        recordsTotal = db.session.query(func.count(Admin.id)).scalar()
    else:
        # Left join
        admins = db.session.query(Admin, Superior).join(Superior, Admin.superior, isouter=True).join(Admin.softwares).filter(
            Admin.superior_id == current_user.id).filter(
            func.CONCAT_WS(',', Admin.user_name, Superior.user_name, Software.name)
                .like('%' + search + '%')
        ).order_by(text(str(int(order_column) + 1) + " " + order_dir)).offset(start).limit(length).all()

        recordsTotal = db.session.query(func.count(Admin.id)).filter(Admin.superior_id == current_user.id).scalar()

    recordsFiltered = recordsTotal if search == "" else len(admins)

    data = []
    for admin, superior in admins:
        item = [admin.id, admin.user_name, admin.password,admin.get_roles_names(),
                admin.superior.user_name if admin.superior else "", admin.get_subordinates_names(),
                admin.get_softwares_names(), admin.is_enable, admin.update_time, admin.create_time]
        data.append(item)

    result = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data}
    return utility.get_json(result)


@app.route('/admin/modify', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def admin_modify():
    args = utility.get_args(request)
    id = args.get('id', "")
    user_name = args.get('user_name', "")
    software_names = request.form.getlist("software_names")  # dict会丢失数据
    role_name = args.get('role_name', "")
    is_enable = args.get('is_enable') == "1"

    if len(software_names) == 0:
        return "未授权软件。"

    admin = None
    if admin_permission.can():
        admin = Admin.query.filter_by(id=id).first()
    else:
        admin = db.session.query(Admin).filter(Admin.superior_id == current_user.id).first()

    if admin is None:
        return "管理员不存在。"

    admin.user_name = user_name
    admin.is_enable = is_enable
    admin.softwares = []
    for software_name in software_names:
        software = Software.query.filter_by(name=software_name).first()
        if software is None:
            return "软件不存在。"
        admin.softwares.append(software)

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "修改{}".format(admin.get_roles_names())
    operate_log.remark = "用户名：{}，授权软件：{}，启用：{}".format(user_name, "、".join(software_names), is_enable)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"

@app.route('/admin/insert', methods=['GET', 'POST'])
@admin_agent_permission.require(http_exception=500)
def admin_insert():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")
    software_names = request.form.getlist("software_names")  # dict会丢失数据
    role_name = args.get('role_name', "")

    if len(software_names) == 0:
        return "未授权软件。"

    softwares = db.session.query(Software).join(Software.admins).filter(Admin.id == current_user.id).filter(Software.name.in_(software_names)).all()
    if len(softwares) == 0:
        return "无权限添加"

    role = Role.query.filter_by(name=role_name).first()
    if role is None:
        return "身份不存在。"

    if not admin_permission.can():
        if role.id <= current_user.roles[0].id:
            return "无权限添加。"

    admin = Admin.query.filter_by(user_name=user_name).first()
    if admin != None:
        return "用户名已存在。"

    admin = Admin()
    admin.user_name = user_name
    admin.password = utility.get_md5(password)
    admin.superior_id = current_user.id
    admin.is_enable = True
    admin.update_time = func.now()
    admin.create_time = func.now()
    admin.roles.append(role)
    for software_name in software_names:
        software = Software.query.filter_by(name=software_name).first()
        if software is None:
            return "软件不存在。"
        admin.softwares.append(software)
    db.session.add(admin)

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "添加{}".format(role.description)
    operate_log.remark = "用户名：{}，密码：{}，授权软件：{}".format(user_name, password, "、".join(software_names))
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "添加成功！"
