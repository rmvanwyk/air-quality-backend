import os
from celery import Celery
import json
from dataclasses import dataclass
import pyrebase

app = Celery('db_message_broker')
app.conf.task_routes = {
    'openaq_stream.*': {'queue': 'openaq_stream_queue'},
    'db_message_broker.*': {'queue': 'db_message_broker_queue'},
    'http_interface.*': {'queue': 'http_queue'},
}

firebase_config = {
  "apiKey": "AIzaSyB6ptd42FvP3YwI3P03PY4UCJkqgrCvY_I",
  "authDomain": "nasa-71ee6.firebaseapp.com",
  "databaseURL": "https://nasa-71ee6.firebaseio.com",
  "storageBucket": "nasa-71ee6s.appspot.com",
  "serviceAccount": "nasa-71ee6-firebase-adminsdk-q8mam-36cdfa3b66.json",
}

'''
	initialize app with config
'''
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

@dataclass
class Measurement:
    city: str
    location: str
    country: str
    parameter: str
    date: str
    value: float
    unit: str
    latitude: float
    longitude: float

    #measurement = Measurement(city=record['city'],
    #                     location=record['location'],
    #                     country=record['country'],
    #                     parameter=record['parameter'],
    #                     date=record['date'],
    #                     value=record['value'],
    #                     unit=record['unit'],
    #                     latitude=record['latitude'],
    #                     longitude=record['longitude']
    #                    )

@app.task
def receive_data_record(source, timestamp, record ):
    record = json.loads(record)
    #db.child('openaq'
    #        ).child('cities'
    #               ).child(record['city']
    #                      ).child('parameters'
    #                             ).child(record['parameter']
    #                                    ).push(record)
    app.send_task('http_interface.show_user_event_location', kwargs={'record': record})
