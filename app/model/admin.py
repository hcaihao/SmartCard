from app import db
from flask_login import UserMixin, AnonymousUserMixin
from app import admin_permission, agent_permission, admin_agent_permission
from sqlalchemy import func, text, or_, and_, create_engine, MetaData, Table, Column, ForeignKey
from app.model.admins_roles import Admins_Roles
from app.model.admins_softwares import Admins_Softwares

class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    superior_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    user_name = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # level = db.Column(db.Integer, nullable=False)
    is_enable = db.Column(db.Boolean, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)
    operate_logs = db.relationship('OperateLog', lazy='dynamic', backref='admin')
    cards = db.relationship('Card', lazy='dynamic', backref='admin')
    roles = db.relationship('Role', secondary=Admins_Roles, lazy='dynamic', backref=db.backref('admins', lazy='dynamic'))
    softwares = db.relationship('Software', secondary=Admins_Softwares, lazy='dynamic', backref=db.backref('admins', lazy='dynamic'))
    subordinates = db.relationship("Admin", backref=db.backref('superior', remote_side=[id]))  # 不要lazy，否则无法len(admin.subordinates)

    def __repr__(self):
        return '<Admin %r>' % self.id

    def get_roles_names(self):
        result = []
        for role in self.roles:
            result.append(role.description)
        return ",".join(result)

    def get_softwares_names(self):
        result = []
        for software in self.softwares:
            result.append(software.name)
        return ",".join(result)

    def get_subordinates_names(self):
        result = []
        for subordinate in self.subordinates:
            result.append(subordinate.user_name)
        return ",".join(result)

    def is_have_software(self, id):
        for software in self.softwares:
            if software.id == id:
                return True
        return False

    # 有level字段时
    # def get_my_admins(self):
    #     admins = []
    #
    #     def query_child(current):
    #         count = 0
    #         for admin in current.subordinates:
    #             count = count + query_child(admin)
    #
    #         current.count = count
    #         admins.append(current)
    #         return count + 1
    #
    #     # 不显示自己
    #     for admin in self.subordinates:
    #         query_child(admin)
    #
    #     return admins

    # 无level字段时
    # def get_my_admins(self):
    #     admins = []
    #
    #     def query_child(current, level=1):
    #         count = 0
    #         for admin in current.subordinates:
    #             count = count + query_child(admin, level=level + 1)
    #
    #         current.level = level
    #         current.count = count
    #         admins.append(current)
    #
    #         print(current.user_name, len(current.subordinates))
    #
    #         return count + 1
    #
    #     # 不显示自己
    #     for admin in self.subordinates:
    #         query_child(admin)
    #
    #     return admins

    # 递归sql查询
    def get_my_admin_ids(self):
        topq = db.session.query(Admin)
        topq = topq.filter(Admin.superior_id == self.id)  # Admin.id则包含自己
        topq = topq.cte('cte', recursive=True)

        bottomq = db.session.query(Admin)
        bottomq = bottomq.join(topq, Admin.superior_id == topq.c.id)

        recursive_q = topq.union(bottomq)

        results = db.session.query(Admin.id).from_statement(recursive_q.select()).all()
        return [value for value, in results]

    # @staticmethod
    # def get_inferiors(id):
    #     admins = Admin.query.filter_by(superior_id=id)
    #     return admins

    # def is_authenticated(self):
    #     # Check the user whether logged in.
    #     # Check the User's instance whether Class AnonymousUserMixin's instance.
    #     return True
    #
    # def is_anonymous(self):
    #     # Check the user's login status whether is anonymous.
    #     return True
    #
    # # For flask-login
    # def is_active(self):
    #     # Check the user whether pass the activation process.
    #     return self.is_enable
    #
    # def get_id(self):
    #     # Get the user's uuid from database.
    #     return str(self.id)
