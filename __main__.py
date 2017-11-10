from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import json
import binascii
import struct
import os

class MessengerProtocol(Protocol):

	def connectionMade(self):
		self.currentMessage = ""
		self.factory.clients.append(self)
		#We have to send available file table to the
		#new client right after connection was made
		filestr = ""
		for root, dirs, files in os.walk('files\\'):
			for fil in files:
				filestr+=fil + ";"
		filestr = filestr[:len(filestr) - 1]

		notification = {"type":"Table info","name": "",\
		"filename":"","date":"","text":filestr}

		self.transport.write(json.dumps(notification).encode())

	def connectionLost(self, reason):
		self.factory.clients.remove(self)

	def dataReceived(self, data):
		datastr = data.decode("utf-8")
		#This is called PRO100PEZDATIY PR0T0C0L
		if datastr[len(datastr) - 3:] == "END":

			message = json.loads(self.currentMessage + datastr[:len(datastr) - 3])

			if message["type"] != "File":
				print("Recieved " + message["type"] + " from " + message["name"] + " : " + message["text"])
			else:
				print("Recieved file " + message["filename"] + " from " + message["name"])

			if(message["type"] == "File Request"):
				#Fetch binary string from file
				in_file = open("files\\" + message["filename"], "rb")
				datastr = in_file.read()
				in_file.close()
				
				#Convert it to base64
				text = binascii.b2a_base64(datastr).decode()
				
				#Send it to the user
				request = {"type":"File","name":"","filename":message["filename"],"date":"","text":text}
				self.transport.write(json.dumps(request).encode())
			if(message["type"] == "File"):
				#Extract bytes from base64 string and save it in "files" folder
				datastr = binascii.a2b_base64(message['text'])
				if not os.path.exists("files\\"):
					os.makedirs("files\\")
				file = open("files\\" + message["filename"],'ab')
				file.write(datastr)
				file.close()
				
				#Notify all users about new file
				notification = {"type":"Notification","name": message["name"],\
				"filename":"","date":"","text":message["date"] + \
				 "  User " + message["name"] + " uploaded new file " + message["filename"] + "\n"}
				for c in self.factory.clients:
					c.transport.write(json.dumps(notification).encode())

				#Send info about new currently available files to all clients
				filestr = ""
				for root, dirs, files in os.walk('files\\'):
					for fil in files:
						filestr+=fil + ";"
				filestr = filestr[:len(filestr) - 1]

				notification = {"type":"Table info","name": "",\
				"filename":"","date":"","text":filestr}

				for c in self.factory.clients:
					c.transport.write(("#" + json.dumps(notification)).encode())

				print("All clients are now notified about current file table")

				#Be ready for the new request
				self.currentMessage = ""

			if(message["type"] == "Text"):
				#Send recieved text to all clients
				messg =  {"type":"Text","name":message["name"] ,\
					"filename":message["filename"],"date":message["date"],"text":message["text"] }
				jsn = json.dumps(messg)
				for c in self.factory.clients:
					c.transport.write(jsn.encode())

				self.currentMessage = ""
		else:
			#Accumulate request
			self.currentMessage+=datastr

if __name__ == "__main__":
	factory = Factory()
	factory.protocol = MessengerProtocol
	factory.clients = []
	
	reactor.listenTCP(8080, factory)
	reactor.run()