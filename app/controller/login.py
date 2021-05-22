from app import app
from app import db
from app import login_manager
from app import utility

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
from flask import current_app

from flask_login import login_user, logout_user
from datetime import timedelta, datetime
from flask_principal import identity_changed, Identity, AnonymousIdentity



# redirect returns a 302 header to the browser, with its Location header as the URL for the index function.
# render_template returns a 200, with the index.html template returned as the content at that URL.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")

    admin = Admin.query.filter(Admin.user_name==user_name, Admin.password==utility.get_md5(password)).first()
    if admin is None:
        flash('用户名或密码错误。')
        return redirect(url_for('login'))
    elif not admin.is_enable:
        flash('账号已停用。')
        return redirect(url_for('login'))
    else:
        login_user(admin)

        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(admin.id))

        # session["id"] = admin.id
        # session["user_name"] = admin.user_name
        # session["is_super"] = admin.is_super
        # session["permissions"] = admin.permissions
        # app.permanent_session_lifetime = timedelta(minutes=30)

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = admin.id
    operate_log.operate = "管理登陆"
    operate_log.remark = "IP：{}".format(request.remote_addr)
    operate_log.create_time = datetime.now()
    db.session.add(operate_log)
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/modify_password', methods=['GET', 'POST'])
def modify_password():
    if request.method == 'GET':
        return render_template('modify_password.html')

    args = utility.get_args(request)
    user_name = args.get('user_name', "")
    password = args.get('password', "")
    new_password = args.get('new_password', "")

    admin = Admin.query.filter(Admin.user_name==user_name, Admin.password==utility.get_md5(password)).first()
    if admin is None:
        flash('用户名或密码错误。')
        return redirect(url_for('modify_password'))
    elif not admin.is_enable:
        flash('账号已停用。')
        return redirect(url_for('modify_password'))
    else:
        admin.password = utility.get_md5(new_password)
        # db.session.commit()

    return redirect(url_for('index'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # session.clear()
    logout_user()

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return redirect(url_for('login'))


# @app.route('/check')
# def check():
#     return str(session.items())
