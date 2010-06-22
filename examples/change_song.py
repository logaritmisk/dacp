#!/usr/bin/env python
import itunes


q = itunes.ITunesController(host='localhost')
q.connect()

if q.login(guid='95AAFD5039592871'):
	q.next_item()

else:
	print('faild to connect to server...')

q.close()
