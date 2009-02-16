import random
import select
import socket
import string
import urlparse
import struct

import pybonjour


BONJOUR_LIBRARY_NAME = 'Gamblor'
BONJOUR_LIBRARY_TYPE = '_touch-able._tcp'
BONJOUR_LIBRARY_PORT = 3689
BONJOUR_LIBRARY_ID_LENGTH = 64

BONJOUR_DEVICE_NAME = 'Pinchy'
BONJOUR_DEVICE_TYPE = '_touch-remote._tcp'
BONJOUR_DEVICE_PORT = 1024
BONJOUR_DEVICE_PAIR_LENGTH = 64
BONJOUR_DEVICE_GUID_LENGTH = 64


KEY_VALID = 0x01
KEY_INVALID = 0x02


def read_list(queue, size):
    p, queue[0:size] = ''.join(queue[0:size]), []
    return p

def generate_hex_string(bits):
    return hex(random.getrandbits(bits))[2:-1]

def encode_txt_record(record):
    return ''.join(['{0}{1}'.format(chr(len(i)), i) for i in map('{0[0]}={0[1]}'.format, record.iteritems())])

def decode_txt_record(record):
    q = list(record)
    d = {}
    
    while q:
        d.update([read_list(q, ord(read_list(q, 1))).split('=', 1)])
    
    return d

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



class BonjourService:
    def __init__(self, **kwargs):
        self.__name = kwargs.get('name')
        self.__regtype = kwargs.get('regtype')
        self.__port = kwargs.get('port')
        self.__txt_record = kwargs.get('txt_record', {})
        
        self.__sdref = None
    
    
    def _callback(self, sdref, flags, error, name, regtype, domain):
        if error != pybonjour.kDNSServiceErr_NoError:
            self.close()
    
    
    def register(self):
        self.close()
        
        self.__sdref = pybonjour.DNSServiceRegister(name=self.__name,
                                                    regtype=self.__regtype,
                                                    port=self.__port,
                                                    txtRecord=encode_txt_record(self.__txt_record),
                                                    callBack=self._callback)
        
        pybonjour.DNSServiceProcessResult(self.__sdref)
    
    def close(self):
        if self.__sdref:
            self.__sdref.close()
            self.__sdref = None
    

class BonjourBrowse:
    def __init__(self, **kwargs):
        self.__regtype = kwargs.get('regtype')
        self.__sdref = None
        
        self.timeout = 5
    
    
    def _query_record_callback(self, sdref, flags, interfaceindex, error, fullname, rrtype, rrclass, rdata, ttl):
        self.on_query(fullname, rrtype, rrclass, rdata, ttl)
    
    def _resolve_callback(self, sdref, flags, interfaceindex, error, fullname, hosttarget, port, txtrecord):
        if error != pybonjour.kDNSServiceErr_NoError:
            return
        
        if self.on_resolve(fullname, hosttarget, port, txtrecord):
            sdref = pybonjour.DNSServiceQueryRecord(interfaceIndex=interfaceindex,
                                                    fullname=hosttarget,
                                                    rrtype=pybonjour.kDNSServiceType_A,
                                                    callBack=self._query_record_callback)
            
            ready = select.select([sdref], [], [], 5)
            if sdref not in ready[0]:
                print 'Query record timed out'
                return
        
            pybonjour.DNSServiceProcessResult(sdref)
            sdref.close()
    
    def _browse_callback(self, sdref, flags, interfaceindex, error, servicename, regtype, replydomain):
        if error != pybonjour.kDNSServiceErr_NoError:
            self.close()
            return
        
        if not (flags & pybonjour.kDNSServiceFlagsAdd):
            print 'Service removed'
            return
        
        if self.on_result(servicename, regtype, replydomain):
            sdref = pybonjour.DNSServiceResolve(0,
                                                interfaceindex,
                                                servicename,
                                                regtype,
                                                replydomain,
                                                self._resolve_callback)
            
            pybonjour.DNSServiceProcessResult(sdref)
            sdref.close()
    
    
    def register(self):
        self.__sdref = pybonjour.DNSServiceBrowse(regtype=self.__regtype,
                                                  callBack=self._browse_callback)
    
    def close(self):
        if self.__sdref:
            self.__sdref.close()
            self.__sdref = None
    
    def update(self):
        if self.__sdref:
            ready = select.select([self.__sdref], [], [], self.timeout)
            if self.__sdref not in ready[0]:
                self.close()
            
            else:
                pybonjour.DNSServiceProcessResult(self.__sdref)
    
    
    def on_result(self, *args, **kwargs):
        return True
    
    def on_resolve(self, *args, **kwargs):
        return True
    
    def on_query(self, *args, **kwargs):
        pass
    


