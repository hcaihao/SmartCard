from app import app
from app import db
from app import utility
from app import admin_permission, agent_permission, seller_permission, admin_agent_permission

from app.model.admins_softwares import Admins_Softwares
from app.model.admin import Admin
from app.model.card import Card
from app.model.cardtype import CardType
from app.model.client import Client
from app.model.log import Log
from app.model.operatelog import OperateLog
from app.model.software import Software
from app.model.user import User
from app.model.rechargelog import RechargeLog

from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import render_template

from flask_login import current_user
from flask_login import login_required
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from datetime import timedelta


@app.route('/software', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def software():
    if request.method == 'GET':
        return render_template('software.html')


@app.route('/software/edit', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def software_edit():
    args = utility.get_args(request)
    id = args.get('id', "")

    software = db.session.query(Software).join(Software.admins).filter(Admin.id == current_user.id).filter(Software.id == id).first()
    if software is None:
        return redirect(url_for('software'))

    return render_template('software_edit.html', software=software)


@app.route('/software/query', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def software_query():
    args = utility.get_args(request)
    draw = args.get('draw', "")  # 这个值作者会直接返回给前台
    start = args.get('start', "")  # 从多少开始
    length = args.get('length', "")  # 数据长度
    search = args.get('search[value]', "")  # 获取前台传过来的过滤条件
    order_column = args.get('order[0][column]', "")  # 哪一列排序，从0开始
    order_dir = args.get('order[0][dir]', "")  # asc desc 升序或者降序
    order_name = args.get('columns[' + order_column + '][name]', "")  # 需要html里定义name

    softwares = db.session.query(Software).join(Software.admins).filter(Admin.id == current_user.id).filter(
        func.CONCAT_WS(',', Software.name, Software.message, Software.version, Admin.user_name)
            .like('%' + search + '%')
    ).order_by(text(order_name + " " + order_dir)).offset(start).limit(length).all()

    recordsTotal = db.session.query(func.count(Software.id)).scalar()
    recordsFiltered = recordsTotal if search == "" else len(softwares)

    data = []
    for software in softwares:
        item = [software.id, software.name, software.register_hour,
                software.unbind_hour, software.wait_hour, software.client_count, software.is_bind, software.message, utility.get_short(software.script, 16), software.version,
                software.new_version, software.new_url, software.get_admins_names(), software.is_enable, software.update_time, software.create_time]
        data.append(item)

    result = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data}
    return utility.get_json(result)


@app.route('/software/modify', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def software_modify():
    args = utility.get_args(request)
    id = args.get('id', "")
    name = args.get('name', "")
    register_hour = args.get('register_hour', "")
    unbind_hour = args.get('unbind_hour', "")
    wait_hour = args.get('wait_hour', "")
    client_count = args.get('client_count', "")
    is_bind = args.get('is_bind', "") == "1"
    message = args.get('message', "")
    script = args.get('script', "")
    version = args.get('version', "")
    new_version = args.get('new_version', "")
    new_url = args.get('new_url', "")
    is_enable = args.get('is_enable') == "1"

    software = db.session.query(Software).join(Software.admins).filter(Admin.id == current_user.id).filter(Software.id == id).first()
    if software is None:
        return "软件不存在。"

    software.name = name
    software.register_hour = register_hour
    software.unbind_hour = unbind_hour
    software.wait_hour = wait_hour
    software.client_count = client_count
    software.is_bind = is_bind
    software.message = message
    software.script = script
    software.version = version
    software.new_version = new_version
    software.new_url = new_url
    software.is_enable = is_enable

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "修改软件"
    operate_log.remark = "软件名称：{}，注册赠送时间：{}，解绑扣除时间：{}，解绑冷却时间：{}，客户端限制：{}，绑定机器：{}，登录版本：{}，最新版本：{}，下载网址：{}，启用：{}".format(name, register_hour, unbind_hour, wait_hour, client_count, is_bind, version, new_version, new_url, is_enable)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"


@app.route('/software/insert', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def software_insert():
    args = utility.get_args(request)
    name = args.get('name', "")
    register_hour = args.get('register_hour', "")
    unbind_hour = args.get('unbind_hour', "")
    wait_hour = args.get('wait_hour', "")
    client_count = args.get('client_count', "")
    is_bind = args.get('is_bind', "") == "1"
    message = args.get('message', "")
    script = args.get('script', "")
    version = args.get('version', "")
    new_version = args.get('new_version', "")
    new_url = args.get('new_url', "")

    software = Software.query.filter_by(name=name).first()
    if software != None:
        return "软件名已存在。"

    software = Software()
    software.name = name
    software.register_hour = register_hour
    software.unbind_hour = unbind_hour
    software.wait_hour = wait_hour
    software.client_count = client_count
    software.is_bind = is_bind
    software.message = message
    software.script = script
    software.version = version
    software.new_version = new_version
    software.new_url = new_url
    software.is_enable = True
    software.update_time = func.now()
    software.create_time = func.now()
    software.admins.append(current_user)
    db.session.add(software)

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "添加软件"
    operate_log.remark = "软件名称：{}，注册赠送时间：{}，解绑扣除时间：{}，解绑冷却时间：{}，客户端限制：{}，绑定机器：{}，版本号：{}".format(name, register_hour, unbind_hour, wait_hour, client_count, is_bind, version)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "添加成功！"
