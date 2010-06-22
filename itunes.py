import dacp


class ITunesController(dacp.DACPTouchableConnection):
    def __init__(self, **kwargs):
        dacp.DACPTouchableConnection.__init__(self, **kwargs)
    
    
    def play_pause(self):
        self.send_cmd('/ctrl-int/1/playpause', {})
    
    
    def next_item(self):
        self.send_cmd('/ctrl-int/1/nextitem', {})
    
    def prev_item(self):
        self.send_cmd('/ctrl-int/1/previtem', {})
    
    
    def shuffle(self, value=None):
        if not value:
            d = dacp.decode_msg(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dacp.shufflestate'})))
            return d['cmgt']['cash']
        
        if 0 <= value <= 1:
            self.send_cmd('/ctrl-int/1/setproperty', {'dacp.shufflestate': value})
    
    def repeat(self, value=None):
        if not value:
            d = dacp.decode_msg(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dacp.repeatstate'})))
            return d['cmgt']['carp']
        
        if 0 <= value <= 2:
            self.send_cmd('/ctrl-int/1/setproperty', {'dacp.repeatstate': value})
    
    def volume(self, value=None):
        if not value:
            d = dacp.decode_msg(list(self.send_cmd('/ctrl-int/1/getproperty', {'properties': 'dmcp.volume'})))
            return d['cmgt']['cmvo']
        
        if 0.0 <= value <= 100.0:
            self.send_cmd('/ctrl-int/1/setproperty?dmcp.volume', {'dmcp.volume': value})
    
    
    def artwork(self, min_w, min_h):
        return self.send_cmd('/ctrl-int/1/nowplayingartwork', {'mw': min_w, 'mh': min_h})
    

