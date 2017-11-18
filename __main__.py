from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
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

		notification = chr(3).encode("utf-8") + chr(0).encode("utf-8") + chr(0).encode("utf-8") \
			 + filestr.encode("utf-8") + "END".encode("utf-8")

		self.transport.write(notification)

	def connectionLost(self, reason):
		self.factory.clients.remove(self)

	def dataReceived(self, data):
		#This is called PRO100PEZDATIY PR0T0C0L
		if data[len(data) - 3:].decode("utf-8") == "END":
			datastr = self.currentMessage + data[:len(data) - 3].decode("utf-8")
			type = ""
			if ord(datastr[0]) == 0:
				type = "Text"
			elif ord(datastr[0]) == 1:
				type = "File"
			elif ord(datastr[0]) == 2:
				type = "File Request"
			
			namelen = ord(datastr[1])
			fnamelen = ord(datastr[2])
			txtlen = len(datastr[3 + namelen + fnamelen:])

			name = datastr[3:3 + namelen]
			filename = datastr[3 + namelen:3 + namelen + fnamelen]
			text = datastr[3 + namelen + fnamelen:3 + namelen + fnamelen + txtlen]

			if type != "File":
				print("Recieved " + type + " from " + name + " : " + text)
			else:
				print("Recieved file " + filename + " from " + name)

			if(type == "File Request"):
				#Fetch binary string from file
				in_file = open("files\\" + filename, "rb")
				dat = in_file.read()
				in_file.close()
				
				txt = binascii.b2a_base64(dat)
				#Send it to the user
				request = chr(1).encode("utf-8") + chr(0).encode("utf-8") + chr(len(filename)).encode("utf-8") + \
			 filename.encode("utf-8") + txt + "END".encode("utf-8")

				self.transport.write(request)

			if(type == "File"):
				dat = binascii.a2b_base64(datastr[3 + namelen + fnamelen:3 + namelen + fnamelen + txtlen])
				#Extract bytes from base64 string and save it in "files" folder
				if not os.path.exists("files\\"):
					os.makedirs("files\\")
				file = open("files\\" + filename,'ab')
				file.write(dat)
				file.close()
				
				#Notify all users about new file

				note = "User " + name + " uploaded new file " + filename + "\n"

				notification = chr(2).encode("utf-8") + chr(len(name)).encode("utf-8") + chr(0).encode("utf-8") + \
				 name.encode("utf-8") + note.encode("utf-8")

				for c in self.factory.clients:
					c.transport.write(notification)

				#Send info about new currently available files to all clients
				filestr = ""
				for root, dirs, files in os.walk('files\\'):
					for fil in files:
						filestr+=fil + ";"
				filestr = filestr[:len(filestr) - 1]

				notification = '#'.encode("utf-8") + chr(3).encode("utf-8") + chr(0).encode("utf-8") + chr(0).encode("utf-8") + \
				 filestr.encode("utf-8") + "END".encode("utf-8")

				for c in self.factory.clients:
					c.transport.write(notification)

				print("All clients are now notified about current file table")

				#Be ready for the new request
				self.currentMessage = ""

			if(type == "Text"):
				#Send recieved text to all clients
				messg = chr(0).encode("utf-8") + chr(len(name)).encode("utf-8") + chr(0).encode("utf-8") + \
			 name.encode("utf-8") + text.encode("utf-8") + "END".encode("utf-8")

				for c in self.factory.clients:
					c.transport.write(messg)

				self.currentMessage = ""
		else:
			#Accumulate request
			self.currentMessage+=data.decode("utf-8")

if __name__ == "__main__":
	factory = Factory()
	factory.protocol = MessengerProtocol
	factory.clients = []
	
	reactor.listenTCP(8080, factory)
	reactor.run()