class DACPClient:
    def __init__(self, sock, addr, code, name):
        self.addr = addr
        self.code = code
        self.name = name
        self.sock = sock
    
    def __repr__(self):
        return '<DACPClient({addr}, {code})>'.format(addr=self.addr, code=self.code)
    


class DACPServiceLibrary(BonjourService):
    def __init__(self, **kwargs):
        txt_record = {'Ver': '131072', 'DvSv': '1905', 'OSsi': '0xD97F', 'txtvers': '1'}
        
        txt_record['CtlN'] = kwargs.get('name', '')
        txt_record['DvTy'] = kwargs.get('type', 'iTunes')
        txt_record['DbId'] = kwargs.get('id', generate_hex_string(BONJOUR_LIBRARY_ID_LENGTH).upper())
        
        BonjourService.__init__(self, name=BONJOUR_LIBRARY_NAME,
                                      regtype=BONJOUR_LIBRARY_TYPE,
                                      port= BONJOUR_LIBRARY_PORT,
                                      txt_record=txt_record)
    

class DACPBrowseLibrary(BonjourBrowse):
    def __init__(self, **kwargs):
        BonjourBrowse.__init__(self, regtype=BONJOUR_LIBRARY_TYPE)
        
        self.__active = ''
        self.__librarys = {}
    
    
    def on_result(self, *args, **kwargs):
        return True
    
    def on_resolve(self, fullname, hosttarget, port, txtrecord):
        data = decode_txt_record(txtrecord)
        if data['DbId'] not in self.__librarys:
            self.__active = data['DbId']
            self.__librarys[self.__active] = {'name': data['CtlN'], 'addr': ([], port)}
        
        return True
    
    def on_query(self, fullname, rrtype, rrclass, rdata, ttl):
        ip = socket.inet_ntoa(rdata)
        if ip not in self.__librarys[self.__active]['addr'][0]:
            self.__librarys[self.__active]['addr'][0].append(ip)
    
    
    def librarys(self):
        return self.__librarys.items()
    


class DACPServiceDevice(BonjourService):
    def __init__(self, **kwargs):
        self.__sock = None
        
        self.guid = kwargs.get('guid', generate_hex_string(BONJOUR_DEVICE_GUID_LENGTH))
        
        txt_record = {'RemV': '10000', 'RemN': 'Remote', 'txtvers': '1'}
        
        txt_record['DvNm'] = kwargs.get('name', '')
        txt_record['DvTy'] = kwargs.get('type', 'iPod')
        txt_record['Pair'] = kwargs.get('pair', generate_hex_string(BONJOUR_DEVICE_PAIR_LENGTH))
        
        BonjourService.__init__(self, name=BONJOUR_DEVICE_NAME,
                                      regtype=BONJOUR_DEVICE_TYPE,
                                      port= BONJOUR_DEVICE_PORT,
                                      txt_record=txt_record)
    
    
    def register(self):
        BonjourService.register(self)
        
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.bind(('', BONJOUR_DEVICE_PORT))
        self.__sock.listen(1)
    
    def close(self):
        BonjourService.close(self)
        
        if self.__sock:
            self.__sock.close()
            self.__sock = None
    
    
    def accept(self):
        if self.__sock:
            sock, addr = self.__sock.accept()
            query = urlparse.parse_qs(urlparse.urlparse(parse_http_request(sock.recv(512))[1]).query)
            
            return DACPClient(sock, addr, query['pairingcode'][0], query['servicename'][0])
        
        return None
    
    def respond(self, client, mode):
        if mode is KEY_VALID:
            values = {'cmpg': ''.join([chr(int(self.guid[i:i + 2], 16)) for i in range(0, 16, 2)]), 'cmnm': 'devicename', 'cmty': 'ipod'}
            encoded = ''
            
            for key, value in values.iteritems():
                encoded += '%s%s%s' % (key, struct.pack('>i', len(value)), value)
            
            header = 'cmpa%s' % (struct.pack('>i', len(encoded)))
            encoded = '%s%s' % (header, encoded)
            
            client.sock.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n{data}\r\n'.format(data=encoded))
        
        client.sock.close()
    

class DACPBrowseDevice(BonjourBrowse):
    def __init__(self, **kwargs):
        pass
    

