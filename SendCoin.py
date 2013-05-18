from time import sleep
from CryptoTap import DripValidate
from CryptoTap import DripRequest

# Globals
DATABASE_FILE = '/root/trc.db'
DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001

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