import random
import socket
import string
import urlparse
import struct
import httplib

import pybonjour


ITUNES_PAIR_STRING_LENGTH = 64
ITUNES_GUID_STRING_LENGTH = 64
ITUNES_DACP_PORT = 3689

BONJOUR_SERVICE_NAME = 'Pinchy'
BONJOUR_SERVICE_REGTYPE = '_touch-remote._tcp'
BONJOUR_SERVICE_PORT = 1024
BONJOUR_SERVICE_TXT_STRING = 'DvNm={name}\nRemV=10000\nDvTy=iPod\nRemN=Remote\ntxtvers=1\nPair={pair}'

DACP_DEVICE_PORT = 1024


IS_VALID = 0x01
IS_INVALID = 0x02


def generate_hex_string(bits):
	return hex(random.getrandbits(bits))[2:-1]

def create_txt_record(record):
	return ''.join(['%s%s' % (chr(len(r)), r) for r in record.splitlines()])

def parse_http_request(request):
	data = request.split('\r\n')
	
	command, path, version = map(string.strip, data.pop(0).split(' ', 2))
	headers = {}
	
	while data:
		head = data.pop(0)
		if head == '': break
		headers.update([map(string.strip, head.split(': ', 1))])
	
	data = data.pop(0)
	
	return command, path, version, headers, data



class DACPClient:
	def __init__(self, sock, addr, code, name):
		self.addr = addr
		self.code = code
		self.name = name
		self.sock = sock
	
	def __repr__(self):
		return '<DACPClient({addr}, {hash})>'.format(addr=self.addr, hash=self.hash)
	

class DACPService:
	def __init__(self, **kwargs):
		self.name = kwargs.get('name', 'DCAP')
		self.pair = kwargs.get('pair', generate_hex_string(ITUNES_PAIR_STRING_LENGTH))
		self.guid = kwargs.get('guid', generate_hex_string(ITUNES_GUID_STRING_LENGTH))
		
		self.__server = None
		self.__service = None
	
	
	def _start_server(self):
		self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__server.bind(('', DACP_DEVICE_PORT))
		self.__server.listen(1)
	
	def _start_bonjour(self):
		self.__service = pybonjour.DNSServiceRegister(name=BONJOUR_SERVICE_NAME, regtype=BONJOUR_SERVICE_REGTYPE, port=BONJOUR_SERVICE_PORT, txtRecord=create_txt_record(BONJOUR_SERVICE_TXT_STRING.format(name=self.name, pair=self.pair)))
	
	
	def open(self, **kwargs):
		self.close()
		
		self.name = kwargs.get('name', self.name)
		self.pair = kwargs.get('pair', self.pair)
		self.guid = kwargs.get('pair', self.guid)
		
		self._start_server()
		self._start_bonjour()
	
	def close(self):
		if self.__server:
			self.__server.close()
			self.__server = None
		
		if self.__service:
			self.__service.close()
			self.__service = None
	
	
	def accept(self):
		if not self.__server:
			return None
		
		sock, addr = self.__server.accept()
		query = urlparse.parse_qs(urlparse.urlparse(parse_http_request(sock.recv(512))[1]).query)
		
		return DACPClient(sock, addr, query['pairingcode'][0], query['servicename'][0])
	
	def respond(self, client, mode):
		if mode is IS_VALID:
			values = {'cmpg': ''.join([chr(int(self.guid[i:i + 2], 16)) for i in range(0, 16, 2)]), 'cmnm': 'devicename', 'cmty': 'ipod'}
			encoded = ''
			
			for key, value in values.iteritems():
				encoded += '%s%s%s' % (key, struct.pack('>i', len(value)), value)
			
			header = 'cmpa%s' % (struct.pack('>i', len(encoded)))
			encoded = '%s%s' % (header, encoded)
			
			client.sock.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n{data}\r\n'.format(data=encoded))
		
		client.sock.close()
	


class DACPConnection:
	def __init__(self, **kwars):
		self.host = kwargs.get('host', 'localhost')
		self.port = kwargs.get('port', ITUNES_DACP_PORT)
		
		self.__connection = None
	
	
	def _login(self):
		pass
	
	
	def open(self):
		self.close()
		
		self.__connection = httplib.HTTPConnection(self.host, self.port)
	
	def close(self):
		if self.__connection:
			self.__connection.close()
			self.__connection = None
	
	
	def send(self):
		pass
	


class ITunesController(DACPConnection):
	def __init__(self, *kwargs):
		DACPConnection.__init__(self, **kwargs)
	
	
	def next_song(self):
		pass
	

