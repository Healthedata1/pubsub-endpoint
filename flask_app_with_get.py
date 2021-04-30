# A very simple Flask Hello World app for you to get started with...add a database
# save the data

import logging
import os
from datetime import datetime
from json import dumps, loads
from time import sleep
from fhirclient.r4models import encounter as E, bundle as B

from flask import Flask, Response, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from requests import get, post, put

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


def search(Type, params=None):
    '''
    Search resource Type with parameters. [base]/[Type]{?params=params}
    where params is a list of tuples
    return resource as request object
    '''

    headers = {
    'Accept':'application/fhir+json',
    'Content-Type':'application/fhir+json'
    }


    r_url = (f'http://hapi.fhir.org/baseR4/{Type}')

    app.logger.info(f' r_url = {r_url}***')
    for attempt in range(5): #retry request up to ten times
        sleep(1)  # wait a bit between retries
        with get(r_url, headers=headers, params=params) as r:
            app.logger.info(f'url-string = {r.url}')
            app.logger.info(f'status = {r.status_code}') #return r.status_code
            #app.logger.info(f'body = {r.json()}')# view  output
            #app.logger.info(f'body as json = {dumps(r.json(), indent=4)}')# view  output
            # return (r.json()["text"]["div"])
            if r.status_code <300:
                app.logger.info(f'query string = {r.url}')
                #app.logger.info(f'bundle entry count = {r.json()["total"]}')
                session['entry_count']= r.json()["total"]
                #bundle_to_file(r.json(),)
                return r # just the first for now
    else:
        return None

def get_enc(my_query):
    '''
    from dict bundle extract the first entry and return as fhir object
    '''
    b = B.Bundle(my_query.json())
    e = b.entry[0].resource
    app.logger.info(f'e.as_json()={e.as_json()}')
    return e

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

@app.route('/', methods=["POST", "GET"])
def hello_world():
    my_response = my_request = ''
    posts = db.session.query(Post).all()
    try:
        last_enc_url = [i.event_ids for i in posts][-1]
        last_enc_id = last_enc_url.split('/')[-1]
    except IndexError:  #empty
        pass
    if request.method == 'POST':
        session.pop('post', None)
        post_type = next(iter(request.form))
        app.logger.info(post_type)
        session['post'] = post_type 
        if post_type == 'post_enc':
            try:
                #my_query = search('Encounter', params = [('_id',last_enc_id)])
                my_query = search('Encounter',
                                     params=[('_id',last_enc_id),
                                     ('_include','Encounter:practitioner'),
                                     ('_include','Encounter:location'),
                                     ('_include','Encounter:patient'),
                                     ('_include','Encounter:service-provider')],
                                      )
            except UnboundLocalError:
                 session['post_error'] = "wait for Subscription notification"

            else:
                session.pop('post_error', None)
                session['encounter_id']=my_query.json()['entry'][0]['resource']['id']
                session['patient_id']=my_query.json()['entry'][0]['resource']['subject']['reference']
                my_request = my_query.url
                app.logger.info(f'my_request = {my_query.url}')
                my_response = dumps(my_query.json(),indent=2)
               
            # my_query = search('Encounter', _id=last_enc_id, _include='Encounter:practitioner',_include='Encounter:location')
            #patient_id
            pass
        elif post_type == 'post_cond':
            try:
                my_query = search('Condition',
                params =[('patient',session['patient_id']), 
                ('encounter',session['encounter_id']) ],
                )
            except KeyError:
                 session['post_error'] = "wait for Step 1"
            else:
                session.pop('post_error', None)
                my_request = my_query.url
                my_response = dumps(my_query.json(),indent=2)
                session.pop('encounter_id', None)
        else: # post_cov
            try:
                my_query = search('Coverage',
                params =[('patient',session['patient_id']),
                 ],
                )
            except KeyError:
                 session['post_error'] = "wait for Step 1"
            else:
                session.pop('post_error', None)
                my_request = my_query.url
                my_response = dumps(my_query.json(),indent=2)
                session.pop('patient_id', None)
    else:
        session['method'] = request.method
        session.clear()



    return render_template('index.html',
                             posts=posts,
                             my_response = my_response,
                             my_request = my_request,
                             )
if __name__ == '__main__':
    app.run(debug=True)
