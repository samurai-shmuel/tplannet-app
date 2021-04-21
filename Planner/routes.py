import secrets
import os
from cryptography.fernet import Fernet
from Planner import app, db, mail
from flask_mail import Message
from datetime import datetime
from flask import render_template, request, redirect, session, g, url_for
from Planner.models import Post, User, Comments, Events
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from Planner import admin
from flask_admin.contrib.sqla import ModelView


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

key = Fernet.generate_key()
fernet = Fernet(key)


@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        check_user = User.query.filter_by(email=request.form['username']).first()
        if not check_user:
            return "<h1>Input your user details properly</h1>"
        boole = request.form.get('logged')
        if check_user.verified:
            if request.form['password'] == 'lionsbelly':
                login_user(check_user, remember=boole)
                return redirect('/tplanner')
            else:
                return '<h1>Invalid Username or Password</h1>'
        else:
            return '<h1>Wait for the mail from the admin</h1>'
    return render_template('index.html')


@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))


@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']


@app.route('/register', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        enc_email = fernet.encrypt(email.encode())
        name = request.form.get('name')
        new_user = User(email=email, name=name)
        msg = Message(f"Request to join the team", recipients=['msm19b002@iiitdm.ac.in'])
        msg.html = f'A new teammate is coming to join with the following details: <br> Name: {name} <br> Email: {email}. To let him in <a href="localhost/permission/params?mail={enc_email}">click here</a> '
        mail.send(msg)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/')
    return render_template('signup.html')


@app.route('/permissions', methods=['GET','POST'])
def permissions():
    email = request.args['mail']
    email = fernet.decrypt(email.decode())
    user = User.query.filter_by(email=email)
    user.verified = True
    db.session.commit()
    msg = Message(f"Request to join the team", recipients=[email])
    msg.html = f'<h1>Congratulations<h1> You have made the team! Login with the password = "lionsbelly"'
    mail.send(msg)


def save_pic(pic):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(pic.filename)
    pic_fn = random_hex + f_ext
    pic_path = os.path.join(app.root_path, 'static/profpics', pic_fn)
    pic.save(pic_path)
    return pic_fn


@app.route('/tplanner/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        pic = request.files['pic']
        if not pic:
            return 'No pic uploaded', 400
        current_user.img = save_pic(pic)
        db.session.commit()
        return redirect('/tplanner/profile')
    image_file = url_for('static', filename='profpics/' + current_user.img)
    return render_template('profile.html', image=image_file, user=current_user)


@app.route('/tplanner/profile/about-upload', methods=['POST'])
@login_required
def about_upload():
    current_user.about = request.form.get('about_me')
    db.session.commit()
    return redirect('/tplanner/profile')


@app.route('/tplanner', methods=['GET','POST'])
@login_required
def tplanner():
    name = current_user.name.split(' ')
    firstName = name[0]
    return render_template('tplanner.html', user=current_user, name=firstName)


@app.route('/about', methods=['GET','POST'])
def about():
    return render_template('about.html', user=current_user)


@app.route('/tplanner/about', methods=['GET','POST'])
@login_required
def about_within():
    return render_template('about.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/tplanner/tlogger/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        new_post = Post(subject=request.form.get('subject'), html=request.form.get('editordata'), poster=current_user)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/tplanner/tlogger/posts')
    return render_template('create_post.html', user=current_user)


@app.route('/tplanner/tlogger/posts', methods=['GET', 'POST'])
def posts():
    q = request.args.get('search')
    if q:
        all_posts = Post.query.filter(Post.subject.contains(q))
    else:
        all_posts = Post.query.all()
    all_comments = Comments.query.all()
    return render_template('posts.html', posts=all_posts, comments=all_comments, user=current_user)


@app.route('/posts/comment/<int:pid>', methods=['GET', 'POST'])
def comment(pid):
    if request.method == 'POST':
        post = Post.query.filter_by(pid=pid).first()
        new_com = Comments(comment=request.form.get('commentdata'), commenter=current_user, comment_to=post)
        db.session.add(new_com)
        db.session.commit()
    return redirect('/tplanner/tlogger/posts')


@app.route('/posts/deletec/<int:cid>', methods=['GET'])
def delete_comment(cid):
    comment = Comments.query.get_or_404(cid)
    if comment.commenter == current_user:
        db.session.delete(comment)
        db.session.commit()
    return redirect('/tplanner/tlogger/posts')


@app.route('/posts/delete/<int:id>', methods=['GET'])
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.poster == current_user:
        db.session.delete(post)
        db.session.commit()
    return redirect('/tplanner/tlogger/posts')

# https://www.youtube.com/watch?v=0yid46tNIDw - update in sqlalchemy


@app.route('/posts/like/<int:pid>', methods=['GET', 'POST'])
def like(pid):
    if request.method == 'POST':
        post = Post.query.filter_by(pid=pid).first()
        if post.poster != current_user:
            post.likes = post.likes + 1
            db.session.commit()
    return redirect('/tplanner/tlogger/posts')


@app.route('/tplanner/calendar', methods=['GET', 'POST'])
def calendar():
    q = request.args.get('search')
    if q:
        events = Events.query.filter(Events.title.contains(q) | Events.description.contains(q) | Events.deadline.contains(q))
    else:
        events = Events.query.all()
    return render_template('calendar2.html', user=current_user, events=events)


@app.route('/tplanner/calendar/new', methods=['GET', 'POST'])
def new_event():
    if request.method == 'POST':
        date = request.form.get('deadline')
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        event = Events(title=request.form.get('title'), description=request.form.get('description'), deadline=date, assigned=request.form.get('worker'))
        db.session.add(event)
        db.session.commit()
        return redirect('/tplanner/calendar')


@app.route('/calendar/delete/<int:eid>', methods=['GET'])
def delete_event(eid):
    del_event = Events.query.get_or_404(eid)
    db.session.delete(del_event)
    db.session.commit()
    return redirect('/tplanner/calendar')


@app.route('/tplanner/repository', methods=['GET', 'POST'])
def repository():
    return render_template('repos.html', user=current_user)


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Comments, db.session))
admin.add_view(ModelView(Events, db.session))
admin.add_view(ModelView(Post, db.session))