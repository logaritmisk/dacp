import StringIO

import pyglet

import itunes


q = itunes.ITunesController(host='192.168.1.3')
q.connect()

if q.login(guid='E551AC288AC81AD3'):
	i = pyglet.image.load('.png', file=StringIO.StringIO(q.artwork(320, 320)))
	w = pyglet.window.Window(width=320, height=320, resizable=False)
	
	@w.event
	def on_draw():
		w.clear()
		i.blit(0, 0)
	
	
	pyglet.app.run()

q.close()
