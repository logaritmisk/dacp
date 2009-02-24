import itunes


q = itunes.ITunesController(host='192.168.1.3')
q.connect()

if q.login(guid='E551AC288AC81AD3'):
	q.next_item()

q.close()
