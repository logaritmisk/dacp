import dacp


DACP_SERVICE_CODE='1717'


q = dacp.DACPRemoteServer()
p = dacp.DACPRemoteService(name='Rubelina')

try:
	q.open()
	p.register()
	
	print 'server-guid:', q.guid
	print 'service-name:', p.name
	print 'service-pair:', p.pair
	print 'service-code:', DACP_SERVICE_CODE
	print
	
	while True:
		c = q.request()
		
		if c.code == dacp.generate_pairing_code(p.pair, DACP_SERVICE_CODE):
			q.respond(c, dacp.PAIR_VALID)
			print ' paired with: %s, %s' % c.host
		
		else:
			q.respond(c, dacp.PAIR_INVALID)
			print ' wrong code: %s, %s' % c.host

except KeyboardInterrupt:
	print '^C for da win! Terminating this shit now...'

finally:
	p.close()
	q.close()
