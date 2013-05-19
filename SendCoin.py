import sqlite3
from time import sleep
from CryptoTap import DripValidate
from CryptoTap import DripRequest

# Globals
DATABASE_FILE = '/root/trc.db'
DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001

def send_coins():
	"""Sends queued coins."""
	# Connect to Database
	conn = sqlite3.connect(DATABASE_FILE)
	c = conn.cursor()

	# Do Query
	query = "SELECT * FROM drip_request WHERE trans_id='UNSENT' LIMIT 1"
	c.execute(query.format("UNSENT"))

	row = c.fetchone()
	print(row)
	# DripRequest(row[3], row[4], row[2], row[0])


# Infinite Loop...
while True:
	print("Checking for drips...")
	send_coins()
	print("Sleeping for 10 seconds...")
	sleep(1)