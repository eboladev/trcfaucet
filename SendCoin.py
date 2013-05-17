import os
import re
import string
import sqlite3
import hashlib
import commands
from random import randrange
from datetime import datetime
from datetime import timedelta

from flask import g
from flask import abort
from flask import Flask
from flask import url_for
from flask import request
from flask import redirect
from flask import render_template
from contextlib import closing


# Global Configs
DATABASE = '/root/trc.db'
DEBUG = True
SECRET_KEY = '31491de80d74f54da681c40cc4d08c41a35939ac'
USERNAME = 'trcadmin'
PASSWORD = 'trcs3cur3'

DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001
COIN_NAME = "TRC"
COIN_CLIENT = "terracoind"
REQUEST_LIMIT = 3


# Load Flask
app = Flask(__name__)
app.config.from_object(__name__)

# Database Functions
def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception): 
	if hasattr(g, 'db'):
		g.db.close()

def send_coins():
	"""Sends queued coins."""
	recent_drips = g.db.execute('SELECT * FROM drip_request ORDER BY id DESC LIMIT 5')
	recent_drips = recent_drips.fetchall()

	if len(recent_drips) >= 0: print("No Drips Found.")
	else: print("Found {0} Drips".format(len(unsent)))

	for row in recent_drips:
		drip = DripRequest(row[3], row[4], row[2], row[0])
		print(drip.send(DEFAULT_SEND_VAL))

# Infinite Loop...
while True:
	print("Checking for drips...")
	send_coins()
	print("Sleeping for 10 seconds...")
	sleep(10)