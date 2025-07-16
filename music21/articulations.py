"""
Minimal articulations implementation
"""

class Articulation:
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f"Articulation({self.name})"

class Staccato(Articulation):
    def __init__(self):
        super().__init__("staccato")

class Legato(Articulation):
    def __init__(self):
        super().__init__("legato")