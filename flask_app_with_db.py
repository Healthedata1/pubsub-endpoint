# A very simple Flask Hello World app for you to get started with using a database
#  just save and display subscription notifications data

from flask import Flask, request, Response, render_template, session
import os
from flask_sqlalchemy import SQLAlchemy
import logging
from datetime import datetime
from json import dumps, loads

logging.basicConfig(
level=logging.DEBUG,
format='[%(asctime)s] %(levelname)s in %(module)s %(lineno)d}: %(message)s')

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 'my_secret_key'

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = True
# for local build
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(basedir, 'post.db')
# for pythonanywhere
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/healthedatainc2/mysite/post.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
#migrate = Migrate(app, db)

#define models

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.PickleType())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    type = db.Column(db.String(50), default='heartbeat')
    event_ids = db.Column(db.PickleType(),)

    def __repr__(self):
        return f'<Post |{self.id}|{self.type}|{self.body}|{self.timestamp}|>'

#create tables do this just once when update models...
db.create_all()

# then clear all tables in database after that
db.session.query(Post).delete()
db.session.commit()

#see add_url_rule to conditionally open rest hook.= e.g after subscribing"

@app.route('/webhook', methods=['POST'])
def respond():
    # webhook logic to do something
    app.logger.info(request.json)
    for e in request.json['entry']:
        try:
            type = next(p['valueCode'] for p in e['resource']['parameter'] \
             if e['resource']['resourceType'] == 'Parameters' and  p['name'] == 'type')
        except KeyError:
            event_ids = e['fullUrl']  # just one for utcnow
        else:
            event_ids = None
    row = Post(body=request.json, type=type, event_ids=event_ids)
    db.session.add(row)
    db.session.commit()
    app.logger.info(f'query = {db.session.query(Post).all()}')
    return Response(status=200)

@app.route('/')
def hello_world():
    posts = db.session.query(Post).all()
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)
