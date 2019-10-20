from celery import Celery
from time import sleep
import requests
import json
import datetime

app = Celery("openaq_stream")
app.conf.task_routes = {
    'openaq_stream.*': {'queue': 'openaq_stream_queue'},
    'ambee_stream.*': {'queue': 'ambee_stream_queue'},
    'db_message_broker.*': {'queue': 'db_message_broker_queue'},
    'http_interface.*': {'queue': 'http_queue'},
}

@app.task
def poll_api(interval):
    current_time = datetime.datetime.now()
    past_time = current_time - datetime.timedelta(hours=2)
    base_url = 'https://api.ambeedata.com/'
    cities_request_params = params = {'city':'CA', 'limit':100}
    cities_response = requests.get(f'{base_url}latest/by-city',params=cities_request_params)
    cities = [result['name'] for result in json.loads(cities_response.text)['results']]
    for city in cities:
        measurement_request_params = {'country':'US',
                                      'city': city,
                                      'date_from': past_time,
                                      'date_to': current_time}
        city_measurements = json.loads(requests.get(f'{base_url}measurements', params=measurement_request_params).text)
        for measurement in city_measurements['results']:
            send_record_to_db(source='openaq',
                              timestamp=measurement['date']['utc'],
                              record=json.dumps(transform_record(measurement)))

def transform_record(record):
    
    record = {'city': record['placeName'],
              'location': record['division'],
              'country': record['countryCode'],
              'date': record['updatedAt'],
              'unit': None,
              'latitude': record['lat'],
              'longitude': record['lng']
            }
    parameters = ["NO2", "PM10", "PM25", "CO", "SO2", "OZONE", "NOX", "AQI"]
    for param in parameters:
       record[
    
def send_record_to_db(source, timestamp, record):
    app.send_task('db_message_broker.receive_data_record', kwargs={'source': source,
                                                                   'timestamp': timestamp,
                                                                   'record': record
								  })

