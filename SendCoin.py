from time import sleep
from DripRequest import *

# Globals
DATABASE_FILE = '/root/trc.db'
DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001

def send_coins():
	"""Sends queued coins."""
	data = Database(DATABASE_FILE, DATABASE_TABLE)
	unsent = data.get_unsent(5)

	if len(unsent) >= 0: print("No Drips Found.")
	else: print("Found {0} Drips".format(len(unsent)))

	for i in unsent:
		drip = DripRequest(i[3], i[4], i[2], i[0])
		print(drip.send(DEFAULT_SEND_VAL, data))

# Infinite Loop...
while True:
	print("Checking for drips...")
	send_coins()
	print("Sleeping for 10 seconds...")
	sleep(10)