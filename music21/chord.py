"""
Minimal chord implementation
"""

from .note import Note, Pitch
from .duration import Duration
from .dynamics import Volume

class Chord:
    def __init__(self, pitches=None, quarterLength=1.0, volume=None):
        if pitches is None:
            pitches = ["C4", "E4", "G4"]
        
        self.notes = []
        for pitch in pitches:
            note = Note(pitch, quarterLength, volume)
            self.notes.append(note)
        
        self.duration = Duration(quarterLength)
        self.volume = volume or Volume()
        self.offset = 0.0
    
    def __repr__(self):
        note_names = [note.pitch.name for note in self.notes]
        return f"Chord({note_names})"