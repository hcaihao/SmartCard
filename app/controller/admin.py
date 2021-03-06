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
    draw = args.get('draw', "")  # ???????????????????????????????????????
    start = args.get('start', "")  # ???????????????
    length = args.get('length', "")  # ????????????
    search = args.get('search[value]', "")  # ????????????????????????????????????
    order_column = args.get('order[0][column]', "")  # ?????????????????????0??????
    order_dir = args.get('order[0][dir]', "")  # asc desc ??????????????????

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
    software_names = request.form.getlist("software_names")  # dict???????????????
    role_name = args.get('role_name', "")
    is_enable = args.get('is_enable') == "1"

    if len(software_names) == 0:
        return "??????????????????"

    admin = None
    if admin_permission.can():
        admin = Admin.query.filter_by(id=id).first()
    else:
        admin = db.session.query(Admin).filter(Admin.superior_id == current_user.id).first()

    if admin is None:
        return "?????????????????????"

    admin.user_name = user_name
    admin.is_enable = is_enable
    admin.softwares = []
    for software_name in software_names:
        software = Software.query.filter_by(name=software_name).first()
        if software is None:
            return "??????????????????"
        admin.softwares.append(software)

    # ????????????
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "??????{}".format(admin.get_roles_names())
    operate_log.remark = "????????????{}??????????????????{}????????????{}".format(user_name, "???".join(software_names), is_enable)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "???????????????"

@app.route('/admin/insert', methods=['GET', 'POST'])
@admin_agent_permission.require(http_exception=500)
def admin_insert():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")
    software_names = request.form.getlist("software_names")  # dict???????????????
    role_name = args.get('role_name', "")

    if len(software_names) == 0:
        return "??????????????????"

    softwares = db.session.query(Software).join(Software.admins).filter(Admin.id == current_user.id).filter(Software.name.in_(software_names)).all()
    if len(softwares) == 0:
        return "???????????????"

    role = Role.query.filter_by(name=role_name).first()
    if role is None:
        return "??????????????????"

    if not admin_permission.can():
        if role.id <= current_user.roles[0].id:
            return "??????????????????"

    admin = Admin.query.filter_by(user_name=user_name).first()
    if admin != None:
        return "?????????????????????"

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
            return "??????????????????"
        admin.softwares.append(software)
    db.session.add(admin)

    # ????????????
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "??????{}".format(role.description)
    operate_log.remark = "????????????{}????????????{}??????????????????{}".format(user_name, password, "???".join(software_names))
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "???????????????"
