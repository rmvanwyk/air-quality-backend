from celery import Celery
from time import sleep
import requests
import json


app = Celery("openaq_stream")
app.conf.task_routes = {
    'openaq_stream.*': {'queue': 'openaq_stream_queue'},
    'db_message_broker.*': {'queue': 'db_message_broker_queue'},
    'http_interface.*': {'queue': 'http_queue'},
}

@app.task
def poll_api(interval):
    source = 'test'
    timestamp = 'now'
    record = {'data':'empty'}
    base_url = 'https://api.openaq.org/v1/'
    cities_response = requests.get(f'{base_url}cities', params={'country':'US', 'limit':10000})
    cities = [result['name'] for result in json.loads(cities_response.text)['results']]
    measurements_responses = [requests.get(f'{base_url}measurements', params={'country':'US', 'city': city})
    		          for city in cities[:25]]
    measurements = [json.loads(city_measurement.text) for city_measurement in measurements_responses]
    if measurements:
        send_record_to_db(source, measurements[-1]['results'], record)
    else:
        send_record_to_db(source, 'no response', record)

def send_record_to_db(source, timestamp, record):
    app.send_task('db_message_broker.receive_data_record', kwargs={'source': source,
                                                                   'timestamp': timestamp,
                                                                   'record': record
								  })
