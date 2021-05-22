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


@app.route('/operatelog', methods=['GET', 'POST'])
@login_required
def operatelog():
    if request.method == 'GET':
        return render_template('operatelog.html')


@app.route('/operatelog/query', methods=['GET', 'POST'])
@login_required
def operatelog_query():
    args = utility.get_args(request)
    draw = args.get('draw', "")  # 这个值作者会直接返回给前台
    start = args.get('start', "")  # 从多少开始
    length = args.get('length', "")  # 数据长度
    search = args.get('search[value]', "")  # 获取前台传过来的过滤条件
    order_column = args.get('order[0][column]', "")  # 哪一列排序，从0开始
    order_dir = args.get('order[0][dir]', "")  # asc desc 升序或者降序

    operatelogs = []
    recordsTotal = 0
    if admin_permission.can():
        operatelogs = db.session.query(OperateLog).join(OperateLog.admin).filter(
            func.CONCAT_WS(',', Admin.user_name, OperateLog.operate, OperateLog.remark)
                .like('%' + search + '%')
        ).order_by(text(str(int(order_column) + 1) + " " + order_dir)).offset(start).limit(length).all()
        recordsTotal = db.session.query(func.count(OperateLog.id)).scalar()
    else:
        operatelogs = db.session.query(OperateLog).join(OperateLog.admin).filter(
            or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).filter(
            func.CONCAT_WS(',', Admin.user_name, OperateLog.operate, OperateLog.remark)
                .like('%' + search + '%')
        ).order_by(text(str(int(order_column) + 1) + " " + order_dir)).offset(start).limit(length).all()
        recordsTotal = db.session.query(func.count(OperateLog.id)).join(OperateLog.admin).filter(
            or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).scalar()

    recordsFiltered = recordsTotal if search == "" else len(operatelogs)

    data = []
    for operatelog in operatelogs:
        item = [operatelog.id, operatelog.admin.user_name, operatelog.operate,
                operatelog.remark, operatelog.create_time]
        data.append(item)

    result = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data}
    return utility.get_json(result)
