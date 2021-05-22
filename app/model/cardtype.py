from app import db


class CardType(db.Model):
    __tablename__ = 'card_types'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    software_id = db.Column(db.Integer, db.ForeignKey('softwares.id'), nullable=False)
    day = db.Column(db.Integer, nullable=False)
    expired_day = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    is_enable = db.Column(db.Boolean, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
    cards = db.relationship('Card', backref='card_type')

    def __repr__(self):
        return '<CardType %r>' % self.id

    def get_name(self):
        return '{}({}天卡)'.format(self.software.name, self.day)
