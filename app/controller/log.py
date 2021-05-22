from app import app
from app import db
from app import utility
from app import admin_permission, agent_permission, seller_permission,admin_agent_permission

from app.model.admin import Admin
from app.model.card import Card
from app.model.cardtype import CardType
from app.model.client import Client
from app.model.log import Log
from app.model.operatelog import OperateLog
from app.model.user import User
from app.model.rechargelog import RechargeLog

from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import render_template

from flask_login import login_required
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from datetime import timedelta
import re
import time

@app.route('/log', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def log():
    if request.method == 'GET':
        months = Log.get_months()
        return render_template('log.html', months=months, re=re)


# @app.route('/log/edit', methods=['GET', 'POST'])
# @login_required
# @admin_permission.require(http_exception=500)
# def log_edit():
#     args = utility.get_args(request)
#     id = args.get('id', "")
#
#     log = Log.query.filter_by(id=id).first()
#     if log is None:
#         return redirect(url_for('log'))
#
#     admins = Admin.query.all()
#     return render_template('log_edit.html', log=log, admins=admins)


@app.route('/log/query', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def log_query():
    args = utility.get_args(request)
    draw = args.get('draw', "")  # 这个值作者会直接返回给前台
    start = args.get('start', "")  # 从多少开始
    length = args.get('length', "")  # 数据长度
    search = args.get('search[value]', "")  # 获取前台传过来的过滤条件
    order_column = args.get('order[0][column]', "")  # 哪一列排序，从0开始
    order_dir = args.get('order[0][dir]', "")  # asc desc 升序或者降序
    log_month = args.get('log_month', "")

    # if db.engine.dialect.has_table(db.engine.connect(), log_month):


    months = Log.get_months()
    month = time.strftime("%Y%m") if log_month == "" else log_month
    if month not in months:
        return "{}"

    MyLog = Log.model(log_month)
    logs = db.session.query(MyLog).filter(
        func.CONCAT_WS(',', MyLog.ip, MyLog.uri, MyLog.args)
            .like('%' + search + '%')
    ).order_by(text(str(int(order_column) + 1) + " " + order_dir)).offset(start).limit(length).all()

    recordsTotal = db.session.query(func.count(MyLog.id)).scalar()
    recordsFiltered = recordsTotal if search == "" else len(logs)

    data = []
    for log in logs:
        item = [log.id, log.ip, log.country, log.region, log.city, log.uri, log.args, log.result, log.create_time]
        data.append(item)

    result = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data}
    return utility.get_json(result)


# @app.route('/log/modify', methods=['GET', 'POST'])
# @login_required
# @admin_permission.require(http_exception=500)
# def log_modify():
#     args = utility.get_args(request)
#     id = args.get('id', "")
#     name = args.get('name', "")
#     register_hour = args.get('register_hour', "")
#     unbind_hour = args.get('unbind_hour', "")
#     wait_hour = args.get('wait_hour', "")
#     message = args.get('message', "")
#     version = args.get('version', "")
#     admins = ",".join(request.form.getlist("admin"))  # dict会丢失数据
#     is_enable = args.get('is_enable') == "1"
#
#     log = Log.query.filter_by(id=id).first()
#     if log is None:
#         return "软件不存在。"
#
#     log.name = name
#     log.register_hour = register_hour
#     log.unbind_hour = unbind_hour
#     log.wait_hour = wait_hour
#     log.message = message
#     log.version = version
#     log.admins = admins
#     log.is_enable = is_enable
#
#     return "修改成功。"
#

@app.route('/log/insert', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def log_insert():
    args = utility.get_args(request)
    name = args.get('name', "")
    register_hour = args.get('register_hour', "")
    unbind_hour = args.get('unbind_hour', "")
    wait_hour = args.get('wait_hour', "")
    message = args.get('message', "")
    version = args.get('version', "")
    admins = ",".join(request.form.getlist("admin"))  # dict会丢失数据

    log = Log()
    log.name = name
    log.register_hour = register_hour
    log.unbind_hour = unbind_hour
    log.wait_hour = wait_hour
    log.message = message
    log.version = version
    log.admins = admins
    log.is_enable = True
    log.update_time = func.now()
    log.create_time = func.now()
    db.session.add(log)

    return "添加成功！"
