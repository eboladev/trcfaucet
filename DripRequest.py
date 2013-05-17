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

from flask import g

COIN_NAME = "TRC"
COIN_CLIENT = "terracoind"
REQUEST_LIMIT = 3


# Hard Coded Coupons
def lookup_coupon(coupon):
	if coupon == "MOREMONEY": return 1.5
	elif coupon == "DOUBLEMONEY": return 2
	return 1 


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
	address -- Terracoin address to send the transaction to.
	coupon  -- Special code that allows users to get additional coins.
	ip      -- The IP address that the request was made from.
	drip_id -- The database id of the drip request.
	
	"""
	def __init__(self, address, coupon, ip, drip_id = 0):
		vall = DripValidate()
		if not vall.validate_address(str(address)): 
			raise ValueError("Invalid Terracoin Address.")
		elif not vall.validate_coupon(str(coupon)): coupon = "INVALID"
		elif not vall.validate_ip(str(ip)): raise ValueError("Invalid IP.")

		self.address = str(address)
		self.coupon = str(coupon).upper()
		self.ip = str(ip)
		self.drip_id = drip_id

	def __str__(self):
		text = '{0} {1} {2} {3} {4}'
		return text.format(self.address, self.coupon, self.ip, self.drip_id)

	def count_unique(self, row, val):
		query = "SELECT Count(*) FROM drip_request WHERE {0} = '{1}'"
		cur = g.db.execute(query.format(row, val))
		return int(cur.fetchone()[0])

	def save(self):
		"""Insert drip request into database."""
		num_ip = self.count_unique("ip", self.ip)
		num_address = self.count_unique("address", self.address)
		request_str = "IP: {0}/{1} and Address: {2}/{3}"
		print(request_str.format(num_ip, REQUEST_LIMIT, num_address, REQUEST_LIMIT))
		if num_ip < REQUEST_LIMIT and num_address < REQUEST_LIMIT:
			g.db.execute('insert into entries (ip, address, coupon, trans_id) values (?, ?, ?, ?)',
			[self.ip, self.address, self.coupon, "UNSENT"])
			g.db.commit()

		else:
			raise LookupError

	def get_balance(self):
		"Retrieves the current balance."
		return float(commands.getstatusoutput('{0} getbalance'.format(COIN_CLIENT))[1])

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
			g.db.execute('update drip_request set (trans_id) values (?) where id = ?',
					   	 [trans_id, self.drip_id])
			g.db.commit()

			# Console Message
			con_message = "Sent {0} {1} to {2}. Traction ID: {3}"
			return con_message.format(str(amount), COIN_NAME, self.address, trans_id)
		else:
			return "Insufficient Funds!"


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
	drip = DripRequest('1DarXYYGgvyHFQKZKsgUq676A9CK7D7FYa',
					   'DOUBLEMONEY', '69.87.160.3')
	drip.save()
	drip2 = DripRequest('1DarXYYGgvyHFQKZKsgUq676A9CK7D7FYa',
						'', '171.247.220.64')
	drip2.save()

# Main
if __name__ == "__main__":
	validate_unit_test()
	drip_unit_test()