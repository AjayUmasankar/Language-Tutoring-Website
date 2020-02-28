from extention import db
from flask_login import UserMixin

class Date:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    student_id = db.relationship('User', backref=db.backref('date'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tutor_id = db.relationship('User', backref=db.backref('date'))
    start_time = db.Column(db.Datetime)
    end_time = db.Column(db.Datetime)    
