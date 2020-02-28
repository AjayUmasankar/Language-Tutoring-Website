from flask import request, render_template, flash, redirect, url_for, session, Flask
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask_cors import CORS
from extention import db, image_to_str
from User import User, TutorInfo, Appointment, Student_Groups, User_Group, Message, Contact, Test, Test_Answer, Video
from Post import Post
from Answer import Answer
from Report import Report
from datetime import datetime
import config
import sys
from base64 import b64encode
from flask_socketio import SocketIO, join_room, leave_room, rooms, emit
import os

app = Flask(__name__)
# allows continue, break
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

# Prevents 'Access Control Allow Origin' header issues
CORS(app)
# app.secret_key = 'super secret key'
app.config.from_object(config)
db.init_app(app)
socketio = SocketIO(app)

# Creates all the required tables automatically
with app.app_context():
    # db.drop_all()
    db.create_all()

# Helps checking if a user is logged in
login_manager = LoginManager()
login_manager.init_app(app)


def clear_data(session):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        session.execute(table.delete())
    session.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Global variable for use in all templates, needed for online chat currently
@app.context_processor
def inject_user():
    return dict(users=User.query.all())


@socketio.on('getcontacts')
def getcontacts():
    join_room(current_user.id)  # so that history is only uploaded for cur user
    dbcontacts = Contact.query.filter(Contact.user_id == current_user.id).all()
    # dbcontacts = Contact.query.filter((Contact.user_id == current_user.id) |
    #                                (Contact.target_id == current_user.id)).all()
    contacts = []
    seen = []
    for dbcontact in dbcontacts:
        # print(dbcontact)
        contact = {}

        # shouldnt be able to talk to ourselves
        print(current_user.id)
        if dbcontact.target_id == current_user.id:
            contact['id'] = dbcontact.user_id
            contact['username'] = dbcontact.user.username
        else:
            contact['id'] = dbcontact.target_id
            contact['username'] = dbcontact.target.username
        print(contact['id'])
        if contact['id'] not in seen:
            # print("adding ", contact['id'])
            contacts.append(contact)
            seen.append(contact['id'])
    emit('contacts', contacts, room=current_user.id)


@socketio.on('sendmsg')
def sendmessage(json, methods=['GET', 'POST']):
    room = session['room']
    curtime = datetime.now()
    json['time'] = curtime.strftime("%H:%M:%S | %b %d")
    message = Message(sender_id=json['senderid'],
                      recipient_id=json['recipientid'], time=json['time'],
                      msg=json['message'])
    db.session.add(message)
    db.session.commit()

    # if recipient doesnt have this contact currently, add it
    # TODO some sort of alert for new message
    senderid = int(json['senderid'])
    recipientid = int(json['recipientid'])
    print("checking between ")
    print(json['recipientid'], json['senderid'])
    contact = Contact.query.filter((Contact.user_id == recipientid) &
                                   (Contact.target_id == senderid)).first()
    if not contact:
        dbcontact = Contact(user_id=recipientid, target_id=senderid)
        db.session.add(dbcontact)
        db.session.commit()
        contact = {}
        contact['id'] = senderid
        sender = User.query.filter(User.id == senderid).first()
        contact['username'] = sender.username
        emit('addcontact', contact, room=recipientid)
    emit('msgrecieved', json, room=room)


def GetUniqueRoom(user1, user2):
    list = []
    list.append(user1)
    list.append(user2)
    list.sort()
    roomname = str(list[0]) + " " + str(list[1])
    return roomname


@socketio.on('joinroom')
def joinroom(recipientid, methods=['GET', 'POST']):
    roomname = GetUniqueRoom(str(current_user.id), str(recipientid))
    session['room'] = roomname
    join_room(roomname)  # so that chatroom between cur and recipient is updated
    join_room(current_user.id)  # so that history is only uploaded for cur user
    print("joining " + roomname)
    print("joining " + str(current_user.id))
    print(recipientid, current_user.id)
    msgs = []
    messages = Message.query.filter(((Message.recipient_id == recipientid) &
                                     (Message.sender_id == current_user.id))
                                    |
                                    ((Message.recipient_id == current_user.id) &
                                     (Message.sender_id == recipientid)))

    for message in messages:
        msg = {'sender': message.sender_id, 'recipient': message.recipient_id, 'message': message.msg,
               'time': message.time}
        msgs.append(msg)
    emit('joinedroom', msgs, room=current_user.id)


@socketio.on('leaveroom')
def leaveroom():
    if session.get('room') == False:
        leave_room(session['room'])


@socketio.on('getlastmsg')
def getlastmsg(recipientid, index):
    message = Message.query.filter(((Message.recipient_id == recipientid) &
                                    (Message.sender_id == current_user.id))
                                   |
                                   ((Message.recipient_id == current_user.id) &
                                    (Message.sender_id == recipientid))).order_by(Message.id.desc()).first()
    # print(index)
    json = {}
    if message is None:
        json['msg'] = ""
    else:
        json['msg'] = message.msg
    json['index'] = index
    emit('lastmsg', json)


