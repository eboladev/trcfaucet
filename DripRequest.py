#!/usr/bin/env python
# Filename: DripRequest.py
# Author: Shawn Wilkinson <me@super3.org>
# Author Website: http://super3.org/
# Github: http://github.com/super3/
# License: GPLv3 <http://gplv3.fsf.org/>

import os
import re
import string
import sqlite3
import commands


# Hard Coded Coupons
def lookup_coupon(coupon):
	if coupon == "MOREMONEY": return 1.5
	elif coupon == "DOUBLEMONEY": return 2
	return 1 


class Database:
	def __init__(self, datebase_path, database_table):
		"""
		Initializes database vars, and installs database if the database file
		is not found.

		Arguments:
		datebase_path  -- Path to the sqlite3 databse file.
		database_table -- Name of the sql table. 

		Data Members:
		sql_database   -- Path to the sqlite3 databse file.
		sql_table      -- Name of the sql table. 

		"""
		self.sql_database = datebase_path
		self.sql_table = database_table
		if not os.path.exists(datebase_path):
			self.install()

	# SQL Methods
	def install(self):
		"""Installs the database, and inserts the first item."""
		# Create Database
		text = "CREATE TABLE {0}(id INTEGER NOT NULL,crdate TEXT(25),"
		text = text.format(self.sql_table)
		text += "ip TEXT(25), address TEXT(50),"
		text += "coupon TEXT(25),trans_id TEXT(25),PRIMARY KEY (id))"
		self.command(text)
		# Insert First Row
		ti = "bf9433692129d60f10f47d391c5b8435fc3852d0cd7c1f19db62403c5df89b3f"
		self.insert("Faucet Start", "69.87.160.3",
				    "1DarXYYGgvyHFQKZKsgUq676A9CK7D7FYa", "DOUBLEMONEY", ti)

	def command(self, text):
		"""Executes a single SQL command."""
		con = sqlite3.connect(self.sql_database)
		con.execute(text)
		con.commit()

	def query(self, text):
		"""Executes a single SQL query."""
		conn = sqlite3.connect(self.sql_database)
		c = conn.cursor()
		c.execute(text)
		return c.fetchall()

	# Drip Methods
	def count_address(self, address):
		text = "SELECT * FROM {0} WHERE address = '{1}'"
		return len(self.query(text.format(self.sql_table, address)))

	def count_ip(self, ip):
		text = "SELECT * FROM {0} WHERE ip = '{1}'"
		return len(self.query(text.format(self.sql_table, ip)))

	def update_drip(self, drip_id, trans_id):
		text = "UPDATE {0} SET trans_id = '{1}' WHERE id = '{2}'"
		self.command(text.format(self.sql_table, trans_id, drip_id))

	def get_html(self, save_time, ip, trans_id):
		html = "<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>"
		return html.format(save_time, ip, trans_id)

	def insert(self, crdate, ip, address, coupon, trans_id):
		text = "INSERT INTO {0} (id, crdate, ip, address, coupon, trans_id)"
		text = text.format(self.sql_table)
		text += "VALUES (NULL,'{0}','{1}','{2}','{3}','{4}')"
		self.command(text.format(crdate, ip, address, coupon, trans_id))

	# Get Methods
	def get_recent(self, limit = 10):
		text = "SELECT * FROM {0} ORDER BY id DESC LIMIT {1}"
		return self.query(text.format(self.sql_table, limit))

	def get_unsent(self, limit = 10):
		text = "SELECT * FROM {0} WHERE trans_id = '{1}'"
		return self.query(text.format(self.sql_table, "UNSENT"))


class DripValidate:
	def __init__(self):
		"""Used to validate input before database use."""
		pass

	def clean(self, in_str):
		"""Strips out string that is not alphanumeric. Should stop injects."""
		pattern = re.compile('[\W_]+')
		return pattern.sub('', in_str)

	def validate_address(self, address):
		# Source: http://bit.ly/17OhFP5
		"""
		Does simple validation of a bitcoin address. 

		param : address : an ASCII or unicode string, of a bitcoin address.
		returns : boolean, indicating that the address has a correct format.

		"""
		
		address = self.clean(address)
		# The first character indicates the "version" of the address.
		CHARS_OK_FIRST = "123"
		# alphanumeric characters without : l I O 0
		CHARS_OK = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
		
		# We do not check the high length limit of the adress. 
		# Usually, it is 35, but nobody knows what could happen in the future.
		if len(address) < 27:
			return False
		elif address[0] not in CHARS_OK_FIRST:
			return False

		# We use the function "all" by passing it an enumerator as parameter. 
		# It does a little optimisation : 
		# if one of the character is not valid, the next ones are not tested.
		return all( ( char in CHARS_OK for char in address[1:] ) )
	
	def validate_coupon(self, coupon):
		"""Makes sure the coupon is alphanumeric and less than 12 chars."""
		coupon = self.clean(coupon)
		cond1 = re.match('^[\w]+$', coupon) and len(coupon)<12
		cond2 = (lookup_coupon(coupon) != 1)
		return (cond1 and cond2)

	def validate_ip(self, ip):
		"""Checks if it is a valid IP address."""
		return re.match('([0-9]{1,3}\.){3}[0-9]+',ip)	


