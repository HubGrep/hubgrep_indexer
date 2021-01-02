from crawler_controller import db

class Platform(db.Model):
    __tablename__ = 'platforms'
    id = db.Column(db.Integer, primary_key=True)
    platform_type = db.Column(db.String(128))
    base_url = db.Column(db.String(128))
