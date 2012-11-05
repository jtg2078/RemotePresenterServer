import os.path
import json
import uuid

import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.httpserver

#################### Model definitions ####################

class Node(object):
	def __init__(self):
		self.nodeType = None
		self.nodeId = None
		self.params = {}
		self.handlers = set()
	
#################### Manager definitions ####################

class NodesManager(object):
	nodes = set()

	def createNode(self, nodeType, nodeId):
		node = Node()
		node.nodeType = nodeType
		node.nodeId = nodeId
		return node

	def addNode(self, node):
		existed = False
		for n in self.nodes:
			if n.nodeId == node.nodeId:
				existed = True
				break;
		if existed == False:
			self.nodes.add(node)

	def getNodeWithId(self, nodeID):
		for n in self.nodes:
			if n.nodeId == nodeID:
				print 'SDFSFSDFSDFSDFSDFSDFSDFSDFSDFSDFSDF'
				return n
		return None

	def getNodesWithType(self, nodeType):
		match = [n for n in self.nodes if n.nodeType == nodeType]
		return match

class DispatchManager(object):

	def _log(self, payload):
		"""dispatchPayloadMulti"""
		#print 'sent:'
		#print payload

	def dispatchPayloadSingle(self, source, to, payload):
		#print 'dispatchPayloadSingle'
		self._log(payload)
		p = json.dumps(payload)
		for handler in to.handlers:
			handler.send(p)

	def dispatchPayloadMulti(self, source, toList, payload):
		#print 'dispatchPayloadMulti'
		self._log(payload)
		p = json.dumps(payload)
		for to in toList:
			for handler in to.handlers:
				handler.send(p)

#################### Module definitions ####################

class RemoteControlModule(object):
	controller = None
	clients = set()
	currentInfo = {}

	def handleMessage(self, handler, msg):
		p = json.loads(msg)
		msgType = p['type']
		msgDetail = p['detail']
		source = None
		#print 'received:'
		#print msg
		if msgType == 'login':
			# handle log in
			"""
			check to see if node with same id already exists
				- if yes:
					update that node with the handler
				- if no:
					create a new node
					add to node list
				add the node to clients
			"""
			clientId = msgDetail['id']
			clientType = msgDetail['type']
			node = nodeManager.getNodeWithId(clientId)
			if node is None:
				node = nodeManager.createNode(clientType, clientId)
				nodeManager.addNode(node)
				#print 'node not found! creating a new one!'
			#print 'node with id:{0} is adding handler with id"{1}'.format(node.nodeId, handler.connID)
			node.handlers.add(handler)
			self.clients.add(node)
			info = {
				'type': 'loginInfo',
				'detail': {
					'connectionId': str(handler.connID)
				},
			}
			dispatchManager.dispatchPayloadSingle(source, node, info)
			print 'node with id: {0} has # of handler: {1}'.format(node.nodeId, len(node.handlers))
			#print 'debug print clients and nodes #'
			#print len(self.clients)
			#print len(nodeManager.nodes)
			#print handler.connID
			#for n in nodeManager.nodes:
			#	print 'node with id: {0} has # of handler: {1}'.format(n.nodeId, len(n.handlers))
		elif msgType == 'change':
			# handle change video
			"""
			change the video, needs the follow parameters
			- videoId
			- timestamp
			- action: play/pause
			notify all the client to ask the server for currentInfo
			"""
			self.currentInfo['videoId'] = msgDetail['videoId']
			self.currentInfo['timestamp'] = msgDetail['timestamp']
			self.currentInfo['action'] = msgDetail['action']
			info = {
				'type': 'playbackInfo',
				'detail': self.currentInfo,
			}
			dispatchManager.dispatchPayloadMulti(
				source, self.clients, info)
		elif msgType == 'inqury':
			# handle inquery current status
			"""
			get the current video info
			"""
			info = {
				'type': 'playbackInfo',
				'detail': self.currentInfo,
			}
			for client in self.clients:
				if handler in client.handlers:
					dispatchManager.dispatchPayloadSingle(
						source, client, info)
					break
		else:
			# undefined command
			print 'undefined msg type:'
			print p

	def handleDisconnect(self, handler):
		for n in self.clients:
			if handler in n.handlers:
				n.handlers.remove(handler)



#################### WebSocket handlers ####################

connections = set()
nodeManager = NodesManager()
dispatchManager = DispatchManager()
remoteControlModule = RemoteControlModule()

class wsHandler(tornado.websocket.WebSocketHandler):
	def initialize(self):
		self.connID = uuid.uuid1()

	def send(self, payload):
		self.write_message(payload)

class wsConnectHandler(wsHandler):

	def open(self):
		connections.add(self)

	def on_close(self):
		connections.remove(self)
		remoteControlModule.handleDisconnect(self)

	def on_message(self, msg):
		#print 'wsConnectHandler on_message:'
		#print self.connID
		remoteControlModule.handleMessage(self, msg)

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

class TestPageHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('test.html')

#################### server methods ####################

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/", MainHandler),
			(r'/remote', RemotePageHandler),
			(r'/admin', AdminPageHandler),
			(r'/ws/connect', wsConnectHandler),
			(r'/test', TestPageHandler),
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
		









