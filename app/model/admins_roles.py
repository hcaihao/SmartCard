from app import db

Admins_Roles = db.Table('admins_roles',
                        db.Column('admin_id', db.Integer, db.ForeignKey('admins.id')),
                        db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
                        )
