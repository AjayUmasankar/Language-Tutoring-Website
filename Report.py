from extention import db
from flask_login import UserMixin
from datetime import datetime
from User import User

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # User who got reported
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user1 = db.relationship('User', foreign_keys=[user1_id])
    # User who did the reporting
    # Not coneect to anything becuase I dont know how to connect to user.id again after already connecting it for user1
    user2_id = db.Column(db.Integer, nullable=False)
    
    report_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    reason = db.Column(db.Text)
    # 3 options
    #   NULL = undecided
    #   True = action to be taken
    #   False = no action taken
    status = db.Column(db.Text, nullable=True)
