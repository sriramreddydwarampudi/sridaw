"""
Minimal note implementation
"""

from .duration import Duration
from .dynamics import Volume

class Pitch:
    def __init__(self, name_or_midi):
        if isinstance(name_or_midi, str):
            self.midi = self._name_to_midi(name_or_midi)
            self.name = name_or_midi
        else:
            self.midi = name_or_midi
            self.name = self._midi_to_name(name_or_midi)
    
    def _name_to_midi(self, name):
        """Convert note name to MIDI number"""
        note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        
        # Handle flats and sharps
        if 'b' in name:
            base_note = name[0]
            octave = int(name[-1])
            offset = -1
        elif '#' in name:
            base_note = name[0]
            octave = int(name[-1])
            offset = 1
        else:
            base_note = name[0]
            octave = int(name[-1])
            offset = 0
        
        return (octave + 1) * 12 + note_map[base_note] + offset
    
    def _midi_to_name(self, midi):
        """Convert MIDI number to note name"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi // 12 - 1
        note_index = midi % 12
        return f"{note_names[note_index]}{octave}"

class Note:
    def __init__(self, pitch=None, quarterLength=1.0, volume=None):
        if pitch is None:
            pitch = "C4"
        
        if isinstance(pitch, str) or isinstance(pitch, int):
            self.pitch = Pitch(pitch)
        else:
            self.pitch = pitch
            
        self.duration = Duration(quarterLength)
        self.volume = volume or Volume()
        self.offset = 0.0
    
    @property
    def notes(self):
        """For compatibility with chord interface"""
        return [self]
    
    def __repr__(self):
        return f"Note({self.pitch.name})"