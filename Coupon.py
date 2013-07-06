import random
import sqlite3
import hashlib
from flask import Flask


# Load Settings  ---------------------------------------------------------------
app = Flask(__name__)
app.config.from_pyfile('settings.cfg')


# Coupon Class  ----------------------------------------------------------------
class Coupon:
	def __init__(self, conn):
		"""
		Allows the admin to create and delete used coupons. Also allows
		the system to validate and lookup coupons. 

		"""
		self.conn = conn # mysqlite db stuff
		self.cursor = self.conn.cursor()

	def new(self, coup_value, max_use = 1):
		"""Creates a new coupon."""

		query = "INSERT INTO coupon_list (id, coup_value, max_use, access_key)"
		query += "VALUES (NULL, ?, ?, ?)"

		# create a random hash, the first 10 digits will be used as 
		# the coupon code. this is inserted into the database and 
		# it is returned
		random.seed()
		ran_num = str(random.random()).encode('utf-8')
		access_key = str(hashlib.sha1().hexdigest())
		access_key = access_key[:10].lower()

		self.cursor.execute(query, (coup_value, max_use, access_key,))
		self.conn.commit()

		return access_key

	def search(self, access_key):
		"""Searches for the coupon in the database."""
		query = "select * from coupon_list where access_key=? limit 1"
		self.cursor.execute(query, (access_key.lower(),))
		return self.cursor.fetchone()

	def use(self, access_key):
		"""
		Attempt to use the coupon. If it is a valid coupon then decrement 
		max_use field, and then return the coupon's value.

		"""
		coupon = self.search(access_key) # check if valid coupon
		if coupon == None: return 0 # if not found return 0 value

		coup_id = coupon[0] # id
		coup_val = coupon[1] # coup_value
		max_use = coupon[2] # max_use

		if max_use >= 1: # if coupon still has uses left decrement uses
			query = "update coupon_list set max_use=(max_use - 1) where id=?"
			self.cursor.execute(query, (coup_id,))
			self.conn.commit()
			return coup_val
		return 0 # fall-though case

	def clear(self):
		"""Delete used up coupons"""
		query = "delete from coupon_list where max_use=0"
		self.cursor.execute(query)
		self.conn.commit()