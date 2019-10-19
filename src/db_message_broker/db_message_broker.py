import os
from celery import Celery
import json

app = Celery('db_message_broker')
app.conf.task_routes = {
    'openaq_stream.*': {'queue': 'openaq_stream_queue'},
    'db_message_broker.*': {'queue': 'db_message_broker_queue'},
    'http_interface.*': {'queue': 'http_queue'},
}


@app.task
def receive_data_record(source, timestamp, record ):
    app.send_task('http_interface.show_user_event_location', kwargs={'location': timestamp})
