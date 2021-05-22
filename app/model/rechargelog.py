from app import db


class RechargeLog(db.Model):
    __tablename__ = 'recharge_logs'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<RechargeLog %r>' % self.id

