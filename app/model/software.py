from app import db
from app.model.admins_softwares import Admins_Softwares

class Software(db.Model):
    __tablename__ = 'softwares'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)
    register_hour = db.Column(db.Integer, nullable=False)
    unbind_hour = db.Column(db.Integer, nullable=False)
    wait_hour = db.Column(db.Integer, nullable=False)
    client_count = db.Column(db.Integer, nullable=False)
    is_bind = db.Column(db.Boolean, nullable=False)
    message = db.Column(db.String(255), nullable=False)
    script = db.Column(db.Text, nullable=False)
    version = db.Column(db.String(255), nullable=False)
    new_version = db.Column(db.String(255), nullable=False)
    new_url = db.Column(db.String(255), nullable=False)
    is_enable = db.Column(db.Boolean, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
    card_types = db.relationship('CardType', backref='software')
    users = db.relationship('User', backref='software')

    def __repr__(self):
        return '<Software %r>' % self.id

    def get_admins_names(self):
        result = []
        for admin in self.admins:
            result.append(admin.user_name)
        return ",".join(result)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'register_hour': self.register_hour,
            'unbind_hour': self.unbind_hour,
            'wait_hour': self.wait_hour,
            'message': self.message,
            'client_count': self.client_count,
            'script': self.script,
            'version': self.version,
            'is_enable': self.is_enable,
            'update_time': self.update_time,
            'create_time': self.create_time
        }
