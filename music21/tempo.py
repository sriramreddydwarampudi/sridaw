"""
Minimal tempo implementation
"""

class MetronomeMark:
    def __init__(self, number=120):
        self.number = number
        self.offset = 0.0
    
    def __repr__(self):
        return f"MetronomeMark(number={self.number})"