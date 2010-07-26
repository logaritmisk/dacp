#!/usr/bin/env python
import dacp
import itunes


q = itunes.ITunesController(host='localhost')
q.connect()

if q.login(guid='95AAFD5039592871'):
	d = q.send_cmd('/databases', {'revision-number': '1'})
	i = dacp.Parser(d).int('miid')
	
	d = q.send_cmd('/databases/' + str(i) + '/containers', {'revision-number': '1'})
	p = dacp.Parser(d).array('mlit')
	
	for i in p:
		print i.int('miid'), i.string('minm')
	
	d = q.send_cmd('/databases/42/containers/34069/items', {'revision-number': '1', 'meta': 'dmap.itemname,dmap.itemid,daap.songartist,daap.songalbum', 'type': 'music', 'sort': 'name', 'include-sort-headers': '1', 'query': 'dmap.itemname:*Evil*'})
	s = dacp.Parser(d).array('mlit')
	
	print len(s)
	
	for i in s:
		print i.string('asal'), '-', i.string('minm')

else:
	print 'faild to connect to server...'

q.close()
