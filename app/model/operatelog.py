from app import db


class OperateLog(db.Model):
    __tablename__ = 'operate_logs'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    operate = db.Column(db.String(255), index=True, nullable=False)
    remark = db.Column(db.String(255), index=True, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<OperateLog %r>' % self.id

