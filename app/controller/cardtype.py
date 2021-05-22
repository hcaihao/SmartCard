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
from app.model.cardtype import CardType
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
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from datetime import timedelta


@app.route('/cardtype', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def cardtype():
    if request.method == 'GET':
        softwares = db.session.query(Software).join(Software.admins).filter(Admin.id == current_user.id).all()
        return render_template('cardtype.html', softwares=softwares)


@app.route('/cardtype/edit', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def cardtype_edit():
    args = utility.get_args(request)
    id = args.get('id', "")

    cardtype = db.session.query(CardType).join(CardType.software).join(Software.admins).filter(Admin.id == current_user.id).filter(CardType.id == id).first()
    if cardtype is None:
        return redirect(url_for('cardtype'))

    return render_template('cardtype_edit.html', cardtype=cardtype)


@app.route('/cardtype/query', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def cardtype_query():
    args = utility.get_args(request)
    draw = args.get('draw', "")  # 这个值作者会直接返回给前台
    start = args.get('start', "")  # 从多少开始
    length = args.get('length', "")  # 数据长度
    search = args.get('search[value]', "")  # 获取前台传过来的过滤条件
    order_column = args.get('order[0][column]', "")  # 哪一列排序，从0开始
    order_dir = args.get('order[0][dir]', "")  # asc desc 升序或者降序

    cardtypes = db.session.query(CardType).join(CardType.software).join(Software.admins).filter(Admin.id == current_user.id).filter(
        func.CONCAT_WS(',', Software.name, CardType.day, CardType.expired_day, CardType.price)
            .like('%' + search + '%')
    ).order_by(text(str(int(order_column) + 1) + " " + order_dir)).offset(start).limit(length).all()

    recordsTotal = db.session.query(func.count(CardType.id)).join(CardType.software).join(Software.admins).filter(Admin.id == current_user.id).scalar()
    recordsFiltered = recordsTotal if search == "" else len(cardtypes)

    data = []
    for cardtype in cardtypes:
        item = [cardtype.id, cardtype.software.name, cardtype.day,
                cardtype.expired_day, cardtype.price, cardtype.is_enable,
                cardtype.update_time, cardtype.create_time]
        data.append(item)

    result = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data}
    return utility.get_json(result)


@app.route('/cardtype/modify', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def cardtype_modify():
    args = utility.get_args(request)
    id = args.get('id', "")
    software_id = args.get('software_id', "")
    day = args.get('day', "")
    expired_day = args.get('expired_day', "")
    price = args.get('price', "")
    is_enable = args.get('is_enable') == "1"

    cardtype = db.session.query(CardType).join(CardType.software).join(Software.admins).filter(Admin.id == current_user.id).filter(CardType.id == id).first()
    if cardtype is None:
        return "软件不存在。"

    cardtype.software_id = software_id
    cardtype.day = day
    cardtype.expired_day = expired_day
    cardtype.price = price
    cardtype.is_enable = is_enable

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "修改卡类"
    operate_log.remark = "软件名称：{}，点卡天数：{}，过期天数：{}，价格：{}，启用：{}".format(cardtype.software.name, day, expired_day, price, is_enable)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"


@app.route('/cardtype/insert', methods=['GET', 'POST'])
@login_required
@admin_agent_permission.require(http_exception=500)
def cardtype_insert():
    args = utility.get_args(request)
    software_id = args.get('software_id', "")
    day = args.get('day', "")
    expired_day = args.get('expired_day', "")
    price = args.get('price', "")

    cardtype = CardType.query.filter_by(software_id=software_id, day = day, expired_day = expired_day).first()
    if cardtype != None:
        return "卡类已存在。"

    cardtype = CardType()
    cardtype.software_id = software_id
    cardtype.day = day
    cardtype.expired_day = expired_day
    cardtype.price = price
    cardtype.is_enable = True
    cardtype.update_time = func.now()
    cardtype.create_time = func.now()
    db.session.add(cardtype)
    db.session.commit() #提交后才能获取name

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "添加卡类"
    operate_log.remark = "软件名称：{}，点卡天数：{}，过期天数：{}，价格：{}".format(cardtype.software.name, day, expired_day, price)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "添加成功！"
