"""
Minimal stream implementation
"""

from .duration import Duration
import io

class Stream:
    def __init__(self):
        self.elements = []
        self._duration = None
    
    def append(self, element):
        """Add element to the end of the stream"""
        if hasattr(element, 'offset'):
            element.offset = self.duration.quarterLength if self._duration else 0.0
        else:
            element.offset = self.duration.quarterLength if self._duration else 0.0
        self.elements.append(element)
        self._duration = None  # Reset cached duration
    
    def insert(self, offset, element):
        """Insert element at specific offset"""
        element.offset = offset
        self.elements.append(element)
        self._duration = None  # Reset cached duration
    
    @property
    def duration(self):
        """Calculate total duration of the stream"""
        if self._duration is None:
            max_end = 0.0
            for element in self.elements:
                if hasattr(element, 'duration') and hasattr(element, 'offset'):
                    end_time = element.offset + element.duration.quarterLength
                    max_end = max(max_end, end_time)
                elif hasattr(element, 'offset'):
                    max_end = max(max_end, element.offset)
            self._duration = Duration(max_end)
        return self._duration
    
    def recurse(self):
        """Return a RecursiveIterator for compatibility"""
        return RecursiveIterator(self)
    
    @property
    def flat(self):
        """Return flattened view of stream"""
        return FlatStream(self)
    
    def getElementsByClass(self, class_type):
        """Get elements of specific class"""
        return [el for el in self.elements if isinstance(el, class_type)]
    
    def write(self, format_type, fp=None):
        """Write stream to file (minimal MIDI implementation)"""
        if format_type == 'midi':
            self._write_midi(fp)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _write_midi(self, filepath):
        """Create a minimal MIDI file"""
        # This is a very basic MIDI file creation
        # For a real implementation, you'd want to use a proper MIDI library
        
        # MIDI file header
        midi_data = bytearray()
        
        # Header chunk
        midi_data.extend(b'MThd')  # Header chunk type
        midi_data.extend((0, 0, 0, 6).to_bytes(4, 'big'))  # Header length
        midi_data.extend((0, 0).to_bytes(2, 'big'))  # Format type 0
        midi_data.extend((0, 1).to_bytes(2, 'big'))  # Number of tracks
        midi_data.extend((0, 96).to_bytes(2, 'big'))  # Ticks per quarter note
        
        # Track chunk
        track_data = bytearray()
        
        # Convert notes to MIDI events
        for element in sorted(self.elements, key=lambda x: getattr(x, 'offset', 0)):
            if hasattr(element, 'pitch'):  # Note
                offset_ticks = int(element.offset * 96)  # Convert to ticks
                duration_ticks = int(element.duration.quarterLength * 96)
                
                # Note on event
                track_data.extend(self._variable_length(offset_ticks))
                track_data.extend([0x90, element.pitch.midi, getattr(element.volume, 'velocity', 100)])
                
                # Note off event
                track_data.extend(self._variable_length(duration_ticks))
                track_data.extend([0x80, element.pitch.midi, 0])
            
            elif hasattr(element, 'notes'):  # Chord
                offset_ticks = int(element.offset * 96)
                duration_ticks = int(element.duration.quarterLength * 96)
                
                for i, note in enumerate(element.notes):
                    # Note on events (simultaneous for chord)
                    delta_time = offset_ticks if i == 0 else 0
                    track_data.extend(self._variable_length(delta_time))
                    track_data.extend([0x90, note.pitch.midi, getattr(element.volume, 'velocity', 100)])
                
                # Note off events
                for i, note in enumerate(element.notes):
                    delta_time = duration_ticks if i == 0 else 0
                    track_data.extend(self._variable_length(delta_time))
                    track_data.extend([0x80, note.pitch.midi, 0])
        
        # End of track
        track_data.extend([0x00, 0xFF, 0x2F, 0x00])
        
        # Track header
        midi_data.extend(b'MTrk')
        midi_data.extend(len(track_data).to_bytes(4, 'big'))
        midi_data.extend(track_data)
        
        # Write to file
        with open(filepath, 'wb') as f:
            f.write(midi_data)
    
    def _variable_length(self, value):
        """Convert integer to MIDI variable length quantity"""
        result = []
        result.append(value & 0x7F)
        value >>= 7
        while value > 0:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        return list(reversed(result))

class RecursiveIterator:
    def __init__(self, stream):
        self.stream = stream
    
    @property
    def notes(self):
        """Get all note-like elements"""
        notes = []
        for element in self.stream.elements:
            if hasattr(element, 'pitch') or hasattr(element, 'notes'):
                notes.append(element)
        return notes

class FlatStream:
    def __init__(self, stream):
        self.stream = stream
    
    def getElementsByClass(self, class_type):
        """Get elements of specific class from flattened stream"""
        return self.stream.getElementsByClass(class_type)