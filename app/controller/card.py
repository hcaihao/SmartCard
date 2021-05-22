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
from app.model.card import Card
from app.model.user import User
from app.model.software import Software
from app.model.rechargelog import RechargeLog

from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import render_template

from flask_login import login_required,current_user
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from datetime import timedelta
from datetime import datetime

@app.route('/card', methods=['GET', 'POST'])
@login_required
def card():
    if request.method == 'GET':
        card_types = db.session.query(CardType).join(CardType.software).join(Software.admins).filter(Admin.id == current_user.id).all()
        return render_template('card.html', card_types=card_types)


@app.route('/card/edit', methods=['GET', 'POST'])
@login_required
def card_edit():
    args = utility.get_args(request)
    id = args.get('id', "")

    card = None
    if admin_permission.can():
        card = Card.query.filter_by(id=id).first()
    else:
        card = db.session.query(Card).join(Card.admin).filter(or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).filter(Card.id == id).first()
    if card is None:
        return redirect(url_for('card'))

    return render_template('card_edit.html', card=card)


@app.route('/card/query', methods=['GET', 'POST'])
@login_required
def card_query():
    args = utility.get_args(request)
    draw = args.get('draw', "")  # 这个值作者会直接返回给前台
    start = args.get('start', "")  # 从多少开始
    length = args.get('length', "")  # 数据长度
    search = args.get('search[value]', "")  # 获取前台传过来的过滤条件
    order_column = args.get('order[0][column]', "")  # 哪一列排序，从0开始
    order_dir = args.get('order[0][dir]', "")  # asc desc 升序或者降序
    order_name = args.get('columns[' + order_column + '][name]', "")  # 需要html里定义name

    '''
    SELECT * FROM
    (SELECT cards.*, admins.user_name AS admin_name, my_card_types.card_type_name FROM `cards` LEFT JOIN `admins` ON cards.admin_id = admins.id
    LEFT JOIN (SELECT card_types.*,CONCAT(softwares.name, '(', CAST(card_types.day AS CHAR), '天卡)') AS card_type_name FROM card_types
    LEFT JOIN softwares ON card_types.software_id = softwares.id) AS my_card_types ON cards.type_id = my_card_types.id) AS t1
    WHERE CONCAT_WS(',',`card_no`,`remark`,`admin_name`,`card_type_name`)
    LIKE '%"..search.."%' "..order.." LIMIT "..start..", "..length
    '''

    # 点卡需要用户间彼此隔离
    cards = []
    recordsTotal = 0
    if admin_permission.can():
        cards = db.session.query(Card).join(Card.admin).join(Card.card_type).join(CardType.software).filter(
            func.CONCAT_WS(',', Card.card_no, Card.remark, Admin.user_name, func.CONCAT(Software.name, "(", CardType.day, '天卡)'))
                .like('%' + search + '%')
        ).order_by(text(order_name + " " + order_dir)).offset(start).limit(length).all()
        recordsTotal = db.session.query(func.count(Card.id)).scalar()
    else:
        cards = db.session.query(Card).join(Card.admin).join(Card.card_type).join(CardType.software).filter(or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).filter(
            func.CONCAT_WS(',', Card.card_no, Card.remark, Admin.user_name, func.CONCAT(Software.name, "(", CardType.day, '天卡)'))
                .like('%' + search + '%')
        ).order_by(text(order_name + " " + order_dir)).offset(start).limit(length).all()
        recordsTotal = db.session.query(func.count(Card.id)).join(Card.admin).join(Card.card_type).join(CardType.software).filter(or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).scalar()

    recordsFiltered = recordsTotal if search == "" else len(cards)

    data = []
    for card in cards:
        item = [card.id, card.admin.user_name, card.card_type.get_name(),
                card.card_no, card.password, card.remark, card.is_used, card.is_enable, card.create_time + timedelta(days = card.card_type.expired_day),
                card.update_time, card.create_time]
        data.append(item)

    result = {"draw": draw, "recordsTotal": recordsTotal, "recordsFiltered": recordsFiltered, "data": data}
    return utility.get_json(result)


@app.route('/card/modify', methods=['GET', 'POST'])
@login_required
def card_modify():
    args = utility.get_args(request)
    id = args.get('id', "")
    # card_type_id = args.get('card_type_id', "")
    # card_no = args.get('card_no', "")
    # password = args.get('password', "")
    remark = args.get('remark', "")
    is_enable = args.get('is_enable') == "1"

    card = None
    if admin_permission.can():
        card = Card.query.filter_by(id=id).first()
    else:
        card = db.session.query(Card).join(Card.admin).filter(or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).filter(Card.id == id).first()
    if card is None:
        return "点卡不存在。"

    card.remark = remark
    card.is_enable = is_enable

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "修改点卡"
    operate_log.remark = "点卡：{}，备注：{}，启用：{}".format(card.card_no, card.remark, card.is_enable)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"


@app.route('/card/generate', methods=['GET', 'POST'])
@login_required
def card_generate():
    args = utility.get_args(request)
    card_type_id = args.get('card_type_id', "")
    amount = args.get('amount', "")
    remark = args.get('remark', "")

    cardtype = db.session.query(CardType).join(CardType.software).join(Software.admins).filter(Admin.id == current_user.id).filter(CardType.id == card_type_id).first()
    if cardtype is None:
        return "卡类不存在。"

    for i in range(int(amount)):
        card = Card()
        card.admin_id = current_user.id
        card.card_type_id = card_type_id
        card.card_no = utility.get_uuid().replace("-", "")
        card.password = utility.get_uuid()[0:6]
        card.remark = remark
        card.is_used = False
        card.is_enable = True
        card.update_time = func.now()
        card.create_time = func.now()
        db.session.add(card)


    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "生成点卡"
    operate_log.remark = "软件名称：{}，数量：{}".format(cardtype.software.name, amount)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "生成成功！"


@app.route('/card/set_enable_batch', methods=['GET', 'POST'])
@login_required
def card_set_enable_batch():
    args = utility.get_args(request)
    card_list = args.get('card_list', "")
    is_enable = args.get('is_enable') == "1"

    result = ""
    card_nos = card_list.strip().split("\n")
    for card_no in card_nos:
        result += card_no

        card = None
        if admin_permission.can():
            card = Card.query.filter(Card.card_no==card_no).first()
        else:
            card = db.session.query(Card).join(Card.admin).filter(or_(Admin.id == current_user.id, Admin.superior_id == current_user.id)).filter(Card.card_no==card_no).first()

        if card is None:
            result += "（点卡不存在)"
        else:
            if card.is_used:
                result += "（点卡已使用）"
            else:
                card.is_enable = is_enable
                result += "（修改成功）"
        result += "\n"

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "批量操作点卡"
    operate_log.remark = "数量：{}，启用：{}".format(len(card_nos), is_enable)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return result
