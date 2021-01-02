from crawler_controller import db
from flask_security.models import fsqla_v2 as fsqla


# Define models
fsqla.FsModels.set_db_info(db)

class Role(db.Model, fsqla.FsRoleMixin):
    pass

class User(db.Model, fsqla.FsUserMixin):
    pass



class Crawler(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey('User'))



