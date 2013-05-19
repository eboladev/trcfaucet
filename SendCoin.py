import sqlite3
from time import sleep
from CryptoTap import DripValidate
from CryptoTap import DripRequest


# Globals ----------------------------------------------------------------------
DATABASE_FILE = '/root/trc.db'
DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001


# Functions --------------------------------------------------------------------
def send(self, amount):
		"""
		Send the specified amount to the drip request, time whatever the
		coupon code specifies. Uses the following unix command to do so:
			sendtoaddress <terracoinaddress> <amount> [comment] [comment-to]
		The comment arguments are optional, and not currently used. 

		"""
		# Make Shell Command
		amount *= lookup_coupon(self.coupon)
		 # hardcoded limit at 0.1 TRC in case the coupon system breaks
		if amount > 0.1: amount = 0.1
		
		if (self.get_balance() - amount) > 0.001:
			# Construct Command
			command = '{0} sendtoaddress {1} {2}'
			command = command.format(COIN_CLIENT, self.address, str(amount))
			trans_id = commands.getstatusoutput(command)[1]
		 
			# Send Payment
			query = "update drip_request set trans_id = '{0}' where id = {1}"
			g.db.execute(query.format(trans_id, self.drip_id))
			g.db.commit()

			# Console Message
			con_message = "Sent {0} {1} to {2}. Traction ID: {3}"
			return con_message.format(amount, COIN_NAME, self.address, trans_id)
		else:
			return "Insufficient Funds!"
			
def send_coins():
	"""Sends queued coins."""
	# Connect to Database
	conn = sqlite3.connect(DATABASE_FILE)
	c = conn.cursor()

	# Do Query
	query = "SELECT * FROM drip_request WHERE trans_id='UNSENT' LIMIT 1"
	c.execute(query.format("UNSENT"))

	row = c.fetchone()
	if row == None:
		return "No drips found..."
	else:
		try:
			drip = DripRequest(row[3], row[4], row[2], row[0])
			return "Done"
		except ValueError: return "Something Broke(ValueError)..." 
		except:	return "Something Broke(SomeError)..."


# Infinite Loop ----------------------------------------------------------------
while True:
	print("Checking for drips...")
	print(send_coins())
	print("Sleeping for 10 seconds...")
	sleep(1)