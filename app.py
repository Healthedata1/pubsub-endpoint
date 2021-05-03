# A very simple Flask app to get started with using 
# FHIR Subscriptions
# This is a reciever for the FHIR R4 Server URL (https://subscriptions.argo.run/)
# with an ednpoint = "http://healthedatainc2.pythonanywhere.com/webhook"
# It just saves the subscription notification data to a flat csv file "data.csv"
#  to initialize the data.csv:
#
# data = dict(
#     timestamp = [], #Bundle['timestamp']
#     type = [], # Bundle['entry'][0]['resource']['parameter'][5]['valueCode']
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
level=logging.DEBUG,
format='[%(asctime)s] %(levelname)s in %(module)s %(lineno)d}: %(message)s')

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = 'my_secret_key'

file_name = 'data.csv'

#see add_url_rule to conditionally open rest hook.= e.g after subscribing"

@app.route('/webhook', methods=['POST'])
def respond():
    # webhook logic to do something
    app.logger.info(request.json)
    try:
        bundle_ts = request.json['timestamp']
        sub_params = request.json['entry'][0]['resource']['parameter']
        bundle_type = sub_params[5]['valueCode']
        bundle_status = sub_params[4]['valueCode']
        bundle_topic = sub_params[1]['valueUri']
        bundle_event_id = request.json['entry'][1]['fullUrl']
    except Exception as e: # work on python 3.x
        app.logger.exception(e)
        return Response(status=400)
    else:
        df = pd.read_csv(file_name, index_col = 0) 
        my_row = pd.Series(
        data = [bundle_ts,bundle_type,bundle_status,bundle_topic,bundle_event_id,],
        index=df.columns,
        )
        app.logger.info(f'{df.shape[0]} rows')       
        df = df.append(my_row, ignore_index=True)
        df.to_csv(file_name)
        app.logger.info(f'saving {file_name} as csv ...')
        return Response(status=200)

@app.route('/')
def html_table():
    df = pd.read_csv(file_name, index_col = 0)
    return render_template('index.html',
     tables=[df.to_html(classes='data')],
      titles = df.columns.values,)

if __name__ == '__main__':
    app.run(debug=True)