@app.route('/')
def homepage():
    # # Sample data to save time
    defaultpic = image_to_str('static/images/default-user-icon.jpg')
    contactbc = Contact(user_id=2, target_id=3)

    if not User.query.filter(User.username == 'admin').first():
        user = User(email='a@a', name='admin', username='admin', phone='7412',
                    password='a', usertype=3, balance=100.0, photo=defaultpic, location="Horiad")
        db.session.add(user)
        db.session.commit()

    if not User.query.filter(User.username == 'b').first():
        user = User(email='b@b', name='Me Student Study', username='b', phone='2147',
                    password='b', usertype=1, balance=100.0, photo=defaultpic, location="San Diego")
        db.session.add(user)
        db.session.commit()

    if not User.query.filter(User.username == 'c').first():
        user = User(email='c@c', name='Adrian Samuels', username='c', phone='7412',
                    password='c', usertype=2, balance=100.0, photo=defaultpic, location="Paradigms")
        db.session.add(user)
        db.session.commit()
        tinfo = TutorInfo(user_id=user.id, languagetoteach='English',
                          rate=10.000, approved=True)
        db.session.add(tinfo)
        db.session.commit()

    if not User.query.filter(User.username == 'd').first():
        user = User(email='d@d', name='Michelin Fargrara', username='d', phone='4444',
                    password='d', usertype=2, balance=100.0, photo=defaultpic, location="Abscance")
        db.session.add(user)
        db.session.commit()
        tinfo = TutorInfo(user_id=user.id, languagetoteach='Latin', rate=1.0001
                          , approved=True)
        db.session.add(tinfo)
        db.session.commit()

    if not User.query.filter(User.username == 'e').first():
        user = User(email='e@e', name='Karl Vostafo', username='e', phone='5555',
                    password='e', usertype=2, balance=100.0, photo=defaultpic, location="CBD")
        db.session.add(user)
        db.session.commit()
        tinfo = TutorInfo(user_id=user.id, languagetoteach='Alpha-Priori9',
                          rate=5, approved=False)
        db.session.add(tinfo)
        db.session.commit()

    if not User.query.filter(User.username == 't').first():
        user = User(email='t@t', name='Fridget Bard', username='t', phone='7412',
                    password='t', usertype=2, balance=100.0, photo=defaultpic)
        db.session.add(user)
        db.session.commit()
        tinfo = TutorInfo(user_id=user.id, languagetoteach='Eigo Jansuas',
                          rate=6.667676, approved=True)
        db.session.add(tinfo)
        db.session.commit()
        db.session.add(contactbc)
        # db.session.add(contactcb)
        db.session.commit()

    if not User.query.filter(User.username == 'u').first():
        user = User(email='u@u', name='Su F', username='u', phone='2147',
                        password='u', usertype=1, balance=0.0, photo=defaultpic, location="Trill")
        db.session.add(user)
        db.session.commit()

    if not User.query.filter(User.username == 'v').first():
        user = User(email='v@v', name='Marcus Jacob', username='v', phone='2147',
                    password='v', usertype=1, balance=1.0, photo=defaultpic, location="Kiki")
        db.session.add(user)
        db.session.commit()

    if not User.query.filter(User.username == 'w').first():
        user = User(email='w@w', name='Dale Tang', username='w', phone='2147',
                password='w', usertype=1, balance=25.0, photo=defaultpic, location="Signed")
        db.session.add(user)
        db.session.commit()

    if not Student_Groups.query.filter(Student_Groups.group_name == '1').first():
        new_group = Student_Groups(group_name='1', description="howdy",
                                   group_admin_id='2',
                                   meeting_day="Wednesday",
                                   location="Sydney", language="English",
                                   photo=None)
        db.session.add(new_group)
        db.session.commit()
        user_group = User_Group(user_id='2', group_id=new_group.id)
        db.session.add(user_group)
        db.session.commit()

    return render_template('homepage.html')


