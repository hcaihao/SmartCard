from app import app
from app import db
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

from flask_login import login_required
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from datetime import timedelta
import os
import platform

# import os
#
# memoryUsage = os.popen("free | grep Mem: | awk '{print $3 \",\" $2}'").readlines()
#
# diskUsage = os.popen("/bin/df -h /usr | tail -1 | awk '{print $2 \",\" $3 \",\" $4 \",\" $5}'").readlines()
#
# connectCount = os.popen("/bin/netstat -n | /bin/awk '/^tcp/{++S[$NF]} END {for(a in S) print a,S[a]}' | grep  ESTABLISHED | awk '{print $2}'").readlines()
#
# systemDate = os.popen("/bin/cat /proc/uptime | awk '{print $1}';date;").readlines()
#
# print(memoryUsage)
# print(diskUsage)
# print(connectCount)
# print(systemDate)

def get_memory():
    if platform.platform().startswith("Linux"):
        result = os.popen("free | grep Mem: | awk '{print $3 \",\" $2}'").read().strip()
        return result.split(',')
    elif platform.platform().startswith("Windows"):
        return "22093484,24596484".split(',')

def get_disk():
    if platform.platform().startswith("Linux"):
        result = os.popen("/bin/df -h /usr | tail -1 | awk '{print $2 \",\" $3 \",\" $4 \",\" $5}'").read().strip()
        return result.split(',')
    elif platform.platform().startswith("Windows"):
        return "99G,5.0G,89G,6%".split(',')

def get_connect():
    if platform.platform().startswith("Linux"):
        result = os.popen("/bin/netstat -n | /bin/awk '/^tcp/{++S[$NF]} END {for(a in S) print a,S[a]}' | grep  ESTABLISHED | awk '{print $2}'").read().strip()
        return result
    elif platform.platform().startswith("Windows"):
        return "123"

def get_date():
    if platform.platform().startswith("Linux"):
        result = os.popen("/bin/cat /proc/uptime | awk '{print $1}';date;").read().strip()
        return result.split('\n')
    elif platform.platform().startswith("Windows"):
        return "45615264.01\nTue Oct 16 03:23:20 CDT 2018".split('\n')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'GET':
        memory_info = get_memory()
        memory = "{:.2f}%".format(100 * float(memory_info[0]) / float(memory_info[1]))
        memory_desc = "总内存:{}".format(memory_info[1])

        disk_info = get_disk()
        disk = "{}".format(disk_info[3])
        disk_desc = "容量:{}".format(disk_info[0])

        connect_info = get_connect();
        connect = connect_info
        connect_desc = "活动连接数"

        date_info = get_date()
        date = "{}秒".format(int(float(date_info[0])))
        date_desc = "系统时间:{}".format(date_info[1])

        return render_template('index.html', memory=memory, memory_desc=memory_desc, disk=disk, disk_desc=disk_desc,
                               date=date, date_desc=date_desc, connect=connect, connect_desc=connect_desc)


@app.route('/index/ip', methods=['GET', 'POST'])
@login_required
def index_ip():
    args = utility.get_args(request)
    ip = args.get('ip', "")

    ip_info = utility.get_ip(ip)
    return str(ip_info)