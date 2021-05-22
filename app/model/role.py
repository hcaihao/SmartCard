from app import db
from app.model.admins_roles import Admins_Roles
from app.model.admins_softwares import Admins_Softwares

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role %r>' % self.id