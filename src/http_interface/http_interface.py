from celery import Celery
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, redirect, request, flash
from flask_restplus import Api, Resource, fields
import requests
import os
import json
import pprint


class LoggingMiddleware(object):
    def __init__(self, app):
        self._app = app

    def __call__(self, environ, resp):
        errorlog = environ['wsgi.errors']
        pprint.pprint(('REQUEST', environ), stream=errorlog)

        def log_response(status, headers, *args):
            pprint.pprint(('RESPONSE', status, headers), stream=errorlog)
            return resp(status, headers, *args)

        return self._app(environ, log_response)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'
app.wsgi_app = LoggingMiddleware(app.wsgi_app)

api = Api(app, version=3)
socketio = SocketIO(app)

celery = Celery('http_interface')
celery.conf.task_routes = {
    'http_interface.*': {'queue': 'http_queue'},
    'openaq_stream.*': {'queue': 'openaq_stream_queue'},
    'db_message_broker.*': {'queue': 'db_message_broker_queue'},
}

name_space = api.namespace('streams', description="APIs to control data streams")


@app.route("/events", methods=['GET', 'POST'])
def show_events():
    if request.method == "GET":
        celery.send_task('openaq_stream.poll_api', kwargs={'interval': 5})
        return render_template('index.html')
    else:
        return redirect(url_for("show_events"))


@app.route("/new-event", methods=['POST'])
def new_event():
    if request.method == "POST":
        socketio.emit('location', json.dumps(request.json), namespace='/test')
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    return json.dumps({'success':False}), 404, {'ContentType':'application/json'}


@celery.task()
def show_user_event_location(record):
    url = 'http://http-interface:5000/new-event'
    requests.post(url, json={"record": record})


@socketio.on('connect', namespace='/test')
def test_connect():
    print('Client connected')


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, port=5000, host='0.0.0.0', debug=True)
