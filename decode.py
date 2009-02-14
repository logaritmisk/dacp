import struct
import re


group = ['cmst','mlog','agal','mlcl','mshl','mlit','abro','abar','apso','caci','avdb','cmgt','aply','adbs','cmpa']
binary = re.compile('[^\x20-\x7e]')


def read(queue, size):
	pull = ''.join(queue[0:size])
	del queue[0:size]
	return pull


def as_hex(s):
	return ''.join([ "%02x" % ord(c) for c in s ])

def as_byte(s):
	return struct.unpack('>B', s)[0]

def as_int(s):
	return struct.unpack('>I', s)[0]

def as_long(s):
	return struct.unpack('>Q', s)[0]


def decode(raw, handle):
	data = {}
	while handle >= 8:
		# read word data type and length
		ptype = read(raw, 4)
		plen = as_int(read(raw, 4))
		handle -= 8 + plen
		
		# recurse into groups
		if ptype in group:
			data[ptype] = decode(raw, plen)
			continue
		
		# read and parse data
		pdata = read(raw, plen)
		
		nice = as_hex(pdata)
		if plen == 1: nice = as_byte(pdata)
		if plen == 4: nice = as_int(pdata)
		if plen == 8: nice = as_long(pdata)
		
		if binary.search(pdata) is None:
			nice = pdata
		
		data[ptype] = nice
	
	return data

