# A very simple Flask app to get started with using
# FHIR Subscriptions
# This is a reciever for the FHIR R4 Server URL (https://subscriptions.argo.run/)
# with an ednpoint = "http://healthedatainc2.pythonanywhere.com/webhook"
# It just saves the subscription notification data to a flat csv file "data.csv"
#  to initialize the data.csv:
#
# data = dict(
#     timestamp = [], #Bundle['timestamp']
#     foo = [], # Bundle['entry'][0]['resource']['parameter'][5]['valueCode']
#     status = [], # Bundle['entry'][0]['resource']['parameter'][4]['valueCode']
#     topic = [], # Bundle['entry'][0]['resource']['parameter'][1]['valueUri']
#     event_id = [], # Bundle['entry'][0]['fullUri']
#     )
# df = pd.DataFrame(data=data)
# df
#
# file_name = 'data.csv'
# df.to_csv(file_name)
# print(f'saving {file_name} as csv ...')

# my_csv = pd.read_csv(file_name, index_col = 0)
# my_csv#
#
# and display subscription notifications data
# the csv file "data.csv" is consantly appended and not created each time

from flask import Flask, request, Response, render_template, session
import os
import logging
from datetime import datetime
from json import dumps, loads
import pandas as pd

logging.basicConfig(
filename='demo.log',
level=logging.DEBUG,
format='[%(asctime)s] %(levelname)s in %(module)s %(lineno)d}: %(message)s')

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 'my_secret_key'

file_name = 'data.csv'

empty_table = dict(
     timestamp = [], #Bundle['timestamp']
     type = [], # Bundle['entry'][0]['resource']['parameter'][5]['valueCode']
     status = [], # Bundle['entry'][0]['resource']['parameter'][4]['valueCode']
     topic = [], # Bundle['entry'][0]['resource']['parameter'][1]['valueUri']
     event_id = [], # Bundle['entry'][0]['fullUri']
     )

#see add_url_rule to conditionally open rest hook.= e.g after subscribing"

@app.route('/webhook', methods=['POST'])
def respond():
    # webhook logic to do something
    app.logger.info(request.headers)
    app.logger.info(request.json)
    try: # sometimes is empty
        bundle_event_id = request.json['entry'][1]['fullUrl']
    except IndexError: # if no entry that is OK
        #app.logger.exception(e)
        bundle_event_id = None
    except KeyError: # if no fullUrl that is no good
        #app.logger.exception(e)
        return Response(status=400)
    try: # if these are empty then fail
        bundle_ts = request.json['timestamp']
        params = request.json['entry'][0]['resource']['parameter']
        bundle_type = [param['valueCode'] for param in params if param['name']=='type'][0]
        bundle_status = [param['valueCode'] for param in params if param['name']=='status'][0]
        bundle_topic = [param['valueUri'] for param in params if param['name']=='topic'][0]
    except Exception as e: # work on python 3.x
        #app.logger.exception(e)
        return Response(status=400)
    else:
        df = pd.read_csv(file_name, index_col = 0)
        my_row = pd.Series(
        data = [bundle_ts,bundle_type,bundle_status,bundle_topic,bundle_event_id,],
        index=df.columns,
        )
        #app.logger.info(f'{df.shape[0]} rows')
        df = df.append(my_row, ignore_index=True)
        df.to_csv(file_name)
        #app.logger.info(f'saving {file_name} as csv ...')
        return Response(status=200)

@app.route('/',methods = ['POST', 'GET'])
def html_table():
    #app.logger.info(f"request.method = {request.method}")
    if "clear_button" in request.form:
        #app.logger.info("clear table")
        df = pd.DataFrame(data=empty_table)
        df.to_csv(file_name)
    df = pd.read_csv(file_name, index_col = 0, keep_default_na=False )
    #app.logger.info("update table")
    return render_template('index.html',
     tables=[df.to_html(classes='data')],
      titles = df.columns.values,)

if __name__ == '__main__':
    app.run(debug=True)
