from celery import Celery
from time import sleep
import requests
import json
import datetime

app = Celery("openaq_stream")
app.conf.task_routes = {
    'openaq_stream.*': {'queue': 'openaq_stream_queue'},
    'db_message_broker.*': {'queue': 'db_message_broker_queue'},
    'http_interface.*': {'queue': 'http_queue'},
}

@app.task
def poll_api(interval):
    current_time = datetime.datetime.now()
    past_time = current_time - datetime.timedelta(hours=2)
    base_url = 'https://api.openaq.org/v1/'
    cities_request_params = params = {'country':'US', 'limit':25}
    cities_response = requests.get(f'{base_url}cities',params=cities_request_params)
    cities = [result['name'] for result in json.loads(cities_response.text)['results']]
    print(f"cities:{cities}")
    for city in cities:
        measurement_request_params = {'country':'US',
                                      'city': city,
                                      'date_from': past_time,
                                      'date_to': current_time}
        city_measurements = json.loads(requests.get(f'{base_url}measurements', params=measurement_request_params).text)
        print(f"cms:{city_measurements}")
        for measurement in city_measurements['results']:
            print(f"m:{measurement}")
            send_record_to_db(source='openaq',
                              timestamp=measurement['date']['utc'],
                              record=json.dumps(transform_record(measurement)))

def transform_record(record):
    return {'city': record['city'],
            'location': record['location'],
            'country': record['country'],
            'parameter': record['parameter'],
            'date': record['date']['utc'],
            'value': record['value'],
            'unit': record['unit'],
            'latitude': record['coordinates']['latitude'],
            'longitude': record['coordinates']['longitude']
            }
    
def send_record_to_db(source, timestamp, record):
    app.send_task('db_message_broker.receive_data_record', kwargs={'source': source,
                                                                   'timestamp': timestamp,
                                                                   'record': record
								  })

