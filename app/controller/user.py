from app import app
from app import db
from app import utility
from app import admin_permission, agent_permission, seller_permission, admin_agent_permission

from app.model.admin import Admin
from app.model.card import Card
from app.model.cardtype import CardType
from app.model.client import Client
from app.model.log import Log
from app.model.operatelog import OperateLog
from app.model.software import Software
from app.model.user import User
from app.model.rechargelog import RechargeLog

from flask_login import current_user
from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import render_template

from flask_login import login_required
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey, asc, desc
from datetime import timedelta, datetime

@app.route('/user', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def user():
    if request.method == 'GET':
        return render_template('user.html')


@app.route('/user/edit', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def user_edit():
    args = utility.get_args(request)
    id = args.get('id', "")

    user = db.session.query(User).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).filter(User.id == id).first()
    if user is None:
        return redirect(url_for('user'))

    return render_template('user_edit.html', user=user)


@app.route('/user/query', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def user_query():
    args = utility.get_args(request)
    draw = args.get('draw', "")  # 这个值作者会直接返回给前台
    start = args.get('start', "")  # 从多少开始
    length = args.get('length', "")  # 数据长度
    search = args.get('search[value]', "")  # 获取前台传过来的过滤条件
    order_column = args.get('order[0][column]', "")  # 哪一列排序，从0开始
    order_dir = args.get('order[0][dir]', "")  # asc desc 升序或者降序
    order_name = args.get('columns[' + order_column + '][name]', "")  # 需要html里定义name

    if order_name == "users.online_client_count": #特殊处理
        order = asc if order_dir=="asc" else desc
        users = db.session.query(User).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).filter(
            func.CONCAT_WS(',', User.user_name, User.qq, User.email, User.serial_no, User.remark, Software.name)
                .like('%' + search + '%')
        ).order_by(order(User.online_client_count)).offset(start).limit(length).all()
    else:
        users = db.session.query(User).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).filter(
            func.CONCAT_WS(',', User.user_name, User.qq, User.email, User.serial_no, User.remark, Software.name)
                .like('%' + search + '%')
        ).order_by(text(order_name + " " + order_dir)).offset(start).limit(length).all()

    recordsTotal = db.session.query(func.count(User.id)).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).scalar()
    recordsFiltered = recordsTotal if search == "" else len(users)

    data = []
    for user in users:
        item = [user.id, user.software.name, user.user_name, user.password, user.password_question, user.password_answer,
                user.qq, user.email, user.phone, user.version, user.serial_no, user.token, "{}/{}".format(user.online_client_count, user.client_count),
                user.is_bind, user.remark, user.unbind_date, user.terminate_date, user.is_enable, user.update_time, user.create_time]
        data.append(item)

    result = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data}
    return utility.get_json(result)


@app.route('/user/modify', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def user_modify():
    args = utility.get_args(request)
    id = args.get('id', "")
    software_name = args.get('software_name', "")
    user_name = args.get('user_name', "")
    password = args.get('password', "")
    password_question = args.get('password_question', "")
    password_answer = args.get('password_answer', "")
    qq = args.get('qq', "")
    email = args.get('email', "")
    phone = args.get('phone', "")
    version = args.get('version', "")
    serial_no = args.get('serial_no', "")
    token = args.get('token', "")
    client_count = args.get('client_count', "")
    is_bind = args.get('is_bind', "") == "1"
    remark = args.get('remark', "")
    unbind_date = args.get('unbind_date', "")
    terminate_date = args.get('terminate_date', "")
    is_enable = args.get('is_enable') == "1"

    user = db.session.query(User).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).filter(User.id == id).first()
    if user is None:
        return "用户不存在。"

    # 调整客户端数量
    if client_count.isdigit() and client_count != 0 and user.client_count != int(client_count) and user.terminate_date > datetime.now():
        left_days = user.terminate_date - datetime.now()
        total_left_days = left_days * user.client_count
        new_left_days = total_left_days / int(client_count)
        # print(left_days)
        # print(total_left_days)
        # print(new_left_days)
        user.terminate_date = datetime.now() + new_left_days
        user.client_count = client_count

    user.qq = qq
    user.email = email
    user.phone = phone
    # user.version = version
    user.is_bind= is_bind
    user.remark = remark
    user.is_enable = is_enable


    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "修改用户"
    operate_log.remark = "用户名：{}，QQ：{}，Email：{}，手机：{}，客户端限制：{}，绑定机器：{}，备注：{}，启用：{}".format(user_name, qq, email, phone, client_count, is_bind, remark, is_enable)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"


@app.route('/user/set_password', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def user_set_password():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")

    user = db.session.query(User).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).filter(User.user_name == user_name).first()
    if user is None:
        return "用户不存在。"

    user.password = password

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "修改密码"
    operate_log.remark = "用户名：{}，密码：{}".format(user_name, password)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"


@app.route('/user/set_terminate', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def user_set_terminate():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    day = args.get('day', "")

    user = db.session.query(User).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).filter(User.user_name == user_name).first()
    if user is None:
        return "用户不存在。"

    user.terminate_date = user.terminate_date + timedelta(days=int(day))

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "增减天数"
    operate_log.remark = "用户名：{}，天数：{}".format(user_name, day)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"


@app.route('/user/set_unbind', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def user_set_unbind():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")

    user = db.session.query(User).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).filter(User.user_name == user_name).first()
    if user is None:
        return "用户不存在。"

    user.serial_no = ""

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "解绑用户"
    operate_log.remark = "用户名：{}".format(user_name)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"


@app.route('/user/set_enable', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def user_set_enable():
    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    is_enable = args.get('is_enable') == "1"

    user = db.session.query(User).join(User.software).join(Software.admins).filter(Admin.id == current_user.id).filter(User.user_name == user_name).first()
    if user is None:
        return "用户不存在。"

    user.is_enable = is_enable

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "启用用户"
    operate_log.remark = "用户名：{}，启用：{}".format(user_name, is_enable)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"
