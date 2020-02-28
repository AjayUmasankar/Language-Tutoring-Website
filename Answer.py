from extention import db
from flask_login import UserMixin
from Post import Post
from User import User
from datetime import datetime

class Answer(db.Model):
    __tablename__ = 'answer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', foreign_keys=[post_id])
    content = db.Column(db.Text)
    post_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', foreign_keys=[author_id])
    photo = db.Column(db.LargeBinary(2**32 - 1), nullable=True)
