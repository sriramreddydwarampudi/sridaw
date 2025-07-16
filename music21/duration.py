"""
Minimal duration implementation
"""

class Duration:
    def __init__(self, quarterLength=1.0):
        self.quarterLength = quarterLength
    
    def __repr__(self):
        return f"Duration({self.quarterLength})"