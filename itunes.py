import dacp


class ITunesController(dacp.DACPTouchableConnection):
    def __init__(self, **kwargs):
        dacp.DACPTouchableConnection.__init__(self, **kwargs)
    
    
    def play_pause(self):
        self.send('/ctrl-int/1/playpause', {})
    
    
    def next_item(self):
        self.send('/ctrl-int/1/nextitem', {})
    
    def prev_item(self):
        self.send('/ctrl-int/1/previtem', {})
    
    
    def shuffle(self, value=None):
        if not value:
            return self.send('/ctrl-int/1/getproperty', {'properties': 'dacp.shufflestate'})['cmgt']['cash']
        
        if 0 <= value <= 1:
            self.send('/ctrl-int/1/setproperty', {'dacp.shufflestate': value})
        
        return None
    
    def repeat(self, value=None):
        if not value:
            return self.send('/ctrl-int/1/getproperty', {'properties': 'dacp.repeatstate'})['cmgt']['carp']
        
        if 0 <= value <= 2:
            self.send('/ctrl-int/1/setproperty', {'dacp.repeatstate': value})
        
        return None
    
    def volume(self, value=None):
        if not value:
            return self.send('/ctrl-int/1/getproperty', {'properties': 'dmcp.volume'})['cmgt']['cmvo']
        
        if 0.0 <= value <= 100.0:
            self.send('/ctrl-int/1/setproperty?dmcp.volume', {'dmcp.volume': value})
        
        return None
    

