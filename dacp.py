import select
import random
import socket
import urlparse
import string
import struct
import re
import httplib
import urllib
import hashlib
import sys

import pybonjour


DNS_REMOTE_NAME = 'Pinchy'
DNS_REMOTE_TYPE = '_touch-remote._tcp'
DNS_REMOTE_PORT = 1024
DNS_REMOTE_PAIR_LENGTH = 64
DNS_REMOTE_GUID_LENGTH = 64

DNS_TOUCHABLE_NAME = 'Gamblor'
DNS_TOUCHABLE_TYPE = '_touch-able._tcp'
DNS_TOUCHABLE_PORT = 3689
DNS_TOUCHABLE_ID_LENGTH = 64

PAIR_VALID = 0x01
PAIR_INVALID = 0x02


def encode_txt_record(record):
	return ''.join(['{0}{1}'.format(chr(len(i)), i) for i in map('{0[0]}={0[1]}'.format, record.iteritems())])

def decode_txt_record(record):
	q = list(record)
	d = {}
	
	while q:
		d.update([read(q, ord(read(q, 1))).split('=', 1)])
	
	return d


def generate_hex_string(bits):
	return hex(random.getrandbits(bits))[2:-1]

def generate_pairing_code(pair, code):
	return hashlib.md5(pair + ''.join([c + "\x00" for c in code])).hexdigest().upper()


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


def encode_msg(msg):
	encoded = ''.join([('%s%s%s' % (key, struct.pack('>i', len(value)), value)) for key, value in msg.iteritems()])
	
	return '%s%s' % (struct.pack('>i', len(encoded)), encoded)



class Parser:
	def __init__(self, raw):
		self._raw = raw
	
	def __call__(self, raw):
		self._raw = raw
	
	
	def nested(self, tag):
		s = re.search(tag, self._raw)
		
		if not s: return None
		
		p = s.start()
		l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
		
		return Parser(self._raw[p + 8:p + 8 + l])
	
	def array(self, tag):
		q = []
		for m in re.finditer(tag, self._raw):
			p = m.start()
			l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
			q += [Parser(self._raw[p + 8:p + 8 + l])]
		
		return q
	
	
	def string(self, tag=None):
		if not tag:
			return self._raw
		
		s = re.search(tag, self._raw)
		if not s:
			return None
		
		p = s.start()
		l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
		
		return self._raw[p + 8:p + 8 + l]
	
	def bool(self, tag=None):
		if not tag:
			return bool(struct.unpack('>B', self._raw)[0])
		
		s = re.search(tag, self._raw)
		if not s:
			return None
		
		p = s.start()
		l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
		
		return bool(struct.unpack('>B', self._raw[p + 8:p + 8 + l])[0])
	
	def int(self, tag=None):
		if not tag:
			return struct.unpack('>I', self._raw)[0]
		
		s = re.search(tag, self._raw)
		if not s:
			return None
		
		p = s.start()
		l = struct.unpack('>I', self._raw[p + 4:p + 8])[0]
		
		return struct.unpack('>I', self._raw[p + 8:p + 8 + l])[0]
	



class DNSService(object):
	def __init__(self, **kwargs):
		self.timeout = kwargs.get('timeout', 5)
		
		self.__name = kwargs.get('name')
		self.__type = kwargs.get('type')
		self.__port = kwargs.get('port')
		self.__record = kwargs.get('txt_record', {})
		
		self.__sdref = None
	
	
	def __callback(self, sdref, flags, error, name, regtype, domain):
		if error != pybonjour.kDNSServiceErr_NoError:
			self.close()
	
	
	@property
	def name(self):
		return self.__name
	
	@property
	def type(self):
		return self.__type
	
	@property
	def port(self):
		return self.__port
	
	
	def register(self):
		self.close()
		
		self.__sdref = pybonjour.DNSServiceRegister(
			name=self.__name,
			regtype=self.__type,
			port=self.__port,
			txtRecord=encode_txt_record(self.__record),
			callBack=self.__callback
		)
		
		ready = select.select([self.__sdref], [], [], self.timeout)
		if self.__sdref not in ready[0]:
			self.close()
		
		else:
			pybonjour.DNSServiceProcessResult(self.__sdref)
	
	def close(self):
		if self.__sdref:
			self.__sdref.close()
			self.__sdref = None
	
	
	def is_alive(self):
		return bool(self.__sdref)
	

