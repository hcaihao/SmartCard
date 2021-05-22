# 项目简介
多年前开发的点卡系统，具有三级代理权限，技术交流6850825@qq.com。

* 三级权限管理：管理员，总代，销售（同级权限隔离，上级能看到下级所有点卡）
* 可以创建多款软件（名称、注册赠送时间、解绑扣除时间、解绑冷却时间、客户端限制、绑定机器、公告、脚本、登录版本、最新版本、下载网址、管理员、启用）
* 可以创建点卡类型（软件名称、点卡天数、过期天数、价格、启用）
* 对点卡管理（管理员、类型、卡号、备注、已用、启用、过期时间）
* 注册用户管理（软件名称、用户名、QQ、Email、手机、版本、机器码、Token、在线/最大客户端、绑定机器、备注、解绑时间、到期时间、启用）
* 销售记录查看（点卡类型、卡号、备注、价格、用户名、销售、创建时间）
* 销售额图形显示（近30天柱状图）
* 批量操作点卡（生成、备注、启用、禁用）
* 管理操作记录（管理登陆、生成点卡、修改信息、增减天数等）
* 管理权限修改，可修改软件授权，可添加下级账户
* 用户行为日志查看（定位用户国家、省、市、请求接口、参数、返回数据）
* 一键备份数据库，秘钥修改，web执行sql，web执行python

# 依赖库
* pip install flask
* pip install flask-sqlalchemy
* pip install flask_login
* pip install flask_principal
* pip install PyMySQL
* pip install redis
* pip install IP2Location
* pip install pycryptodome
* ...

# 功能演示
![image](https://github.com/hcaihao/SmartCard/blob/master/Demo.png)
