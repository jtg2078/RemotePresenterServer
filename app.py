import os.path
import json
import uuid

import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.httpserver


#################### Model definitions ####################

CLIENT_STATE_DISCONNECTED = 0
CLIENT_STATE_CONNECTED = 1

CLIENT_TYPE_STUDENT = 'student'
CLIENT_TYPE_INSTRUCTOR = 'instructor'
CLIENT_TYPE_ADMIN = 'admin'

class Client(object):
	clientID = None
	callback = None
	info = None
	state = 0

ADMIN_STATE_DISCONNECTED = 0
ADMIN_STATE_CONNECTED = 1

class Admin(object):
	deviceID = None
	handler = None
	info = None
	state = 0

class Payload(object):
	name = None
	detail = None

#################### Core methods ####################

class Manager(object):
	handlers = set()
	clients = {}
	instructor = None
	admin = None

	def handle_connect(self, handler):
		print 'handle_connect'
		self.handlers.add(handler)

	def handle_disconnect(self, handler):
		self.handlers.remove(handler)

	def process_msg_connect(self, handler, p):
		"""
			check to see if we already have this client in the record
				- if yes:
					1 .get the client from the record
				- if no:
					1. create a client object
					2. add the client object to the record
			update the state
			update the handler reference
		"""
		print 'process_msg_connect'
		clientType = p['clientType']
		if clientType == CLIENT_TYPE_STUDENT:
			clientID = p['deviceID']
			if clientID in self.clients:
				client = clients['clientID']
			else:
				client = Client()
				self.clients[clientID] = client
			client.state = CLIENT_STATE_CONNECTED
			client.handler = handler

			#send connection message to admin page
			if self.admin:
				p = {
					'msgType': 'info',
					'msgPayLoad': 'client:{0} has connected'.format(clientID),
				}
				if self.admin.handler:
					self.admin.handler.to_message(p)

		elif clientType == CLIENT_TYPE_INSTRUCTOR:
			if not self.instructor:
				self.instructor = Client()
			self.instructor.state = CLIENT_STATE_CONNECTED
			self.instructor.handler = handler
		elif clientType == CLIENT_TYPE_ADMIN:
			if not self.admin:
				self.admin = Client()
			self.admin.state = CLIENT_STATE_CONNECTED
			self.admin.handler = handler





	def process_msg_disconnect(self, handler, p):
		"""
			check to see if we already have this client in the record
				- if yes:
					1. get the client from the record
					2. update the state
					3. update the handler reference
		"""
		clientType = p['type']
		self.handlers.remove(handler)
		if clientType == CLIENT_TYPE_STUDENT:
			clientID = p['deviceID']
			if clientID in self.clients:
				client = clients['clientID']
				client.state = ADMIN_STATE_DISCONNECTED
				client.handler = None
			else:
				print 'disconnecting a client that we have no record of??!!'
		elif clientType == CLIENT_TYPE_INSTRUCTOR:
			self.instructor = None
		elif clientType == CLIENT_TYPE_ADMIN:
			self.admin = None

	def process_msg_info(self, handler, p):
		pass

	def process_msg_changeClientPage(self, handler, p):
		toPage = p['to']
		fromPage = p['from']
		cmd = json.dumps(p)
		self.send_msg_to_client(cmd)

	def handle_message(self, handler, msg):
		"""
			decode the message from JSON format
			determine the type of the msg
			process base on type of the msg
		"""
		p = json.loads(msg)
		print p
		if p['type'] == 'connect':
			self.process_msg_connect(handler, p)
		elif p['type'] == 'disconnect':
			self.process_msg_disconnect(handler, p)
		elif p['type'] == 'info':
			self.process_msg_info(handler, p)
		elif p['type'] == 'changePage':
			self.process_msg_changeClientPage(handler, p)
		else:
			print p

	def send_msg_to_client(self, msg, specifics=None):
		targets = self.clients
		if specifics:
			targets = specifics
		for clientID, client in targets.items():
			if client.state == CLIENT_STATE_CONNECTED:
				client.handler.to_message(msg)


#################### WebSocket methods ####################

class wsHandler(tornado.websocket.WebSocketHandler):
	connID = uuid.uuid1()

class wsClientHandler(wsHandler):

	def open(self):
		self.application.manager.handle_connect(self)

	def on_close(self):
		self.application.manager.handle_disconnect(self)

	def on_message(self, msg):
		self.application.manager.handle_message(self, msg)

	def to_message(self, msg):
		self.write_message(msg)


#################### API methods ####################

class apiHander(tornado.web.RequestHandler):
	def _outputJSON(self, p):
		self.content_type = 'application/json; charset=utf-8'
		self.write(json.dumps(p))

#################### web methods ####################

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.write("Hello, world")

class RemotePageHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('remote.html')

class AdminPageHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('admin.html')

#################### server methods ####################

class Application(tornado.web.Application):
	def __init__(self):
		self.manager = Manager()
		handlers = [
			(r"/", MainHandler),
			(r'/remote', RemotePageHandler),
			(r'/admin', AdminPageHandler),
			(r'/websocket/client/connect', wsClientHandler),
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
