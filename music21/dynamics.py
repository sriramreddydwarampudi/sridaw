"""
Minimal dynamics implementation
"""

class Volume:
    def __init__(self, velocity=100):
        self.velocity = velocity
    
    def __repr__(self):
        return f"Volume(velocity={self.velocity})"

class Dynamic:
    def __init__(self, value='mf'):
        self.value = value
        self.offset = 0.0
    
    def __repr__(self):
        return f"Dynamic({self.value})"