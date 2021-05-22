from app import app
from app import db
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_no = db.Column(db.String(255), unique=True, nullable=False)
    client_info = db.Column(db.Text, nullable=False)
    client_version = db.Column(db.Text, nullable=False)
    host_name = db.Column(db.Text, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.id

    def is_online(self):
        if (datetime.now() - self.update_time).total_seconds() > app.config['HEART_SECONDS']:
            return False
        return True