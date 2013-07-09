import random
import sqlite3
import commands
from time import sleep
from flask import Flask
from Coupon import Coupon
from CryptoTap import DripRequest


# Load Settings  ---------------------------------------------------------------
app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
		

# SendCoin Class ---------------------------------------------------------------
class SendCoin:
	def __init__(self, refresh_time):
		self.refresh_time = int(refresh_time)

	def get_balance(self):
		"Retrieves the current balance."
		com = '{0} getbalance'.format(app.config['COIN_CLIENT'])
		return float(commands.getstatusoutput(com)[1])


	def com_send(self, drip_id, address, coupon, amount, conn):
		"""
		Send the specified amount to the address Uses the following unix
		command to do so:
			sendtoaddress <terracoinaddress> <amount> [comment] [comment-to]
		The comment arguments are optional, and not currently used. 

		"""

		# Check coupon amount
		coupon_val = float(Coupon(conn).use(coupon))
		print(coupon_val)
		if coupon_val > 0: amount = coupon_val
		else: amount = float(app.config['DEFAULT_SEND_VAL'])
		print(amount)

		# Hardcoded limit at 0.1 TRC in case the coupon system breaks
		if amount > app.config['HARD_LIMIT']: amount = app.config['HARD_LIMIT']
		
		# Make sure balance is not empty before sending
		if (get_balance() - amount) > app.config['LOW_BAL_LIMIT']:
			# Construct Command
			command = "{0} sendtoaddress {1} {2}"
			command = command.format(app.config['COIN_CLIENT'], address, amount)
			trans_id = commands.getstatusoutput(command)[1]
			print(command)

			# Update
			c = conn.cursor()
			query = "update drip_request set trans_id=? where id=?"
			c.execute(query, (trans_id, drip_id,))
			conn.commit()

			# Console Message
			coin_name = app.config['COIN_NAME']
			con_message = "Sent {0} {1} to {2}. Traction ID: {3}"
			return con_message.format(amount, coin_name, address, trans_id)
		else:
			return "Insufficient Funds!"


	def send_coins(self):
		"""Sends queued coins."""
		# Connect to Database
		conn = sqlite3.connect(app.config['DATABASE_FILE'])
		c = conn.cursor()

		# Do Query
		query = "select * from drip_request where trans_id=? limit 1"
		c.execute(query, ("UNSENT",))

		row = c.fetchone()
		if row == None:
			return "No drips found..."
		else:
			try:
				drip = DripRequest(row[3], row[4], row[2], row[0])
				return self.com_send( drip.drip_id, drip.address, drip.coupon,
							 app.config['DEFAULT_SEND_VAL'], conn)
			except ValueError as detail: 
				return "Something Broke: " + str(detail) 
			#except:	return "Script Fail..."

		# Close Database
		conn.close()

	def run(self):
		try: 
			print("SendCoin 'Daemon' Active. Press CTRL+C to exit.")
			while True:
				print(self.send_coins())
				sleep(self.refresh_time)
		except KeyboardInterrupt:
			print("Closing...")



# Infinite Loop ----------------------------------------------------------------
if __name__ == '__main__':
	cheap_daemon = SendCoin(int(app.config['CHECK_SEND_SEC']))
	cheap_daemon.run()