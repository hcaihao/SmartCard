from app import db


# class Log(db.Model):
#     __tablename__ = 'logs'
#     id = db.Column(db.Integer, primary_key=True)
#     ip = db.Column(db.String(255))
#     country = db.Column(db.String(255), index=True)
#     region = db.Column(db.String(255), index=True)
#     city = db.Column(db.String(255), index=True)
#     uri = db.Column(db.String(255), index=True)
#     args = db.Column(db.String(255), index=True)
#     create_time = db.Column(db.DateTime)
#
#     def __repr__(self):
#         return '<Log %r>' % self.id

class Log(object):
    _mapper = {}

    @staticmethod
    def model(month):
        class_name = 'Log' + month

        ModelClass = Log._mapper.get(class_name, None)
        if ModelClass is None:
            ModelClass = type(class_name, (db.Model,), {
                '__module__': __name__,
                '__name__': class_name,
                '__tablename__': "logs_" + month,

                'id': db.Column(db.Integer, primary_key=True, nullable=False),
                'ip': db.Column(db.String(255), index=True, nullable=False),
                'country': db.Column(db.String(255), index=True, nullable=False),
                'region': db.Column(db.String(255), index=True, nullable=False),
                'city': db.Column(db.String(255), index=True, nullable=False),
                'uri': db.Column(db.String(255), index=True, nullable=False),
                'args': db.Column(db.String(1024), nullable=False),
                'result': db.Column(db.String(1024), nullable=False),
                'create_time': db.Column(db.DateTime, nullable=False)
            })
            Log._mapper[class_name] = ModelClass

        return ModelClass

    @staticmethod
    def get_months():
        result = []
        table_names = db.engine.table_names()
        for table_name in table_names:
            if table_name.startswith("logs_"):
                result.append(table_name[5:])
        return result
