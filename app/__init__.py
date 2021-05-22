from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from IP2Location import IP2Location
import redis
import os
from flask_login import LoginManager
from flask_principal import Principal, Permission, RoleNeed

BASE_DIR = os.path.dirname(__file__)

app = Flask(__name__, static_folder='static', static_url_path='/static')

app.config['SECRET_KEY'] = "12345678"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:test123@localhost:3306/smartcard"
app.config['SQLALCHEMY_POOL_SIZE'] = 200
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 100
app.config['SQLALCHEMY_ECHO'] = False
app.config['UPLOAD_PATH'] = os.path.join(app.root_path, 'upload')
app.config['HEART_SECONDS'] = 600

# 创建数据库对象
# base.ischema_names['tinyint'] = base.BOOLEAN    #reflect后可以显示true/false
db = SQLAlchemy(app)

# 创建Login对象
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message = ""

# Principal
principal = Principal()
principal.init_app(app)
admin_permission = Permission(RoleNeed('admin'))
agent_permission = Permission(RoleNeed('agent'))
seller_permission = Permission(RoleNeed('seller'))
admin_agent_permission = admin_permission.union(agent_permission)

# a = admin_permission.union(user_permission)
# b = admin_permission & user_permission
# assert a.needs == b.needs

# 创建Redis对象
cache = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# IP2Location
ip2location = IP2Location()
ip2location.open(os.path.join(BASE_DIR, 'static/ip/IP2LOCATION-LITE-DB11.BIN'))
# ip2location.close()

# GeoIP
# geoip = geoip2.database.Reader(os.path.join(BASE_DIR, 'static/ip/GeoIP2-City.mmdb'))
# geoip.close()
