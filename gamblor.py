import time

import dacp


q = dacp.ITunesController()

q.open()
print q.mlid
q.next_item()
q.close()

'''
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
'''
