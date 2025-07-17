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
        
        # Parse note name (e.g., "C4", "F#3", "Bb5")
        note_name = name[0].upper()
        octave = 4  # default octave
        accidental = 0
        
        # Extract octave and accidental
        rest = name[1:]
        if rest:
            if rest[0] in '#b':
                if rest[0] == '#':
                    accidental = 1
                elif rest[0] == 'b':
                    accidental = -1
                if len(rest) > 1:
                    try:
                        octave = int(rest[1:])
                    except:
                        octave = 4
            else:
                try:
                    octave = int(rest)
                except:
                    octave = 4
        
        base_midi = note_map.get(note_name, 0)
        return (octave + 1) * 12 + base_midi + accidental
    
    def _midi_to_name(self, midi_num):
        """Convert MIDI number to note name"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_num // 12) - 1
        note_index = midi_num % 12
        return f"{note_names[note_index]}{octave}"
    
    def __repr__(self):
        return f"Pitch({self.name})"

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