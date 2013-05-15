import web
import random
import datetime
from DripRequest import *

DATABASE_FILE = 'trc.db'
DATABASE_TABLE = 'drip_request'
DEFAULT_SEND_VAL = 0.0001

urls = (
	'/', 'index',
	'/add', 'add',
	'/good', 'good',
	'/bad', 'bad',
	'/duplicate', 'duplicate',
	'/send', 'send',
	'/chat', 'chat',
	'/resources', 'resources'
)

def get_index(form_submit_status = None):
	"""Displays the default index page, or a success/error page."""
	render = web.template.frender('index.html')
	captcha = (random.randrange(1, 15), random.randrange(1, 15))
	captcha_awns = captcha[0] + captcha[1]
	recent_drips = Database(DATABASE_FILE, DATABASE_TABLE).get_recent()
	return render(recent_drips, form_submit_status, captcha, captcha_awns)

def send_coins():
	"""Sends queued coins."""
	data = Database(DATABASE_FILE, DATABASE_TABLE)
	for i in data.get_unsent():
		DripRequest(i[1], i[3], i[4], i[2], i[0]).send(DEFAULT_SEND_VAL, data)
	return "Sent!"

class add:
	"""Takes add POST request, and redirects to relevant page"""
	def POST(self):
		i = web.input()
		ip = str(web.ctx.get('ip'))
		now = str(datetime.datetime.now())
		try:
			if i.captcha != i.captcha_awns: raise ValueError
			print("Good drip request. Saving to database...")
			DripRequest(now, i.address, i.coupon, ip).save()
			raise web.seeother('/good')
		except ValueError:
			print("Bad drip request. Redirecting...")
			raise web.seeother('/bad')
		except LookupError:
			print("Duplicate IP or Address. Redirecting...")
			raise web.seeother('/duplicate')
		else:
			print("Unexplained failure.")
			raise web.seeother('/bad')

# Unfortunately, web.py does not allow me to route to functions, so
# this will always look a bit messy in my opinion. 

class index:
	"""Displays index page."""
	def GET(self): return get_index()

class good:
	"""Displays success page."""
	def GET(self): return get_index("good")

class bad:
	"""Displays error page."""
	def GET(self): return get_index("bad")

class duplicate:
	"""Displays duplicate page."""
	def GET(self): return get_index("duplicate")

class send:
	"""Sends unprocessed drips."""
	def GET(self): return send_coins()

# Other pages.

class chat:
	def GET(self): return web.template.frender('chat.html')()

class resources:
	def GET(self): return web.template.frender('resources.html')()


if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()