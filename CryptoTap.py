import web
import random
import datetime
from DripRequest import *

urls = (
	'/', 'index',
	'/add', 'add',
	'/good', 'good',
	'/bad', 'bad',
	'/duplicate', 'duplicate',
	'/send', 'send'
)

def get_index(form_submit_status = None):
	"""Displays the default index page, or a success/error page."""
	render = web.template.frender('index.html')
	captcha = (random.randrange(1, 15), random.randrange(1, 15))
	captcha_awns = captcha[0] + captcha[1]
	recent_drips = Database('test.db', 'drip_request').get_recent()
	return render(recent_drips, form_submit_status, captcha, captcha_awns)

def send_coins():
	"""Sends queued coins."""
	data = Database('test.db', 'drip_request')
	for i in data.get_unsent():
		print(DripRequest(i[1], i[3], i[4], i[2], i[0]))
		DripRequest(i[1], i[3], i[4], i[2], i[0]).send(0.001)

class add:
	"""Takes add POST request, and redirects to relevant page"""
	def POST(self):
		i = web.input()
		ip = str(web.ctx.get('ip'))
		now = str(datetime.datetime.now())
		try:
			if i.captcha != i.captcha_awns: raise ValueError
			print("good")
			DripRequest(now, i.address, i.coupon, ip).save()
			raise web.seeother('/good')
		except ValueError:
			print("bad")
			raise web.seeother('/bad')
		except LookupError:
			print("duplicate")
			raise web.seeother('/duplicate')
		else:
			print("fail")
			raise web.seeother('/bad')

class index:
	"""Displays index page."""
	def GET(self):
		return get_index()

class good:
	"""Displays success page."""
	def GET(self):
		return get_index("good")

class bad:
	"""Displays error page."""
	def GET(self):
		return get_index("bad")

class duplicate:
	"""Displays duplicate page."""
	def GET(self):
		return get_index("duplicate")

class send:
	"""Sends unprocessed drips."""
	def GET(self):
		send_coins()
		return "Sent."


if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()