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
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey, DATE
from datetime import timedelta, datetime
import re
import time


@app.route('/rechargelog', methods=['GET', 'POST'])
@login_required
def rechargelog():
    if request.method == 'GET':
        softwares = Software.query.group_by(Software.name).all()
        return render_template('rechargelog.html', softwares=softwares)


@app.route('/rechargelog/query', methods=['GET', 'POST'])
@login_required
def rechargelog_query():
    args = utility.get_args(request)
    draw = args.get('draw', "")  # 这个值作者会直接返回给前台
    start = args.get('start', "")  # 从多少开始
    length = args.get('length', "")  # 数据长度
    search = args.get('search[value]', "")  # 获取前台传过来的过滤条件
    order_column = args.get('order[0][column]', "")  # 哪一列排序，从0开始
    order_dir = args.get('order[0][dir]', "")  # asc desc 升序或者降序
    order_name = args.get('columns[' + order_column + '][name]', "") #需要html里定义name
    # recharge_software = args.get('recharge_software', "")

    rechargelogs = []
    recordsTotal = 0
    if admin_permission.can():
        rechargelogs = db.session.query(RechargeLog).join(RechargeLog.card).join(RechargeLog.user).join(
            Card.card_type).join(CardType.software).filter(
            func.CONCAT_WS(',', Card.card_no, User.user_name, func.CONCAT(Software.name, "(", CardType.day, '天卡)'))
                .like('%' + search + '%')
        ).order_by(text(order_name + " " + order_dir)).offset(start).limit(length).all()
        recordsTotal = db.session.query(func.count(RechargeLog.id)).scalar()
    else:
        rechargelogs = db.session.query(RechargeLog).join(RechargeLog.card).join(RechargeLog.user).join(
            Card.card_type).join(CardType.software).join(Card.admin).filter(
            or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).filter(
            func.CONCAT_WS(',', Card.card_no, User.user_name, func.CONCAT(Software.name, "(", CardType.day, '天卡)'))
                .like('%' + search + '%')
        ).order_by(text(order_name + " " + order_dir)).offset(start).limit(length).all()
        recordsTotal = db.session.query(func.count(RechargeLog.id)).join(RechargeLog.card).join(Card.admin).filter(or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).scalar()

    recordsFiltered = recordsTotal if search == "" else len(rechargelogs)

    data = []
    for rechargelog in rechargelogs:
        item = [rechargelog.id, rechargelog.card.card_type.get_name(), rechargelog.card.card_no,
                rechargelog.card.remark, rechargelog.card.card_type.price,
                rechargelog.user.user_name, rechargelog.card.admin.user_name, rechargelog.create_time]
        data.append(item)

    result = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data}
    return utility.get_json(result)


@app.route('/rechargelog/chart', methods=['GET', 'POST'])
@login_required
def rechargelog_chart():
    args = utility.get_args(request)
    software_id = args.get('software_id', "")

    result = {"days": [], "incomes": [], "amounts": []}

    for i in range(30):
        day = datetime.strftime(datetime.now() - timedelta(days=i), '%Y-%m-%d')

        query = None
        if admin_permission.can():
            query = db.session.query(RechargeLog).join(RechargeLog.card).join(
                Card.card_type).join(CardType.software)
        else:
            query = db.session.query(RechargeLog).join(RechargeLog.card).join(RechargeLog.user).join(
                Card.card_type).join(CardType.software).join(Card.admin).filter(
                or_(Admin.id == current_user.id, Admin.superior_id == current_user.id))

        if software_id != "0":
            query = query.filter(Software.id == software_id)

        rechargelogs = query.filter(func.cast(RechargeLog.create_time, DATE) == day).all()

        income = 0
        for rechargelog in rechargelogs:
            income = income + rechargelog.card.card_type.price
        amount = len(rechargelogs)

        result["days"].append(day)
        result["incomes"].append(income)
        result["amounts"].append(amount)

    return utility.get_json(result)
