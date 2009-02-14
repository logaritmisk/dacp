import time

import dacp


q = dacp.DACPService(name='Kalle')

print "pair:", q.pair
print "guid:", q.guid
print

q.open()
c = q.accept()

print "addr:", c.addr
print "code:", c.code
print "name:", c.name
print

#time.sleep(2.5)

q.respond(c, dacp.IS_VALID)
q.close()


q = dacp.ITunesController(host=c.host, port=c.port, guid=guid)
q.open()

if q.is_alive():
	q.next_song()
