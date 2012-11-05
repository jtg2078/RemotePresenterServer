import os.path
import json
from uuid import uuid4

import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.httpserver


#################### Model definitions ####################

CLIENT_STATE_DISCONNECTED = 0
CLIENT_STATE_CONNECTED = 1

class Client(object):
	clientID = None
	callback = None
	info = None
	state = 0

ADMIN_STATE_DISCONNECTED = 0
ADMIN_STATE_CONNECTED = 1

class Admin(object):
	deviceID = None
	callback = None
	info = None
	state = 0

class Payload(object):
	name = None
	detail = None

#################### Core methods ####################

class RemoteControlEx(object):
	handlers = []
	clients = {}
	admin = None

	def add_callback(self, callback):
		self.callbacks.append(callback)

	def remove_callback(self, callback):
		self.callbacks.remove(callback)

	def client_connect(self):
		pass

	def client_disconnect(self):
		pass

	def admin_connect(self):
		pass

	def admin_disconnect(self):
		pass

	def issue_command(self, command, specifics=None):
		clients = self.clients
		if specifics:
			clients = specifics
		for client in clients:
			if client.state == CLIENT_STATE_CONNECTED:
				client.callback(command)

class RemoteControl(object):
	currentPage = 0
	callbacks = []
	console = None

	def register(self, callback):
		self.callbacks.append(callback)

	def unregister(self, callback):
		self.callbacks.remove(callback)

	def consoleConnect(self, callback):
		self.console = callback

	def consoleDisconnect(self):
		self.console = None

	def changePage(self, newPage):
		print 'page changed!'
		self.currentPage = newPage
		self.notifyCallbacks()

	def getCurrentPage(self):
		return self.currentPage

	def notifyCallbacks(self):
		for callback in self.callbacks:
			callback(self.getCurrentPage())

#################### WebSocket methods ####################

class RemoteHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		self.application.remoteControl.register(self.callback)

	def on_close(self):
		self.application.remoteControl.unregister(self.callback)

	def on_message(self):
		pass

	def callback(self, page):
		msg = page
		print msg
		self.write_message(msg)

class ConsoleHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		self.application.remoteControl.consoleConnect(self.callback)

	def on_close(self):
		self.application.remoteControl.consoleDisconnect(self.callback)

	def on_message(self):
		pass

	def callback(self, payload):
		print payload
		self.write_message(payload)

class wsClientHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		self.application.rc.add_callback(self)

	def on_close(self):
		self.application.rc.remove_callback(self)

	def on_message(self, msg):
		self.application.rc.handle_client_incoming(self, msg)

	def to_message(self, msg):
		self.write_message(msg)


#################### API methods ####################

class apiHander(tornado.web.RequestHandler):
	def _outputJSON(self, p):
		self.content_type = 'application/json; charset=utf-8'
		self.write(json.dumps(p))

class apiChangePageHandler(apiHander):
	def post(self):
		toPage = self.get_argument('page')
		fromPage = self.application.remoteControl.getCurrentPage()
		self.application.remoteControl.changePage(toPage)
		p = {
			'status': 'ok',
			'from': fromPage,
			'to': toPage,
			'msg': 'page is changed from {0} to {1}'.format(fromPage, toPage)
		}
		self._outputJSON(p)

#################### web methods ####################

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.write("Hello, world")

class PoemPageHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('index.html')
	def post(self):
		noun1 = self.get_argument('noun1')
		noun2 = self.get_argument('noun2')
		verb = self.get_argument('verb')
		noun3 = self.get_argument('noun3')
		self.render('poem.html', roads=noun1, wood=noun2, made=verb,
			difference=noun3)

class RemotePageHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('remote.html')

#################### server methods ####################

class Application(tornado.web.Application):
	def __init__(self):
		self.remoteControl = RemoteControl()
		handlers = [
			(r"/", MainHandler),
			(r'/poem', PoemPageHandler),
			(r'/remote', RemotePageHandler),
			(r'/api/change', apiChangePageHandler),
			(r'/websocket/connect', RemoteHandler),
		]
		settings = {
			'template_path': 'templates',
			'static_path': 'static'
		}
		tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
	tornado.options.parse_command_line()
	app = Application()
	server = tornado.httpserver.HTTPServer(app)
	server.listen(8080)
	tornado.ioloop.IOLoop.instance().start()


"""
application = tornado.web.Application(handlers=[
	(r"/", MainHandler),
	(r'/poem', PoemPageHandler),
	],
	template_path=os.path.join(os.path.dirname(__file__), "templates"))
To map a local folder to a remote folder, right-click on it in the side bar
and select the SFTP/SFTP > Map to Remote... You will enter your connection
parameters and a new file will be created named sftp-config.json.

Once this file has been saved, all files in that folder and all subfolders
will have various operations available via the side bar context menu, editor
context menu and command palette.
"""