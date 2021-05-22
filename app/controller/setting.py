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
from app.model.software import Software
from app.model.user import User
from app.model.rechargelog import RechargeLog

from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import flash
from flask import render_template

from flask_login import login_required,current_user
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from datetime import timedelta, datetime

import sys
import io
import os
import time
import pipes
import re

def backup_db():
    # MySQL database details to which backup to be done. Make sure below user having enough privileges to take databases backup.
    # To take multiple databases backup, create any file like /backup/dbnames.txt and put databases names one on each line and assigned to DB_NAME variable.

    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_USER_PASSWORD = 'shadowsoft'
    # DB_NAME = '/backup/dbnameslist.txt'
    DB_NAME = 'smartcard'
    BACKUP_PATH = '/root'

    # Getting current DateTime to create the separate backup folder like "20180817-123433".
    DATETIME = time.strftime('%Y%m%d-%H%M%S')
    TODAYBACKUPPATH = BACKUP_PATH + '/' + DATETIME

    # Checking if backup folder already exists or not. If not exists will create it.
    try:
        os.stat(TODAYBACKUPPATH)
    except:
        os.mkdir(TODAYBACKUPPATH)

    # Code for checking if you want to take single database backup or assinged multiple backups in DB_NAME.
    print("Checking for databases names file")
    if os.path.exists(DB_NAME):
        file1 = open(DB_NAME)
        multi = 1
        print("Databases file found...")
        print("Starting backup of all dbs listed in file " + DB_NAME)
    else:
        print("Databases file not found...")
        print("Starting backup of database " + DB_NAME)
        multi = 0

    # Starting actual database backup process.
    if multi:
        in_file = open(DB_NAME, "r")
        flength = len(in_file.readlines())
        in_file.close()
        p = 1
        dbfile = open(DB_NAME, "r")

        while p <= flength:
            db = dbfile.readline()  # reading database name from file
            db = db[:-1]  # deletes extra line
            dumpcmd = "mysqldump -h " + DB_HOST + " -u " + DB_USER + " -p" + DB_USER_PASSWORD + " " + db + " > " + pipes.quote(
                TODAYBACKUPPATH) + "/" + db + ".sql"
            os.system(dumpcmd)
            gzipcmd = "gzip " + pipes.quote(TODAYBACKUPPATH) + "/" + db + ".sql"
            os.system(gzipcmd)
            p = p + 1
        dbfile.close()
    else:
        db = DB_NAME
        dumpcmd = "mysqldump -h " + DB_HOST + " -u " + DB_USER + " -p" + DB_USER_PASSWORD + " " + db + " > " + pipes.quote(TODAYBACKUPPATH) + "/" + db + ".sql"
        os.system(dumpcmd)
        gzipcmd = "gzip " + pipes.quote(TODAYBACKUPPATH) + "/" + db + ".sql"
        os.system(gzipcmd)

    print("Backup script completed")
    print("Your backups have been created in '" + TODAYBACKUPPATH + "' directory")


##################################################

@app.route('/setting', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def setting():
    if request.method == 'GET':
        domain = utility.get_domain()
        ua_regex = utility.get_ua_regex()
        des_key = utility.get_des_key()
        is_encrypt = utility.get_is_encrypt()
        is_offline = utility.get_is_offline()

        return render_template('setting.html', domain=domain, ua_regex=ua_regex, des_key=des_key, is_encrypt=is_encrypt, is_offline=is_offline)


@app.route('/setting/modify', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def setting_modify():
    args = utility.get_args(request)
    domain = args.get('domain', "")
    ua_regex = args.get('ua_regex', "")
    des_key = args.get('des_key', "")
    is_encrypt = args.get('is_encrypt', "") == "1"
    is_offline = args.get('is_offline', "") == "1"

    utility.set_domain(domain)
    utility.set_ua_regex(ua_regex)
    utility.set_des_key(des_key)
    utility.set_is_encrypt(is_encrypt)
    utility.set_is_offline(is_offline)

    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "修改秘钥"
    operate_log.remark = "域名：{}，匹配：{}，秘钥：{}，加密：{}，维护：{}".format(domain, ua_regex, des_key, is_encrypt, is_offline)
    operate_log.create_time = func.now()
    db.session.add(operate_log)
    db.session.commit()

    return "修改成功。"


@app.route('/setting/backup', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def setting_backup():
    result = ""

    __stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        backup_db()
        result = sys.stdout.getvalue()
    except Exception as err:
        result = str(err)

    sys.stdout = __stdout


    # 操作记录
    operate_log = OperateLog()
    operate_log.admin_id = current_user.id
    operate_log.operate = "备份数据"
    operate_log.remark = "备份内容：数据库"
    operate_log.create_time = datetime.now()
    db.session.add(operate_log)
    db.session.commit()

    return result

@app.route('/setting/exe_sql', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def setting_exe_sql():
    args = utility.get_args(request)
    sql_cmd = args.get('sql_cmd', "")

    try:
        res = db.session.execute(sql_cmd)
        # print(res.rowcount)
        # print(res.keys())
        # print(res.fetchall())

        if res.returns_rows:
            # use special handler for dates and decimals
            return utility.get_json([dict(r) for r in res]).encode('utf-8').decode('unicode_escape')
        else:
            return utility.get_json([{"affected": res.rowcount}]).encode('utf-8').decode('unicode_escape')
    except Exception as err:
        return str(err)


@app.route('/setting/exe_python', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=500)
def setting_exe_python():
    args = utility.get_args(request)
    python_cmd = args.get('python_cmd', "")

    result = ""

    __stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        exec(python_cmd)
        result = sys.stdout.getvalue()
    except Exception as err:
        result = str(err)

    sys.stdout = __stdout

    return result