@app.route('/register/', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('SignUp.html')
    else:
        username = request.form['username']
        email = request.form['email']
        password1 = request.form['Password']
        password2 = request.form['ConfirmPassword']
        email_exist = User.query.filter(User.email == email).first()
        username_exist = User.query.filter(User.username == username).first()
        if username_exist:
            flash('The username has been used, please use another username')
            return render_template('SignUp.html')
        elif email_exist:
            flash('The email address has been used, please use another address')
            return render_template('SignUp.html')
        else:
            if password1 != password2:
                flash('Please enter the same password')
                return render_template('SignUp.html')
            else:
                if request.form.get('TermsAndCons'):
                    if request.form.get('becomeStudent') and request.form.get('becomeTutor'):
                        flash('Please choose only one role in the current stage')
                        return render_template('SignUp.html')
                    if request.form.get('becomeStudent'):

                        defaultpic = image_to_str('static/images/default-user-icon.jpg')
                        user = User(email=email, name='pholder', username=username, phone='0',
                                    password=password1, usertype=1, balance=0.0
                                    , photo=defaultpic)

                        db.session.add(user)
                        db.session.commit()
                        flash('Successfully registered as a Student')
                        return redirect(url_for('more_student', username=username))
                    if request.form.get('becomeTutor'):
                        defaultpic = image_to_str('static/images/default-user-icon.jpg')
                        user = User(email=email, name='pholder', username=username, phone='0',
                                    password=password1, usertype=2, balance=0.0
                                    , photo=defaultpic)
                        db.session.add(user)
                        db.session.commit()
                        tinfo = TutorInfo(user_id=user.id)
                        db.session.add(tinfo)
                        db.session.commit()
                        flash('Successfully registered as a Tutor')
                        return redirect(url_for('more_tutor', username=username))
                    return redirect(url_for('login'))
                else:
                    flash('Please read the legal documents and accept')
                    return render_template('SignUp.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('Login.html')
    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter(User.email == email).first()
        if user and user.password == password:
            session['user_id'] = user.id
            login_user(user)
            return redirect(url_for('profile'))
        else:
            flash("Login failed")
    return render_template('Login.html')


@app.route('/more_student/<username>', methods=['POST', 'GET'])
def more_student(username):
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        language = request.form['language']
        phone = request.form['phone']
        photo = request.files['photo']
        user = db.session.query(User).filter(User.username == username).first()
        if name:
            user.name = name
        if phone:
            user.phone = phone
        if language:
            user.languagetolearn = language
        if location:
            user.location = location
        if photo:
            user.photo = photo.read()
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('Moredetail_student.html', username=username)


@app.route('/more_tutor/<username>', methods=['POST', 'GET'])
def more_tutor(username):
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        location = request.form['location']
        language = request.form['language']
        photo = request.files['photo']
        id_file = request.files['fileToUpload_id']
        qualifile = request.files['fileToUpload_cer']
        user = db.session.query(User).filter(User.username == username).first()
        tutor = db.session.query(TutorInfo).filter(TutorInfo.user_id == user.id).first()
        if name:
            user.name = name
        if phone:
            user.phone = phone
        if language:
            tutor.languagetoteach = language
        if location:
            user.location = location
        tutor.level = 0
        if photo:
            user.photo = photo.read()
        if id_file:
            id_string = id_file.read()
            tutor.idfile = id_string
            user.idfile = id_string
        if qualifile:
            quali_String = qualifile.read()
            tutor.qualifile = quali_String
            user.qualifile = quali_String
        tutor.approved = False
        db.session.commit()
        flash("Please complete the advanced test for {} after logging in".format(language))
        return redirect(url_for('login'))
    return render_template('Moredetail_tutor.html', username=username)


@app.route('/become_tutor/<username>', methods=['POST', 'GET'])
@login_required
def become_tutor(username):
    if request.method == 'POST':
        language = request.form['language']
        id_file = request.files['fileToUpload_id']
        qualifile = request.files['fileToUpload_cer']
        user = User.query.filter(User.username == username).first()
        user.usertype = 2
        tutor = TutorInfo(user_id=user.id, languagetoteach=language, level=0, approved=False)
        if id_file:
            tutor.idfile = id_file.read()
        if qualifile:
            tutor.qualifile = qualifile.read()
        db.session.add(tutor)
        db.session.commit()
        flash("Please complete the advanced test for {}".format(language))
        return redirect(url_for('find_test'))
    return render_template('Become_tutor.html')


@app.route('/remove_tutor/<username>')
@login_required
def remove_tutor(username):
    if current_user.usertype != 3:
        flash("You do not have this authority")
    else:
        user = User.query.filter(User.username == username).first()
        # If user is student or admin
        if user.usertype != 2:
            flash("User {} is not a tutor".format(username))
        else:
            tutor = TutorInfo.query.filter(TutorInfo.user_id == user.id).first()
            tutor.approved = False
            db.session.commit()
            flash("User {} has been removed as a tutor".format(username))
    return redirect(url_for('user', username=username))


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    tutorinfo = current_user.tutorinfo
    tutor = []
    if current_user.usertype == 1:
        appointments = Appointment.query.filter(Appointment.student_id == current_user.id).all()
        for i in appointments:
            tutor.append(User.query.filter(User.id == i.tutor_id).first())
    else:
        appointments = Appointment.query.filter(Appointment.tutor_id == current_user.id).all()
        sum = 0
        count = 0
        for i in appointments:
            if i.rate != 0:
                sum += i.rate
                count += 1
        if count > 0:
            tutorinfo.rate = sum / count
            db.session.commit()
    # if request.form == 'POST':

    #     return render_template('profile.html', tutor=tutor, appointments=appointments)
    # tutorinfo = current_user.tutorinfo
    return render_template('profile.html', tutorinfo=tutorinfo, appointments=appointments, tutor=tutor)


@app.route('/event_logo/', methods=['POST', 'GET'])
@login_required
def event_logo():
    id = session['user_id']
    user = User.query.filter(User.id == id).first()
    return app.response_class(user.photo, mimetype='application/octet-stream')


@app.route('/display_image/<id>')
@login_required
def display_image(id):
    post = Post.query.filter(Post.id == id).first()
    return app.response_class(post.photo, mimetype='application/octet-stream')


@app.route('/display_image_user/<id>')
@login_required
def display_image_user(id):
    user = User.query.filter(User.id == id).first()
    return app.response_class(user.photo, mimetype='application/octet-stream')


@app.route('/display_idfile/<id>')
@login_required
def display_idfile(id):
    tutor = User.query.filter(User.id == id).first()
    return app.response_class(tutor.tutorinfo.idfile, mimetype='application/pdf')


@app.route('/display_qualifile/<id>')
@login_required
def display_qualifile(id):
    tutor = User.query.filter(User.id == id).first()
    return app.response_class(tutor.tutorinfo.qualifile, mimetype='application/pdf')


@app.route('/delete_photo_post/<id>')
@login_required
def delete_photo_post(id):
    post = Post.query.filter(Post.id == id).first()
    post.photo = None
    db.session.commit()
    return redirect(url_for("view_post", id=id))


@app.route('/display_image_group/<id>')
@login_required
def display_image_group(id):
    group = Student_Groups.query.filter(Student_Groups.id == id).first()
    return app.response_class(group.photo, mimetype='application/octet-stream')


@app.route('/delete_photo_group/<id>')
@login_required
def delete_photo_group(id):
    group = Student_Groups.query.filter(Student_Groups.id == id).first()
    group.photo = None
    db.session.commit()
    return redirect(url_for("view_group", id=id))


@app.route('/forum', methods=['POST', 'GET'])
def forum():
    if current_user.is_anonymous:
        flash("Please login to access this page.")
        return redirect(url_for('login'))
    posts = Post.query.all()
    return render_template('Forum.html', posts=posts)


@app.route('/create_post', methods=['POST', 'GET'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        label = request.form['label']
        photo = request.files['photo']
        post = Post(title=title, content=body, author_id=current_user.id, label=label)
        db.session.add(post)
        if photo:
            photo_string = photo.read()
            post.photo = photo_string
        db.session.commit()
        return redirect(url_for('view_post', id=post.id))
    return render_template('Create_post.html')

@app.route('/view_post/<id>', methods=['POST', 'GET'])
@login_required
def view_post(id):
    post = Post.query.filter(Post.id == id).first()
    comments = []
    if request.method == 'POST':
        comment = request.form['comment']
        ans = Answer(post_id=post.id, content=comment, author_id=current_user.id, post_date=datetime.utcnow())
        db.session.add(ans)
        db.session.commit()
    comments = Answer.query.filter(Answer.post_id == id).all()
    return render_template('View_post.html', post=post, comments=comments)


@app.route('/edit_post/<id>', methods=['POST', 'GET'])
@login_required
def edit_post(id):
    post = Post.query.filter(Post.id == id).first()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        label = request.form['label']
        photo = request.files['photo']
        if title:
            post.title = title
        if body:
            post.content = body
        if label:
            post.label = label
        if photo:
            photo_string = photo.read()
            post.photo = photo_string
        db.session.commit()
        return redirect(url_for('view_post', id=id))
    return render_template('Edit_post.html', post=post)


@app.route('/edit_comment/<post_id>/<comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(post_id, comment_id):
    post = Post.query.filter(Post.id == post_id).first()
    answer = Answer.query.filter(Answer.id == comment_id).first()
    if request.method == 'POST':
        comment = request.form['edit_comment']
        if comment:
            answer.content = comment
            answer.post_date = datetime.utcnow()
            db.session.commit()
        return redirect(url_for('view_post', id=post_id))
    return render_template('Edit_comment.html', post=post, comment=answer)


@app.route('/delete_post/<id>', methods=['GET'])
@login_required
def delete_post(id):
    # Delete all comments first
    Answer.query.filter(Answer.post_id == id).delete()
    Post.query.filter(Post.id == id).delete()
    db.session.commit()
    flash("Post has been deleted")
    return redirect(url_for('forum'))


@app.route('/delete_comment/<post_id>/<comment_id>', methods=['POST', 'GET'])
@login_required
def delete_comment(post_id, comment_id):
    Answer.query.filter(Answer.id == comment_id).delete()
    db.session.commit()
    flash("Comment has been deleted")
    return redirect(url_for('view_post', id=post_id))

@app.route('/find_tutor', methods=['POST', 'GET'])
def find_tutor():
    if current_user.is_anonymous:
        flash("Please login to access this page.")
        return redirect(url_for('login'))
    tutor = TutorInfo.query.filter(TutorInfo.approved == True).all()
    return render_template('Find_tutor.html', tutor=tutor)

@app.route('/videos', methods=['POST', 'GET'])
def videos():
    if current_user.is_anonymous:
        flash("Please login to access this page.")
        return redirect(url_for('login'))
    videos = Video.query.all()
    return render_template('Videos.html', videos=videos)


@app.route('/find_groups')
def find_groups():
    if current_user.is_anonymous:
        flash("Please login to access this page.")
        return redirect(url_for('login'))
    groups = Student_Groups.query.all()
    return render_template('Find_groups.html', groups=groups)


@app.route('/user/<username>', methods=['POST', 'GET'])
@login_required
def user(username):
    # if attempting to access admin
    if username == 'admin':
        flash("Access denied")
        return redirect(url_for("homepage"))
    user = User.query.filter(User.username == username).first()

    # if user doesnt exist
    if not user:
        flash('Username ' + username + ' not found')
        return redirect(url_for('homepage'))

    # if user is trying to access himself, go to profile
    if user.id == current_user.id:
        return redirect(url_for('profile'))

    tutor = user.tutorinfo
    contact = Contact.query.filter((Contact.user_id == current_user.id) &
                                   (Contact.target_id == user.id)).first()

    if request.method == 'POST':
        reason = request.form['reason']
        if reason == '':
            flash("You must enter a valid reason")
            return render_template('Report_user.html', username=username)
        user1 = User.query.filter(User.username == username).first()
        report = Report(user1_id=user1.id, user2_id=current_user.id, reason=reason)
        db.session.add(report)
        db.session.commit()
        flash("Your report has been submitted")
        return render_template('Other_profile.html', user=user, contact=contact, tutor=tutor)
        # TODO flashes for error messages
        # appt = Appointment(student_id=current_user.id, tutor_id=user.id, pending=1)
        # db.session.add(appt)
        # db.session.commit()

        # user = User(email=email, name='pholder', username=username, phone='0',
        #             password=password1, usertype=1, balance=0.0)

    # if contact.user_id == current_user.id:
    #     contact = None
    return render_template('Other_profile.html', user=user, contact=contact, tutor=tutor)


@app.route('/logout')
def logout():
    if current_user:
        logout_user()
    return redirect(url_for('homepage'))


@app.route('/create_appointment/<username>', methods=['POST', 'GET'])
@login_required
def create_appointment(username):
    user = User.query.filter(User.username == username).first()
    tutor = TutorInfo.query.filter(TutorInfo.user_id == user.id).first()
    if tutor.approved == False:
        flash("This tutor is no longer accepting appointments")
        return redirect(url_for("user", username=username))
    curuser = User.query.filter(User.username == current_user.username).first()
    if request.method == 'POST':
        start_time = request.form['start_time']
        if start_time == '':
            flash("Please input a valid date and time")
            return redirect(url_for('create_appointment', username=username))
        add = request.form['address']            
        duration = request.form['duration']
        price = 50 * float(duration) / 60
        if curuser.balance < 25:
            flash(
                "You do not have enough credits for this booking. Please top up using the payment option. Please note: All bookings are 50 credits per hour and the minimum booking is 30 mins")
            return redirect(url_for('payment'))
        app = Appointment(student_id=current_user.id, tutor_id=tutor.user_id, address=add,
            start_time=start_time, duration=duration, total_price=price, rate=0)
        db.session.add(app)
        db.session.commit()
        flash("Appointment made. Awaiting tutor's confirmation")
        return redirect(url_for('user', username=username))
    return render_template('Create_appointment.html', tutor=user)


@app.route('/create_group', methods=['POST', 'GET'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['desc']
        location = request.form['location']
        language = request.form['language']
        day = request.form['day']
        time = request.form['start_time']
        photo = request.files['photo']
        if name == '':
            name = current_user.username + "'s group"
        new_group = Student_Groups(group_name=name, description=desc,
                                   group_admin_id=current_user.id, meeting_day=day,
                                   meeting_time=time, location=location, language=language, photo=None)
        db.session.add(new_group)
        db.session.commit()
        user_group = User_Group(user_id=current_user.id, group_id=new_group.id)
        db.session.add(user_group)
        if photo:
            new_group.photo = photo.read()
        db.session.commit()
        return redirect(url_for('view_group', id=new_group.id))
    return render_template('Create_group.html')


@app.route('/view_group/<id>', methods=['POST', 'GET'])
@login_required
def view_group(id):
    group = Student_Groups.query.filter(Student_Groups.id == id).first()
    user_member = User_Group.query.filter(User_Group.group_id == id).filter(
        User_Group.user_id == current_user.id).first()
    all_users = User.query.all()
    is_member = 0
    if user_member is None:
        is_member = 1
    if request.method == 'POST':
        if group.group_admin_id == current_user.id:
            member_list = request.form['member']
            member = member_list.split(', ')
            for i in member:
                y = i.split()
                for j in y:
                    new_member = User.query.filter(User.username == j).first()
                    if new_member:
                        member_exist = User_Group.query.filter(User_Group.group_id == id).filter(
                            User_Group.user_id == new_member.id).first()
                        if member_exist:
                            flash("{} is already a member of this group".format(new_member.username))
                        else:
                            new_member_group = User_Group(user_id=new_member.id, group_id=id)
                            db.session.add(new_member_group)
                            db.session.commit()
                            flash("{} has been added to the group".format(j))
                    else:
                        flash("User {} does not exist".format(j))
        else:
            flash("You are not allowed to add members to this group")
    members = User_Group.query.filter(User_Group.group_id == id).all()
    return render_template("View_group.html", group=group, members=members, is_member=is_member, all_users=all_users)


@app.route('/join_group/<id>')
@login_required
def join_group(id):
    group = Student_Groups.query.filter(Student_Groups.id == id).first()
    # print("entered join group")
    if group:
        user_group = User_Group(user_id=current_user.id, group_id=id)
        db.session.add(user_group)
        db.session.commit()
        flash("You have succesfully joined the group")
        return redirect(url_for('view_group', id=id))
    else:
        flash("Error group cannot be found")
        return redirect(url_for('find_group'))


@app.route('/leave_group/<id>')
@login_required
def leave_group(id):
    group = Student_Groups.query.filter(Student_Groups.id == id).first()
    if group:
        if int(current_user.id) == int(group.group_admin_id):
            flash("You cannot leave a group where you are the admin. Please delete the group instead.")
        else:
            delete_user = User_Group.query.filter(
                User_Group.user_id == current_user.id and User_Group.group_id == id).first()
            if delete_user:
                db.session.delete(delete_user)
                db.session.commit()
                flash("You have succesfully left the group")
            else:
                flash("You cannot leave a group that you did not join")
        return redirect(url_for('view_group', id=id))
    else:
        flash("Error group cannot be found")
        return redirect(url_for('find_group'))


@app.route('/add_member/<id>')
@login_required
def add_member(id):
    group = Student_Groups.query.filter(Student_Groups.id == id).first()
    if group.group_admin_id == current_user.id:
        return render_template("Add_group_member.html", group=group)
    else:
        flash("You are not allowed to add members")
        return redirect(url_for('view_group', id=id))

@app.route('/edit_group/<id>', methods=['POST', 'GET'])
@login_required
def edit_group(id):
    group = Student_Groups.query.filter(Student_Groups.id == id).first()
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['desc']
        location = request.form['location']
        language = request.form['language']
        time = request.form['start_time']
        photo = request.files['photo']
        if name:
            group.group_name = name
        if desc:
            group.desc = desc
        if location:
            group.location = location
        if language:
            group.language = language
        if time:
            day = request.form['day']
            group.meeting_day = day
            group.meeting_time = time
        if photo:
            group.photo = photo.read()
        db.session.commit()
        return redirect(url_for('view_group', id=id))
    return render_template('Edit_group.html', group=group)


@app.route('/remove_group_member/<id>')
@login_required
def remove_group_member(id):
    user = User_Group.query.filter(User_Group.user_id == id).first()
    group_id = user.group_id
    group = Student_Groups.query.filter(Student_Groups.id == group_id).first()
    if int(group.group_admin_id) == int(id):
        flash("You cannot remove group admin")
        return redirect(url_for('view_group', id=group_id))
    else:
        db.session.delete(user)
        db.session.commit()
        flash("You have successfully removed a group member")
        return redirect(url_for('view_group', id=group_id))


@app.route('/delete_group/<id>')
@login_required
def delete_group(id):
    users = User_Group.query.filter(User_Group.group_id == id).all()
    for i in users:
        db.session.delete(i)
    group = Student_Groups.query.filter(Student_Groups.id == id).first()
    db.session.delete(group)
    db.session.commit()
    flash("You have successfully deleted a group")
    return redirect(url_for('find_groups'))

@app.route('/edit_profile/', methods=['POST', 'GET'])
@login_required
def edit_profile():
    teach = None
    if request.method == 'POST':
        oldpassword = request.form['oldpassword']
        password1 = request.form['password1']
        password2 = request.form['password2']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        location = request.form['location']
        learn = request.form['learn']
        photo = request.files['photo']
        if current_user.tutorinfo != None:
            teach = request.form['teach']
        if oldpassword or password1 or password2:
            if oldpassword != current_user.password:
                flash("Current password is invalid")
                return render_template("Edit_profile.html")
            if password1 != password2:
                flash('Please enter the same password')
                return render_template('Edit_profile.html')
            if password1:
                current_user.password = password1
        if name:
            current_user.name = name
        if email:
            current_user.email = email
        if phone:
            current_user.phone = phone
        if location:
            current_user.location = location
        if learn:
            current_user.languagetolearn = learn
        if teach:
            current_user.tutorinfo.languagetoteach = teach
        if photo:
            photo_string = photo.read()
            current_user.photo = photo_string
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('Edit_Profile.html', tutor=current_user.tutorinfo)

@app.route('/edit_files/<username>', methods=['POST', 'GET'])
@login_required
def edit_files(username):
    user = User.query.filter(User.username == username).first()
    tutorinfo = TutorInfo.query.filter(TutorInfo.user_id == user.id).first()
    if request.method == 'POST':
        id_file = request.files['fileToUpload_id']
        qualifile = request.files['fileToUpload_cer']
        if id_file:
            tutorinfo.idfile = id_file.read()
        if qualifile:
            tutorinfo.qualifile = qualifile.read()
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('Edit_files.html', user=user, tutorinfo=tutorinfo)


@app.route('/view_appointment/<id>', methods=['POST', 'GET'])
@login_required
def view_appointment(id):
    appt = Appointment.query.filter(Appointment.appointment_id == id).first()
    if request.method == 'POST':
        if current_user.usertype == 2:
            if appt.approved == True:
                appt.approved = False
            else:
                appt.approved = True
            db.session.commit()
        else:
            rate = request.form['rate']
            appt.rate = rate
            db.session.commit()

            appointments = Appointment.query.filter(Appointment.tutor_id == appt.tutor_id).all()
            sum = 0
            count = 0
            for i in appointments:
                if i.rate != 0:
                    sum += i.rate
                    count += 1
            if count > 0:
                appt.tutor.rate = sum / count
            db.session.commit()
    return render_template("View_appointment.html", appt=appt, datetime=datetime)


@app.route('/report_user/<username>', methods=['POST', 'GET'])
@login_required
def report_user(username):
    if current_user.usertype == 3:
        flash("You cannot report a user as an admin")
        return redirect(url_for('user', username=username))
    if request.method == 'POST':
        reason = request.form['reason']
        if reason == '':
            flash("You must enter a valid reason")
            return render_template('Report_user.html', username=username)
        user1 = User.query.filter(User.username == username).first()
        report = Report(user1_id=user1.id, user2_id=current_user.id, reason=reason)
        db.session.add(report)
        db.session.commit()
        flash("Your report has been submitted")
        return redirect(url_for('user', username=user1.username))
    return render_template('Report_user.html', username=username)


@app.route('/view_report/<id>', methods=['POST', 'GET'])
@login_required
def view_report(id):
    if current_user.usertype != 3:
        flash("Access denied")
        return redirect(url_for('homepage'))
    report = Report.query.filter(Report.id == id).first()
    if request.method == 'POST':
        if request.form['status_btn'] == 'approved':
            report.status = 'Approved'
        elif request.form['status_btn'] == 'reject':
            report.status = 'Rejected'
        db.session.commit()
    user1 = []
    user2 = []
    if report:
        user1 = User.query.filter(User.id == report.user1_id).first()
        user2 = User.query.filter(User.id == report.user2_id).first()
    return render_template("View_report.html", report=report, user1=user1, user2=user2)


@app.route('/reports')
@login_required
def reports():
    if current_user.usertype != 3:
        flash("Access denied")
        return redirect(url_for('homepage'))
    reports = Report.query.all()
    return render_template("Reports.html", reports=reports)


@app.route('/view_verify/<id>', methods=['POST', 'GET'])
@login_required
def view_verify(id):
    if current_user.usertype != 3:
        flash("Access denied")
        return redirect(url_for('homepage'))
    tutor = User.query.filter(User.id == id).first()
    test = []
    test = Test_Answer.query.filter(Test_Answer.user_id == tutor.id).first()
    if request.method == 'POST':
        if request.form['status_btn'] == 'approved':
            tutor.tutorinfo.approved = True
        elif request.form['status_btn'] == 'reject':
            tutor.tutorinfo.approved = False
        db.session.commit()

    return render_template("View_verify.html", tutor=tutor, test=test)


@app.route('/verify')
@login_required
def verify():
    if current_user.usertype != 3:
        flash("Access denied")
        return redirect(url_for('homepage'))
    info = User.query.filter(User.usertype == 2).all()
    tutorinfo = []
    for i in info:
        tutorinfo.append(i.tutorinfo)
    return render_template("Verify.html", info=info, tutorinfo=tutorinfo)


@app.route('/add_balance/<username>', methods=['POST', 'GET'])
@login_required
def add_balance(username):
    if current_user.usertype != 3:
        flash("Access denied")
        return redirect(url_for('homepage'))
    user = User.query.filter(User.username == username).first()
    if request.method == 'POST':
        credit = request.form['credits']
        user.balance += float(credit)
        db.session.commit()
        return redirect(url_for('user', username=username))
    return render_template("Add_balance.html", username=username)


@app.route('/payment')
@login_required
def payment():
    return render_template("Payment.html")


@app.route('/get_payment')
@login_required
def get_payment():
    app = Appointment.query.all()
    for a in app:
        if a.paid == False and a.approved == True:
            a.student.balance -= a.total_price
            a.tutor.user.balance += a.total_price
            a.paid = True
            db.session.commit()
    return redirect(url_for('profile'))


@app.route('/add_contact/<target_id>')
@login_required
def add_contact(target_id):
    contact = Contact.query.filter((Contact.user_id == current_user.id) &
                                   (Contact.target_id == target_id)).first()
    if not contact:
        contact = Contact(user_id=current_user.id, target_id=target_id)
        db.session.add(contact)
        db.session.commit()
    user = User.query.filter(User.id == target_id).first()
    return render_template('Other_profile.html', user=user, contact=contact, tutor=user.tutorinfo)


@app.route('/remove_contact/<target_id>')
@login_required
def remove_contact(target_id):
    # if not target_id:
    #   target_id = request.args.get('targetid', 0, type=int)
    contact = Contact.query.filter((Contact.user_id == current_user.id) &
                                   (Contact.target_id == target_id)).first()
    if contact:
        db.session.delete(contact)
        db.session.commit()
    user = User.query.filter(User.id == target_id).first()
    return render_template('Other_profile.html', user=user, contact=None, tutor=user.tutorinfo)


@app.route('/create_test/', methods=['POST', 'GET'])
@login_required
def create_test():
    if request.method == 'POST':
        language = request.form['language']
        level = request.form['level']
        test = Test(language=language, level=level)
        db.session.add(test)
        db.session.commit()
        q1 = request.form['question1']
        if q1:
            a1 = request.form['a1']
            q2 = request.form['q2']
            a2 = request.form['a2']
            q3 = request.form['q3']
            a3 = request.form['a3']
            test.q1 = q1
            test.a1 = a1
            test.q2 = q2
            test.a2 = a2
            test.q3 = q3
            test.a3 = a3
        q4 = request.form['q4']
        if q4:
            a4 = request.form['a4']
            q5 = request.form['q5']
            a5 = request.form['a5']
            q6 = request.form['q6']
            a6 = request.form['a6']
            test.q4 = q4
            test.a4 = a4
            test.q5 = q5
            test.a5 = a5
            test.q6 = q6
            test.a6 = a6
        q7 = request.form['q7']
        if q7:
            a7 = request.form['a7']
            test.q7 = q7
            test.a7 = a7
        q8 = request.form['q8']
        if q8:
            a8 = request.form['a8']
            test.q8 = q8
            test.a8 = a8
        q9 = request.form['q9']
        if q9:
            test.q9 = q9
        db.session.commit()
        return redirect(url_for('view_test', id=test.id))
    return render_template('Create_test.html')


@app.route('/view_test/<id>')
@login_required
def view_test(id):
    if current_user.usertype == 1:
        flash("You are not authorised to access this page")
        return redirect(url_for('homepage'))
    elif current_user.usertype == 2:
        tutor = TutorInfo.query.filter(TutorInfo.user_id == current_user.id).first()
        if tutor.approved == False:
            flash("You are not authorised to access this page")
            return redirect(url_for('homepage'))
    test = Test.query.filter(Test.id == id).first()
    if test:
        return render_template('View_test.html', test=test)
    flash("This test does not exist")
    return redirect(url_for("homepage"))

@app.route('/find_test/')
def find_test():
    if current_user.is_anonymous:
        flash("Please login to access this page.")
        return redirect(url_for('login'))
    tests = Test.query.all()
    approved = False
    if current_user.usertype == 2:
        tutor = TutorInfo.query.filter(TutorInfo.user_id == current_user.id).first()
        if tutor.approved == True:
            approved = True
    return render_template('Find_test.html', tests=tests, approved=approved)


@app.route('/attempt_test/<id>', methods=['POST', 'GET'])
@login_required
def attempt_test(id):
    if current_user.usertype == 3:
        flash("You cannot attempt this test")
        return redirect('view_test', id=id)
    test = Test.query.filter(Test.id == id).first()
    if request.method == 'POST':
        answer = Test_Answer(test_id=id, user_id=current_user.id)
        db.session.add(answer)
        db.session.commit()
        answer.a1 = request.form['a1']
        answer.a2 = request.form['a2']
        answer.a3 = request.form['a3']
        answer.a4 = request.form['a4']
        answer.a5 = request.form['a5']
        answer.a6 = request.form['a6']
        answer.a7 = request.form['a7']
        answer.a8 = request.form['a8']
        answer.a9 = request.form['a9']
        db.session.commit()
        mark = 0
        if answer.a1 == test.a1:
            mark += 1
        if answer.a2 == test.a2:
            mark += 1
        if answer.a3 == test.a3:
            mark += 1
        if answer.a4 == test.a4:
            mark += 1
        if answer.a5 == test.a5:
            mark += 1
        if answer.a6 == test.a6:
            mark += 1
        if answer.a7 == test.a7:
            mark += 1
        if answer.a8 == test.a8:
            mark += 1
        answer.mark = mark
        db.session.commit()
        flash("Your test will be marked and marks will be shown to the admin")
        return redirect(url_for('homepage'))
    return render_template('Attempt_test.html', test=test)

@app.route('/find_all_completed_test_by_user/<user_id>')
@login_required
def find_all_completed_test_by_user(user_id):
    test_attempt = Test_Answer.query.filter(Test_Answer.user_id == user_id).all()
    user = User.query.filter(User.id == user_id).first()
    return render_template('View_user_completed_test.html', all_test=test_attempt, user=user)

@app.route('/view_test_attempt/<test_attempt_id>')
@login_required
def view_test_attempt(test_attempt_id):
    test_attempt = Test_Answer.query.filter(Test_Answer.id == test_attempt_id).first()
    ans = Test.query.filter(Test.id == test_attempt.test_id).first()
    return render_template('View_completed_test.html', test=test_attempt, ans=ans)

# upload video start
ALLOWED_EXTENSIONS = set(['mp4', 'MOV'])
app.config['UPLOAD_FOLDER'] = os.getcwd()+"/static/videos/"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload_video', methods=['GET', 'POST'])
@login_required
def upload_video():
    if request.method == 'POST':
        file = request.files['file']
        language = request.form['language']
        name = request.form['name']
        if file and allowed_file(file.filename):
            if name == '':
                name = file.filename
            u_id = current_user.id
            path = os.path.join(app.config['UPLOAD_FOLDER'], name)
            video = Video(user_id=u_id, name=name, path=path, language=language)
            file.save(path)
            db.session.add(video)
            db.session.commit()
            flash("Your video has been uploaded")
            return redirect(url_for('videos'))
        else:
            flash("File could not be read. Please ensure it is in an MP4 format")
    return render_template('Upload_video.html')
# upload video end

@app.route('/delete_video/<vid_id>')
@login_required
def delete_video(vid_id):
    if current_user.usertype == 3:
        vid = Video.query.filter(Video.id == vid_id).delete()
        db.session.commit()
        flash("You have successfully deleted this video")
    else:
        flash("You have no authority for this action")
    return redirect(url_for('videos'))

if __name__ == '__main__':
    socketio.run(app, debug=True)
    # app.run()
