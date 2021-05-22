from app import app
from app import db
from app.model.client import Client
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from datetime import timedelta, datetime
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import func, select

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    software_id = db.Column(db.Integer, db.ForeignKey('softwares.id'), nullable=False)
    user_name = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)    #md5
    password_question = db.Column(db.String(255), nullable=False)
    password_answer = db.Column(db.String(255), nullable=False)
    qq = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(255), nullable=False)
    serial_no = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(255), nullable=False)
    client_count = db.Column(db.Integer, nullable=False)
    is_bind = db.Column(db.Boolean, nullable=False)
    remark = db.Column(db.String(255), nullable=False)
    unbind_date = db.Column(db.DateTime, nullable=False)
    terminate_date = db.Column(db.DateTime, nullable=False)
    is_enable = db.Column(db.Boolean, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
    recharge_logs = db.relationship('RechargeLog', lazy='dynamic', backref='user')
    # clients = db.relationship('Client', backref='user') #不会触发online_client_count(cls)
    # clients = db.relationship('Client', lazy='dynamic', primaryjoin=and_(Client.user_id == id, func.timestampdiff(text('second'), Client.update_time, func.now()) < app.config['HEART_SECONDS']), backref='user') #all_client_count(self) -> client_count用len不能用lazy load
    clients = db.relationship('Client', primaryjoin=and_(Client.user_id == id, func.timestampdiff(text('second'), Client.update_time, func.now()) < app.config['HEART_SECONDS']), backref='user')

    def __repr__(self):
        return '<User %r>' % self.id

    @hybrid_property
    def is_enable_text(self):
        if self.is_enable:
            return "是"
        else:
            return "否"

    @hybrid_property
    def all_client_count(self):
        return len(self.clients)

    @hybrid_property
    def online_client_count(self):
        count = 0
        for client in self.clients:
            if (datetime.now() - client.update_time).total_seconds() < app.config['HEART_SECONDS']:
                count = count + 1
        return count

    @online_client_count.expression
    def online_client_count(cls):
        # return (select([func.count(Client.id)]).where(Client.user_id == cls.id))
        return (select([func.count(Client.id)]).where(and_(Client.user_id == cls.id, func.timestampdiff(text('second'), Client.update_time, func.now()) < app.config['HEART_SECONDS'])))
