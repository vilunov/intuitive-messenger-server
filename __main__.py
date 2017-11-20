from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import binascii
import struct
import os

class MessengerProtocol(Protocol):

	def getFileStr(self):
		filestr = ""
		for root, dirs, files in os.walk('files'):
			for fil in files:
				filestr += fil + ";"
			break
		filestr = filestr[:len(filestr) - 1]
		return filestr

	def connectionMade(self):
		self.currentMessage = bytes()
		self.namelen = 0
		self.fnamelen = 0
		self.txtlen = 0
		self.waiting = False
		self.msgtype = ""
		
		self.factory.clients.append(self)
		#We have to send available file table to the
		#new client right after connection was made

		encoded = self.getFileStr().encode("utf-8")
		notification = bytes([3, 0, 0]) + int.to_bytes(len(encoded), 4, byteorder='little') + encoded

		self.transport.write(notification)

	def connectionLost(self, reason):
		self.factory.clients.remove(self)

	def dataReceived(self, data):
		if self.waiting:
			self.currentMessage += data
			if len(self.currentMessage) >= self.namelen + self.fnamelen + self.txtlen:
				self.waiting = False
			else:
				return
		else:
			if data[0] == 0:
				self.msgtype = "Text"
			elif data[0] == 1:
				self.msgtype = "File"
			elif data[0] == 2:
				self.msgtype = "File Request"
			
			self.namelen = data[1]
			self.fnamelen = data[2]
			self.txtlen = int.from_bytes(data[3:7], byteorder='little')
			self.currentMessage = data[7:]
			
			if len(self.currentMessage) < self.namelen + self.fnamelen + self.txtlen:
				self.waiting = True
				return

		name = self.currentMessage[:self.namelen].decode("utf-8")
		filename = self.currentMessage[self.namelen:self.namelen + self.fnamelen].decode("utf-8")
		text = self.currentMessage[self.namelen + self.fnamelen:self.namelen + self.fnamelen + self.txtlen]

		if(self.msgtype == "File Request"):
			print("Received file request from " + name + " : " + filename)
			#Fetch binary string from file
			in_file = open(os.path.join("files", filename), "rb")
			dat = in_file.read()
			in_file.close()
			
			#Send it to the user
			request = bytes([1, 0, len(filename)]) + int.to_bytes(len(dat), 4, byteorder='little') + filename.encode("utf-8") + dat

			self.transport.write(request)
		elif(self.msgtype == "File"):
			print("Received file " + filename + " from " + name)
			#Extract bytes from base64 string and save it in "files" folder
			if not os.path.exists("files"):
				os.makedirs("files")
			file = open(os.path.join("files", filename), "ab")
			file.write(text)
			file.close()
			
			filestr =self.getFileStr().encode("utf-8")
			notification = bytes([3, len(name), 0]) + int.to_bytes(len(filestr), 4, byteorder='little') + name.encode("utf-8") + filestr

			for c in self.factory.clients:
				c.transport.write(notification)

			print("All clients are now notified about current file table")
		if(self.msgtype == "Text"):
			print("Received text from " + name + ": " + text.decode("utf-8"))
			#Send recieved text to all clients
			messg = bytes([0, len(name), 0]) + int.to_bytes(len(text), 4, byteorder='little') + name.encode("utf-8") + text

			for c in self.factory.clients:
				c.transport.write(messg)

		self.currentMessage = bytes()

if __name__ == "__main__":
	factory = Factory()
	factory.protocol = MessengerProtocol
	factory.clients = []
	
	reactor.listenTCP(8080, factory)
	reactor.run()
