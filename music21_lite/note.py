class Note:
    def __init__(self, name=None, midi=None, quarterLength=1.0):
        self.name = name
        self.midi = midi
        self.quarterLength = quarterLength
        self.offset = 0
        self.volume = type('vol', (), {'velocity': 64})()