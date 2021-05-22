from app import db


class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    card_type_id = db.Column(db.Integer, db.ForeignKey('card_types.id'), nullable=False)
    card_no = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    remark = db.Column(db.String(255), nullable=False)
    is_used = db.Column(db.Boolean, nullable=False)
    is_enable = db.Column(db.Boolean, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
    recharge_logs = db.relationship('RechargeLog', backref='card')

    def __repr__(self):
        return '<Card %r>' % self.id
