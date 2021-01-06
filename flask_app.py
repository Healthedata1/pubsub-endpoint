# A very simple Flask Hello World app for you to get started with...add a database
# save the data

from flask import Flask, request, Response, render_template, session
import os
from flask_sqlalchemy import SQLAlchemy
from logging.config import dictConfig
from datetime import datetime
from json import dumps, loads

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s %(lineno)d}: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'my_secret_key'

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(basedir, 'post.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
#migrate = Migrate(app, db)

#define models
'''
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>'
'''

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.PickleType())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Post |{self.id}|{self.body}|{self.timestamp}|>'


# Delete database file if it exists currently

if os.path.exists('post.db'):
    os.remove('post.db')

# Create the database
db.create_all()

# instantiate db
'''
u = User(username='susan', email='susan@example.com')
db.session.add(u)
db.session.commit()
app.logger.info(f'u = {repr(u)}')

app.logger.info(f'query = {session.query(Post).all()}')
'''
#session['notified'] = "false"
#see add_url_rule to conditionally open rest hook.= e.g after subscribing"
@app.route('/webhook', methods=['POST'])
def respond():
    # webhook logic to do something
    app.logger.info(request.json)
    row = Post(body=request.json)
    db.session.add(row)
    db.session.commit()
    app.logger.info(f'query = {db.session.query(Post).all()}')
    return Response(status=200)

@app.route('/')
def hello_world():
    posts = db.session.query(Post).all()
    return render_template('index.html', posts = posts)

if __name__ == '__main__':
    app.run(debug=True)