class DNSBrowser(object):
	class Service(object):
		def __init__(self):
			self._name = None
			self._type = None
			self._domain = None
			self._full_name = None
			self._host_target = None
			self._txt_record = None
			self._rr_full_name = None
			self._rr_type = None
			self._rr_class = None
			self._rr_data = None
			self._rr_ttl = None
		
		
		@property
		def name(self):
			return self._name
		
		@property
		def type(self):
			return self._type
		
		@property
		def domain(self):
			return self._domain
		
		@property
		def full_name(self):
			return self._full_name
		
		@property
		def host_target(self):
			return self._host_target
		
		@property
		def txt_record(self):
			return self._txt_record
		
		@property
		def rr_full_name(self):
			return self._rr_full_name
		
		@property
		def rr_type(self):
			return self._rr_type
		
		@property
		def rr_class(self):
			return self._rr_class
		
		@property
		def rr_data(self):
			return self._rr_data
		
		@property
		def rr_ttl(self):
			return self._rr_ttl
		
	
	
	def __init__(self, **kwargs):
		self.timeout = kwargs.get('timeout', 5)
		
		self.__type = kwargs.get('type')
		
		self.__service = None
		self.__sdref = None
	
	
	def _callback_query(self, sdref, flags, interfaceindex, error, fullname, rrtype, rrclass, rdata, ttl):
		self.__service._rr_full_name
		self.__service._rr_type
		self.__service._rr_class
		self.__service._rr_data
		self.__service._rr_ttl
	
	def _callback_resolve(self, sdref, flags, interfaceindex, error, fullname, hosttarget, port, txtrecord):
		if error != pybonjour.kDNSServiceErr_NoError:
			return
		
		self.__service._full_name = fullname
		self.__service._host_target = hosttarget
		self.__service._port = port
		self.__service._txt_record = txtrecord
		
		sdref = pybonjour.DNSServiceQueryRecord(interfaceIndex=interfaceindex,
												fullname=hosttarget,
												rrtype=pybonjour.kDNSServiceType_A,
												callBack=self._callback_query)
		
		ready = select.select([sdref], [], [], 5)
		if sdref not in ready[0]:
			return
		
		pybonjour.DNSServiceProcessResult(sdref)
		sdref.close()
	
	def _callback_browse(self, sdref, flags, interfaceindex, error, servicename, regtype, replydomain):
		if error != pybonjour.kDNSServiceErr_NoError:
			self.close()
			return
		
		self.__service = self.__class__.Service()
		
		self.__service._name = servicename
		self.__service._type = regtype
		self.__service._domain = replydomain
				
		sdref = pybonjour.DNSServiceResolve(0,
											interfaceindex,
											servicename,
											regtype,
											replydomain,
											self._callback_resolve)
		
		ready = select.select([sdref], [], [], 5)
		if sdref not in ready[0]:
			return
		
		pybonjour.DNSServiceProcessResult(sdref)
		sdref.close()
		
		if (flags & pybonjour.kDNSServiceFlagsAdd):
			self.on_added(self.__service)
		
		else:
			self.on_removed(self.__service)
	
	
	def register(self):
		self.__sdref = pybonjour.DNSServiceBrowse(regtype=self.__type,
												  callBack=self._callback_browse)
	
	def close(self):
		if self.__sdref:
			self.__sdref.close()
			self.__sdref = None
	
	
	def is_alive(self):
		return bool(self.__sdref)
	
	
	def process(self):
		if self.__sdref:
			ready = select.select([self.__sdref], [], [], self.timeout)
			if self.__sdref not in ready[0]:
				self.close()
			
			else:
				pybonjour.DNSServiceProcessResult(self.__sdref)
	
	
	def on_added(self, service):
		pass
	
	def on_removed(self, service):
		pass
	


class DACPRemoteService(DNSService):
	def __init__(self, **kwargs):
		self.__name = kwargs.get('name', '')
		self.__port = kwargs.get('port', DNS_REMOTE_PORT)
		self.__type = kwargs.get('type', 'iPod')
		self.__pair = kwargs.get('pair', generate_hex_string(DNS_REMOTE_PAIR_LENGTH).upper())
		
		txt_record = {'RemV': '10000', 'RemN': 'Remote', 'txtvers': '1', 'DvNm': self.__name, 'DvTy': self.__type, 'Pair': self.__pair}
		DNSService.__init__(self, name=DNS_REMOTE_NAME,
								  type=DNS_REMOTE_TYPE,
								  port=self.__port,
								  txt_record=txt_record)
	
	
	@property
	def name(self):
		return self.__name
	
	@property
	def port(self):
		return self.__port
	
	@property
	def type(self):
		return self.__type
	
	@property
	def pair(self):
		return self.__pair
	

class DACPRemoteBrowser(DNSBrowser):
	def __init__(self, **kwargs):
		DNSBrowser.__init__(self, type=DNS_REMOTE_TYPE)
		#data = decode_txt_record(txtrecord)
		#ip = socket.inet_ntoa(rdata)
	
	
	def on_added(self, service):
		print 'added:', service.name
	
	def on_removed(self, service):
		print 'removed:', service.name
	


