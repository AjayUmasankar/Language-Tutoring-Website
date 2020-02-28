from extention import db, image_to_str
from flask_login import UserMixin, login_manager
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(40), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(50), nullable=False)
    usertype = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Float)
    location = db.Column(db.String(20), nullable=True)
    languagetolearn = db.Column(db.String(30), nullable=True)
    photo = db.Column(db.LargeBinary(2**32 - 1), nullable=False, default=image_to_str('static/images/default-user-icon.jpg'))
    tutorinfo = db.relationship('TutorInfo', backref='curuser', uselist=False)
    appointments = db.relationship('Appointment', backref="user")
    groups = db.relationship('Student_Groups', backref="user")
    # contacts = db.relationship('Contact', backref="user")

class Contact(db.Model):
    __tablename__ = 'contact'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id], backref='contactor')
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target = db.relationship('User', foreign_keys=[target_id], backref='contactee')

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient = db.relationship('User', foreign_keys=[recipient_id])
    time = db.Column(db.String(50), nullable=False)
    msg = db.Column(db.String(100), nullable=True)

class TutorInfo(db.Model):
    __tablename__ = 'tutorinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id])
    approved = db.Column(db.Boolean, default=False, nullable=False)
    rate = db.Column(db.Float, default=0)
    languagetoteach = db.Column(db.String(30))
    level = db.Column(db.Integer)
    idfile = db.Column(db.LargeBinary(2**32 - 1))
    qualifile = db.Column(db.LargeBinary(2**32 - 1))
    appointment = db.relationship('Appointment', backref="tutorinfo")

class Appointment(db.Model):
    __tablename__ = 'appointment'
    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student = db.relationship('User', foreign_keys=[student_id])
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutorinfo.user_id'), nullable=False)
    tutor = db.relationship('TutorInfo', foreign_keys=[tutor_id])

    address = db.Column(db.String(100))
    start_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer) 
    rate = db.Column(db.Integer, default=0)
    comment = db.Column(db.Text, default='')
    total_price = db.Column(db.Float)
    approved = db.Column(db.Boolean, default=False, nullable=False)
    paid = db.Column(db.Boolean, default=False, nullable=False)

class Student_Groups(db.Model):
    __tablename__ = 'student_groups'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    group_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_admin = db.relationship('User', foreign_keys=[group_admin_id])
    meeting_day = db.Column(db.Text, nullable=True)
    meeting_time = db.Column(db.Time)
    location = db.Column(db.Text, nullable=True)
    language = db.Column(db.Text)
    photo = db.Column(db.LargeBinary(2**32 - 1), nullable=True)

class User_Group(db.Model):
    __tablename__ = 'user_group'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', foreign_keys=[user_id])
    group_id = db.Column(db.Integer, db.ForeignKey('student_groups.id'), primary_key=True)
    group = db.relationship('Student_Groups', foreign_keys=[group_id])

class Test(db.Model):
    __tablename__ = 'test'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    language = db.Column(db.String(30), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    q1 = db.Column(db.Text)
    q2 = db.Column(db.Text)
    q3 = db.Column(db.Text)
    q4 = db.Column(db.Text)
    q5 = db.Column(db.Text)
    q6 = db.Column(db.Text)
    q7 = db.Column(db.Text)
    q8 = db.Column(db.Text)
    q9 = db.Column(db.Text)
    a1 = db.Column(db.Text)
    a2 = db.Column(db.Text)
    a3 = db.Column(db.Text)
    a4 = db.Column(db.Text)
    a5 = db.Column(db.Text)
    a6 = db.Column(db.Text)
    a7 = db.Column(db.Text)
    a8 = db.Column(db.Text)

class Test_Answer(db.Model):
    __tablename__ = 'test_answer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id])
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    test = db.relationship('Test', foreign_keys=[test_id])

    a1 = db.Column(db.Text)
    a2 = db.Column(db.Text)
    a3 = db.Column(db.Text)
    a4 = db.Column(db.Text)
    a5 = db.Column(db.Text)
    a6 = db.Column(db.Text)
    a7 = db.Column(db.Text)
    a8 = db.Column(db.Text)
    a9 = db.Column(db.Text)
    mark = db.Column(db.Integer)

class Video(db.Model):
    __tablename__ = 'Video'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[user_id])
    name = db.Column(db.String(50), nullable=False)
    path = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(30), nullable=False)
