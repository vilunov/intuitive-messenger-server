from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import json

class MessengerProtocol(Protocol):
	def connectionMade(self):
		self.factory.clients.append(self)

	def connectionLost(self, reason):
		self.factory.clients.remove(self)

	def dataReceived(self, data):
		print data
		message = json.loads(j)
		if(message.type=="Text"):
			for c in self.factory.clients:
				c.transport.write(data)


if __name__ == "__main__":
	factory = Factory()
	factory.protocol = MessengerProtocol
	factory.clients = []
	
	reactor.listenTCP(8080, factory)
	reactor.run()