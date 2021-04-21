from datetime import datetime
from Planner import db
from flask_login import UserMixin


class Comments(db.Model):
    cid = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable="False", default="...")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.pid'))
    timestamp = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow())

    def __repr__(self):
        return f"for {self.comment_to} at {self.timestamp}"


class Post(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False, default='No Subject')
    html = db.Column(db.Text)
    likes = db.Column(db.Integer(), default=0)
    timestamp = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow())
    posted_by = db.Column(db.Integer(), db.ForeignKey('user.id'))
    comments = db.relationship('Comments', backref='comment_to', lazy='dynamic')

    def __repr__(self):
        return f"{self.subject}"


# connect like to a person instead of a number - make a post-user like relationship, if the relationship already exists, then cannot like again

# 1dc3046810ae -> 6e7ffd5462d8, empty message is the latest upgrade
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='Anon')
    img = db.Column(db.Text, nullable=False, default='default.jpg')
    about = db.Column(db.Text)
    email = db.Column(db.String(150), nullable=False, unique=True)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    comments = db.relationship('Comments', backref='commenter', lazy='dynamic')
    posts = db.relationship('Post', backref='poster', lazy='dynamic')
    work = db.relationship('Events', backref='worker', lazy='dynamic')

    def __repr__(self):
        return f"{self.email}"


class Events(db.Model):
    eid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, default='No Subject')
    assigned = db.Column(db.Integer(), db.ForeignKey('user.id'))
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        return f"{self.title}"

