import dacp


d = dacp.DACPServiceDevice(name='Ristorante')
d.register()

print d.guid

c = d.accept()
print c
d.respond(c, dacp.KEY_VALID)

d.close()

'''
p = dacp.DACPServiceLibrary(name='Nisse Hult')
p.register()

q = dacp.DACPBrowseLibrary(regtype='_touch-able._tcp')
q.register()

for i in xrange(10):
	q.update()

for k, v in q.librarys():
	print 'id:', k
	print 'name:', v['name']
	print 'addr:', v['addr']
	print

p.close()
q.close()
'''

