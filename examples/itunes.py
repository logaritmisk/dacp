import dacp


class ITunesController(dacp.DACPTouchableConnection):
    def __init__(self, **kwargs):
        dacp.DACPTouchableConnection.__init__(self, **kwargs)
        
        self._cmsr = 1
    
    
    def play_pause(self):
        self.send_cmd('/ctrl-int/1/playpause')
    
    
    def next_item(self):
        self.send_cmd('/ctrl-int/1/nextitem')
    
    def prev_item(self):
        self.send_cmd('/ctrl-int/1/previtem')
    
    
    def shuffle(self, value=None):
        if not value:
            d = dacp.Parser(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dacp.shufflestate'})))
            return d.int('cash')
        
        if 0 <= value <= 1:
            self.send_cmd('/ctrl-int/1/setproperty', {'dacp.shufflestate': value})
    
    def repeat(self, value=None):
        if not value:
            d = dacp.Parser(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dacp.repeatstate'})))
            return d.int('carp')
        
        if 0 <= value <= 2:
            self.send_cmd('/ctrl-int/1/setproperty', {'dacp.repeatstate': value})
    
    def volume(self, value=None):
        if not value:
            d = dacp.Parser(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dmcp.volume'})))
            return d.int('cmvo')
        
        if 0.0 <= value <= 100.0:
            self.send_cmd('/ctrl-int/1/setproperty?dmcp.volume', {'dmcp.volume': value})
    
    
    def artwork(self, min_w, min_h):
        return self.send_cmd('/ctrl-int/1/nowplayingartwork', {'mw': min_w, 'mh': min_h})
    
    
    def status(self, **kwargs):
        if kwargs.get('wait', False):
            rev = self._cmsr
        
        else:
            rev = 1
        
        d = dacp.Parser(self.send_cmd('/ctrl-int/1/playstatusupdate', {'revision-number': rev}))
        self._cmsr = d.int('cmsr')
		
        return d
    
    
    @property
    def revision_number(self):
        return self._cmsr
    

