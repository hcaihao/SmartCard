from app import db

Admins_Softwares = db.Table('admins_softwares',
                        # db.Column('id', db.Integer, primary_key=True, nullable=False),
                        db.Column('admin_id', db.Integer, db.ForeignKey('admins.id')),
                        db.Column('software_id', db.Integer, db.ForeignKey('softwares.id'))
                        )
