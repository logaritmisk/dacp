import itunes


q = itunes.ITunesController(host='172.16.115.1')
q.connect()

if q.login(guid='33B9EE8B96627E26'):
	q.next_item()

q.close()