class DACPRemoteServer(object):
	class Request(object):
		def __init__(self, host, name, code):
			self.__host = host
			self.__name = name
			self.__code = code
		
		def __repr__(self):
			return '<Request(host={0})>'.format(self.__host)
		
		
		@property
		def host(self):
			return self.__host
		
		@property
		def name(self):
			return self.__name
		
		@property
		def code(self):
			return self.__code
		
	
	
	def __init__(self, **kwargs):
		self.__port = kwargs.get('port', DNS_REMOTE_PORT)
		self.__guid = kwargs.get('guid', generate_hex_string(DNS_REMOTE_GUID_LENGTH).upper())
		
		self.__list = {}
		self.__sock = None
	
	
	def open(self):
		self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__sock.bind(('', self.__port))
		self.__sock.listen(1)
	
	def close(self):
		if self.__sock:
			self.__sock.close()
			self.__sock = None
		
		while self.__list:
			self.__list.popitem()[1].close()
	
	
	def request(self):
		req = None
		
		if self.__sock:
			sock, addr = self.__sock.accept()
			
			field = parse_http_request(sock.recv(512))
			query = urlparse.parse_qs(urlparse.urlparse(field[1]).query)
			
			req = self.__class__.Request(addr, query['servicename'][0], query['pairingcode'][0])
			
			self.__list[req.name] = sock
		
		return req
	
	def respond(self, req, mode, **kwargs):
		sock = self.__list.pop(req.name, None)
		
		if sock:
			if mode is PAIR_VALID:
				cmpg = ''.join([chr(int(kwargs.get('guid', self.__guid)[i:i + 2], 16)) for i in range(0, 16, 2)])
				data = encode_msg({'cmpg': cmpg, 'cmnm': 'devicename', 'cmty': 'ipod'})
				
				sock.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\ncmpa{0}\r\n'.format(data))
			
			sock.close()
	
	
	@property
	def port(self):
		return self.__port
	
	@property
	def guid(self):
		return self.__guid
	

class DACPRemoteConnection(object):
	def __init__(self, **kwargs):
		pass
	


class DACPTouchableService(DNSService):
	def __init__(self, **kwargs):
		txt_record = {'Ver': '131072', 'DvSv': '1905', 'OSsi': '0xD97F', 'txtvers': '1'}
		
		txt_record['CtlN'] = kwargs.get('name', '')
		txt_record['DvTy'] = kwargs.get('type', 'iTunes')
		txt_record['DbId'] = kwargs.get('id', generate_hex_string(DNS_LIBRARY_ID_LENGTH).upper())
		
		DNSService.__init__(self, name=DNS_TOUCHABLE_NAME,
								  type=DNS_TOUCHABLE_TYPE,
								  port= DNS_TOUCHABLE_PORT,
								  txt_record=txt_record)
	

class DACPTouchableBrowser(DNSBrowser):
	def __init__(self, **kwargs):
		DNSBrowser.__init__(self, type=DNS_TOUCHABLE_TYPE)
		#data = decode_txt_record(txtrecord)
		#ip = socket.inet_ntoa(rdata)
	
	
	def on_added(self, service):
		print 'added:', service.name
	
	def on_removed(self, service):
		print 'removed:', service.name
	


class DACPTouchableServer(object):
	class Request(object):
		def __init__(self):
			pass
		
		def __repr__(self):
			return ''
		
	
	
	def __init__(self, **kwargs):
		pass
	
	
	def open(self):
		pass
	
	def close(self):
		pass
	

class DACPTouchableConnection(object):
	def __init__(self, **kwargs):
		self.__host = kwargs.get('host', 'localhost')
		self.__port = kwargs.get('port', DNS_TOUCHABLE_PORT)
		self.__guid = kwargs.get('guid', '')
		
		self.__conn = None
		self.__mlid = None
	
	
	def connect(self):
		self.close()
		
		self.__conn = httplib.HTTPConnection(self.__host, self.__port, False)
	
	def close(self):
		if self.__conn:
			self.__conn.close()
			self.__conn = None
	
	
	def is_alive(self):
		return bool(self.__conn)
	
	
	def login(self, **kwargs):
		guid = kwargs.get('guid', self.__guid)
		
		self.__conn.request("GET", "/login?pairing-guid=0x{0}".format(guid), None, {'Viewer-Only-Client': '1'})
		
		respond = self.__conn.getresponse()
		if respond and respond.status == 200:
			self.__mlid = Parser(respond.read()).int('mlid')
			return True
		
		else:
			self.close()
			return False
	
	
	def send_raw(self, raw):
		self.__conn.request('GET', '{0}&session-id={1}'.format(raw, self.__mlid), None, {'Viewer-Only-Client': '1'})
		
		respond = self.__conn.getresponse()
		if respond:
			if respond.status == 200:
				return respond.read()
			
			return respond.status
	
	def send_cmd(self, cmd, args={}):
		return self.send_raw('{0}?{1}'.format(cmd, urllib.urlencode(args)))
	
	
	@property
	def host(self):
		return self.__host
	
	@property
	def port(self):
		return self.__port
	
	@property
	def guid(self):
		return self.__guid
	
	@property
	def session_id(self):
		return self.__mlid
	