class DripRequest:
	"""
	Stores a users terracoin send request. 

	Data Members:
	date    -- The timestamp of when the request was created.
	address -- Terracoin address to send the transaction to.
	coupon  -- Special code that allows users to get additional coins.
	ip      -- The IP address that the request was made from.
	drip_id -- The database id of the drip request.
	
	"""
	def __init__(self, date, address, coupon, ip, drip_id = 0):
		vall = DripValidate()
		if not vall.validate_address(str(address)): 
			raise ValueError("Invalid Terracoin Address.")
		elif not vall.validate_coupon(str(coupon)): coupon = "INVALID"
		elif not vall.validate_ip(str(ip)): raise ValueError("Invalid IP.")

		self.date = date
		self.address = str(address)
		self.coupon = str(coupon).upper()
		self.ip = str(ip)
		self.drip_id = drip_id

	def __str__(self):
		text = '{0} {1} {2} {3} {4}'
		return text.format(self.date, self.address, self.coupon, self.ip,
						   self.drip_id)

	def save(self):
		"""Insert drip request into databse."""
		data = Database('test.db', 'drip_request')
		num_ip = data.count_ip(self.ip)
		num_address = data.count_address(self.address)
		print("IP: {0} and Address: {1}".format(str(num_ip), str(num_address)))
		if num_ip <= 3 and num_address <= 3:
			data.insert(self.date, self.ip, self.address, self.coupon,
					    "UNSENT")
		else:
			raise LookupError

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
		command = './terracoind sendtoaddress {0} {1}'
		command = command.format(self.address, str(amount))
		trans_id = commands.getstatusoutput(command)[1]
		
		# Send Payment
		data = Database('test.db', 'drip_request')
		data.update_drip(self.drip_id, trans_id)

		# Console Message
		con_message = "Sent {0} TRC to {1}. Traction ID: {2}"
		print(con_message.format(str(amount), self.address, trans_id))


# Unit Tests
def validate_unit_test():
	# Validate Object
	drip = DripValidate()

	# Sample Addresses
	assert(drip.validate_address("1aueAUEZMN9875bjnsYXYX52366ZMWJJ"))
	assert(not drip.validate_address("1aueAUEZMN9875bjnsYXYX52366ZMWJJO"))
	assert(drip.validate_address("3aueAUEZMN9875bjnsYXYX52366ZMWJJio1L"))
	assert(not drip.validate_address(""))
	assert(not drip.validate_address("1"))
	assert(not drip.validate_address("4aueAUEZMN9875bjnsYXYX52366ZMWJJ"))

	# Sample Coupons
	assert(drip.validate_coupon("DOUBLEMONEY"))
	assert(drip.validate_coupon("MOREMONEY"))
	assert(not drip.validate_coupon("NOTCOUPON"))
	assert(not drip.validate_coupon("WAYTOOLONGCOUPON"))
	assert(not drip.validate_coupon("<?echo 'H';?>"))
	assert(not drip.validate_coupon("<div><div>"))
	assert(not drip.validate_coupon("</div></div>"))

	# Sample IPs
	assert(not drip.validate_ip("notiplol"))
	assert(drip.validate_ip("69.87.160.3"))

def drip_unit_test():
	# Insert Two Drip Objects
	drip = DripRequest('today', '1DarXYYGgvyHFQKZKsgUq676A9CK7D7FYa',
					   'DOUBLEMONEY', '69.87.160.3')
	drip.save()
	drip2 = DripRequest('today', '1DarXYYGgvyHFQKZKsgUq676A9CK7D7FYa',
						'', '171.247.220.64')
	drip2.save()

def get_html_recent():
	data = Database('test.db', 'drip_request')
	return data.get_recent()

# Main
if __name__ == "__main__":
	validate_unit_test()
	drip_unit_test()