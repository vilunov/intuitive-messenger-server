from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import json


class MessengerProtocol(Protocol):

	def connectionMade(self):
		self.currentMessage = ""
		self.factory.clients.append(self)

	def connectionLost(self, reason):
		self.factory.clients.remove(self)

	def dataReceived(self, data):
		if data[len(data)-3:]=="END":
			print self.currentMessage+data[:len(data)-3]
			message = json.loads(self.currentMessage+data[:len(data)-3])
			if(message['type']=="Table Request"):
				print "idi naxui" #fetch and send table of files
			if(message['type']=="File Request"):
				file ="" #fetch file and convert to base 64
				request = {"type":"File","name":"","filename":message["filename"],"date":"","text":file}
				self.transport.write(json.dumps(request))
			if(message['type']=="File"):
				#write file on server (todo: sdelat eto normalno)
				#file = open("files\\"+message["filename"],'w')
				#file.write(message["text"])
				#file.close()
				notification = {"type":"Notification","name":"",\
				"filename":"","date":"","text":message["date"] +\
				 "  User " + message["name"] + " uploaded new file " + message["filename"]+"\n"}
				for c in self.factory.clients:
					c.transport.write(json.dumps(notification))
				self.currentMessage=""
			if(message['type']=="Text"):
				for c in self.factory.clients:
					c.transport.write(self.currentMessage)
				self.currentMessage=""
		else:
			self.currentMessage+=data

if __name__ == "__main__":
	factory = Factory()
	factory.protocol = MessengerProtocol
	factory.clients = []
	
	reactor.listenTCP(8080, factory)
	reactor.run()