from app import app
from app import db
from app import login_manager
from app import admin_permission, agent_permission, seller_permission, admin_agent_permission

from app.model.admin import Admin
from app.model.admins_roles import Admins_Roles
from app.model.admins_softwares import Admins_Softwares
from app.model.card import Card
from app.model.cardtype import CardType
from app.model.client import Client
from app.model.log import Log
from app.model.operatelog import OperateLog
from app.model.software import Software
from app.model.user import User
from app.model.role import Role
from app.model.rechargelog import RechargeLog

from app.controller import index
from app.controller import login
from app.controller import user
from app.controller import software
from app.controller import card
from app.controller import cardtype
from app.controller import log
from app.controller import operatelog
from app.controller import setting
from app.controller import admin
from app.controller import rechargelog

from flask import make_response
from flask import abort
from flask import url_for
from flask import redirect
from flask import request
from flask import session
from flask import current_app
from flask import render_template
from flask import send_from_directory

from flask_login import current_user
import time
import re
import os
from datetime import timedelta, datetime
from app import utility
from sqlalchemy import func
from flask_principal import identity_loaded, RoleNeed, UserNeed, IdentityContext, Permission


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.before_request
def before_request():
    pass


@app.after_request
def after_request(response):
    return response


@app.route('/des/<text>')
def des(text):
    chiper = utility.des_encode(text)
    plain = utility.des_decode(chiper)
    return plain


@app.route('/md5/<text>')
def md5(text):
    chiper = utility.get_md5(text)
    return chiper


@app.route('/ip')
@app.route('/ip/<ip>')
def ip(ip=None):
    if ip == None:
        ip = request.remote_addr

    ip_info = utility.get_ip(ip)
    return str(ip_info)


@app.route("/update/<name>")
def update(name):
    result = {"name": name, "items": []}
    all_files = utility.get_all_files("update/" + name)
    for file in all_files:
        item = {
            "name": file[0],
            "size": utility.get_file_size(file[2]),
            "time": utility.get_file_mtime(file[2]),
            "md5": utility.get_file_md5(file[2]),
            "url": request.url_root + file[1] + "/" + file[0],
        }

        result["items"].append(item)

    return utility.get_json(result)


@app.route('/download/<name>')
def download(name):
    info = os.stat("{}/{}".format(app.config['UPLOAD_PATH'], name))
    response = make_response(send_from_directory(app.config['UPLOAD_PATH'], name, as_attachment=True))
    response.headers['Pack'] = int(info.st_mtime)
    return response


@app.route('/init')
def init():
    from app import db
    from app.model import admin, card, cardtype, log, operatelog, rechargelog, software, user, role, client
    # db.drop_all()
    db.create_all()

    return "ok"


@login_manager.user_loader
def user_loader(id):
    admin = Admin.query.filter_by(id=id).first()
    return admin


@app.context_processor
def context():
    my_admin_permission = IdentityContext(admin_permission)
    my_agent_permission = IdentityContext(agent_permission)
    my_seller_permission = IdentityContext(seller_permission)
    return dict(admin_permission=my_admin_permission, agent_permission=my_agent_permission,
                seller_permission=my_seller_permission)


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user

    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role.name))


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, debug=True, use_reloader=True)
