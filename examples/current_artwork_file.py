#!/usr/bin/env python
import StringIO

import itunes


q = itunes.ITunesController(host='192.168.1.3')
q.connect()

if q.login(guid='E551AC288AC81AD3'):
	p = open('artwork.png', 'wb')
	p.write(q.artwork(320, 320))
	p.close()

q.close()
