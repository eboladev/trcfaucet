import sqlite3
from DripRequest import *
from random import randrange
from datetime import datetime
from datetime import timedelta

from flask import g
from flask import flash
from flask import abort
from flask import Flask
from flask import url_for
from flask import request
from flask import session
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

def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql') as f:
			db.cursor().executescript(f.read())
		db.commit()

def get_connection():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = connect_db()
    return db

def query_db(query, args=(), one=False):
	cur = g.db.execute(query, args)
	rv = [dict((cur.description[idx][0], value)
		for idx, value in enumerate(row)) for row in cur.fetchall()]
	return (rv[0] if rv else None) if one else rv


# Helper Functions
def sub_cypher(ip, offset):
	"""Number substitution offset cypher(protect ips). Don't use offset values 0-9."""
	# Implement Better Cypher: rotate((ip % sum1bits(ip) ), sum0bits(ip))
	return [(abs(int(x) - offset)%10) if x.isdigit() else '.' for x in ip]

def get_html(save_time, ip, trans_id):
	"""Transform database output into a table."""
	diff_time = datetime.now() - datetime.strptime(save_time, "%Y-%m-%d %H:%M:%S")
	diff_time = divmod(diff_time.seconds, 60)
	diff_time = "{0} mins, {1} secs ago".format(diff_time[0], diff_time[1])
	obfuscated_ip = ''.join(map(str, sub_cypher(list(ip), 655)))
	if trans_id == "UNSENT":
		html = "<tr><td>{0}</td><td>{1}</td><td>Processing...</td></tr>"
		html = html.format(diff_time, obfuscated_ip)
	else:
		short_trans_id = trans_id[:37] + "..."
		trans_id_url = "http://cryptocoinexplorer.com:3750/tx/{0}".format(trans_id)
		html = "<tr><td>{0}</td><td>{1}</td><td><a href='{2}'>{3}</a></td></tr>"
		html = html.format(diff_time, obfuscated_ip, trans_id_url, short_trans_id)
	
	return html

def get_index(form_submit_status = None):
	"""Displays the default index page, or a success/error page."""
	captcha = (randrange(1, 15), randrange(1, 15))
	captcha_awns = captcha[0] + captcha[1]

	recent_drips = g.db.execute('SELECT * FROM drip_request ORDER BY id DESC LIMIT 10')
	recent_drips_html = [get_html(row[1], row[2], row[5]) for row in recent_drips.fetchall()]
	recent = ''.join(map(str, recent_drips_html))
	
	cur = g.db.execute('SELECT Count(*) FROM drip_request')
	stats = 3060 + int(cur.fetchone()[0])

	return render_template('index.html', recent=recent, form_submit=form_submit_status,
						   captcha=captcha, captcha_awns=captcha_awns, stats=stats)


# Routes
@app.route('/')
def index(): return get_index()

# @app.route('/add', methods=['POST'])
# def add(): 
# 	ip = str(request.remote_addr)
# 	try:
# 		if request.form['captcha'] != request.form['captcha_awns']: 
# 			raise ValueError
# 		print("Good drip request. Saving to database...")
# 		data = Database(DATABASE_FILE, DATABASE_TABLE)
# 		DripRequest(request.form['address'], request.form['coupon'],
# 				    ip).save(data)
# 		return redirect('/good')
# 	except ValueError:
# 		print("Bad drip request. Redirecting...")
# 		return redirect('/bad')
# 	except LookupError:
# 		print("Duplicate IP or Address. Redirecting...")
# 		return redirect('/duplicate')
# 	else:
# 		print("Unexplained failure.")
# 		return redirect('/bad')

# @app.route('/good')
# def good(): return get_index("good")
# @app.route('/bad')
# def bad(): return get_index("bad")
# @app.route('/duplicate')
# def duplicate(): return get_index("duplicate")

# @app.route('/chat')
# def chat(): return render_template('chat.html')
# @app.route('/resources')
# def resources(): return render_template('resources.html')


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)