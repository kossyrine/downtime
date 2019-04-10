#!/usr/bin/python3.6

from flask import Flask
from flask_socketio import SocketIO
# from datetime import datetime

import time
import sqlite3
import json

flask_app = Flask(__name__)
app = SocketIO(flask_app)

def now():
    return int(time.time())

@flask_app.route('/')
def index():
    return flask_app.send_static_file('client.html')

@flask_app.route('/db')
def dbdump():
    return flask_app.send_static_file('timestamps.db')

@flask_app.route('/wipe')
def wipe():
    connection = sqlite3.connect('timestamps.db')
    cursor = connection.cursor()
    cursor.execute(f'delete from downtime;')
    connection.commit()
    connection.close()
    return '200'

@flask_app.route('/24hours')
def dump():
    shift = now() - 24 * 60 * 60

    connection = sqlite3.connect('timestamps.db')
    cursor = connection.cursor()
    ##cursor.execute(f'select rowid, * from downtime where event_start > {shift};')
    cursor.execute(f'select rowid, * from downtime;')
    resp = cursor.fetchall()
    connection.close()
    
    return json.dumps(resp)

@flask_app.route('/signal/<string:line_code>/<string:signal_type>')
def signal(line_code, signal_type):
    ##timestamp = int(datetime.utcnow().timestamp())
    timestamp = now()

    connection = sqlite3.connect('timestamps.db')
    cursor = connection.cursor()
    
    cursor.execute(f'select rowid, * from downtime where line_code = "{line_code}" and signal_type = "{signal_type}" order by rowid desc limit 1;')
    resp = cursor.fetchone()

    if resp == None or resp[4] != 0:
        cursor.execute(f'insert into downtime values("{line_code}", "{signal_type}", {timestamp}, 0, "-");')
        cursor.execute(f'select rowid, * from downtime where line_code = "{line_code}" and signal_type = "{signal_type}" order by rowid desc limit 1;')
        resp = cursor.fetchone()
    else:
        cursor.execute(f'update downtime set event_stop = {timestamp} where rowid = {resp[0]};')
        cursor.execute(f'select rowid, * from downtime where line_code = "{line_code}" and signal_type = "{signal_type}" and rowid = {resp[0]};')
        resp = cursor.fetchone()

    connection.commit()
    connection.close()

    app.send(json.dumps(resp))

    return '200'

@flask_app.route('/delete/<string:rowid>')
def delete(rowid):
    connection = sqlite3.connect('timestamps.db')
    cursor = connection.cursor()
    cursor.execute(f'delete from downtime where rowid = {rowid};')
    connection.commit()
    connection.close()
    
    app.send(f'delete {rowid}')
    
    return '200'

@flask_app.route('/update/<string:rowid>/<string:comment>')
def update(rowid, comment):
    connection = sqlite3.connect('timestamps.db')
    cursor = connection.cursor()
    cursor.execute(f'update downtime set event_comment = "{comment}" where rowid = {rowid};')
    cursor.execute(f'select rowid, * from downtime where rowid = {rowid};')
    resp = cursor.fetchone()
    connection.commit()
    connection.close()

    app.send(json.dumps(resp))

    return '200'

connection = sqlite3.connect('timestamps.db')
cursor = connection.cursor()
cursor.execute('create table if not exists downtime(line_code text, signal_type text, event_start integer, event_stop integer, event_comment text);')
connection.commit()
connection.close()

if __name__ == "__main__":
    app.run(flask_app, host = "0.0.0.0", port = "8010")
