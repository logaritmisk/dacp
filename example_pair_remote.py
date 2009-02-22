import dacp


q = dacp.DACPRemoteServer()
p = dacp.DACPRemoteService(name='Rubelina')

try:
	q.open()
	p.register()
	
	print 'server-guid:', q.guid
	print 'service-name:', p.name
	print
	
	while True:
		c = q.request()
		q.respond(c, dacp.PAIR_VALID)
		
		print ' paired with:', c.addr[0]

except KeyboardInterrupt:
	print '^C for da win! Terminating this shit now...'

finally:
	p.close()
	q.close()
