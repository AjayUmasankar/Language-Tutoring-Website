from extention import db
from flask_login import UserMixin
from datetime import datetime
from User import User

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', foreign_keys=[author_id])
    label = db.Column(db.String(15), nullable=True)
    photo = db.Column(db.LargeBinary(2**32 - 1), nullable=True, default=None)
