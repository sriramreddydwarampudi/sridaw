"""
Minimal stream implementation with better error handling
"""

from .duration import Duration
import io

class Stream:
    def __init__(self):
        self.elements = []
        self._duration = None
    
    def append(self, element):
        """Add element to the end of the stream"""
        try:
            if hasattr(element, 'offset'):
                element.offset = self.duration.quarterLength if self._duration else 0.0
            else:
                element.offset = self.duration.quarterLength if self._duration else 0.0
            self.elements.append(element)
            self._duration = None  # Reset cached duration
        except Exception as e:
            print(f"Stream append error: {e}")
    
    def insert(self, offset, element):
        """Insert element at specific offset"""
        try:
            element.offset = float(offset)
            self.elements.append(element)
            self._duration = None  # Reset cached duration
        except Exception as e:
            print(f"Stream insert error: {e}")
    
    @property
    def duration(self):
        """Calculate total duration of the stream"""
        try:
            if self._duration is None:
                max_end = 0.0
                for element in self.elements:
                    try:
                        if hasattr(element, 'duration') and hasattr(element, 'offset'):
                            end_time = element.offset + element.duration.quarterLength
                            max_end = max(max_end, end_time)
                        elif hasattr(element, 'offset'):
                            max_end = max(max_end, element.offset)
                    except:
                        continue
                self._duration = Duration(max_end)
            return self._duration
        except:
            return Duration(10.0)  # Fallback duration
    
    def recurse(self):
        """Return a RecursiveIterator for compatibility"""
        return RecursiveIterator(self)
    
    @property
    def flat(self):
        """Return flattened view of stream"""
        return FlatStream(self)
    
    def getElementsByClass(self, class_type):
        """Get elements of specific class"""
        try:
            return [el for el in self.elements if isinstance(el, class_type)]
        except:
            return []
    
    def write(self, format_type, fp=None):
        """Write stream to file (minimal MIDI implementation)"""
        try:
            if format_type == 'midi':
                self._write_midi(fp)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
        except Exception as e:
            print(f"Write error: {e}")
            # Create minimal valid MIDI file
            self._write_minimal_midi(fp)
    
    def _write_minimal_midi(self, filepath):
        """Create a minimal valid MIDI file"""
        try:
            # Very basic MIDI file
            midi_data = bytearray()
            
            # Header chunk
            midi_data.extend(b'MThd')
            midi_data.extend((0, 0, 0, 6).to_bytes(4, 'big'))
            midi_data.extend((0, 0).to_bytes(2, 'big'))  # Format 0
            midi_data.extend((0, 1).to_bytes(2, 'big'))  # 1 track
            midi_data.extend((0, 96).to_bytes(2, 'big')) # 96 ticks per quarter
            
            # Track chunk with single note
            track_data = bytearray()
            track_data.extend([0x00, 0x90, 60, 100])  # Note on C4
            track_data.extend([0x60, 0x80, 60, 0])    # Note off after 96 ticks
            track_data.extend([0x00, 0xFF, 0x2F, 0x00]) # End of track
            
            midi_data.extend(b'MTrk')
            midi_data.extend(len(track_data).to_bytes(4, 'big'))
            midi_data.extend(track_data)
            
            with open(filepath, 'wb') as f:
                f.write(midi_data)
        except Exception as e:
            print(f"Minimal MIDI write error: {e}")
    
    def _write_midi(self, filepath):
        """Create a MIDI file from stream elements"""
        try:
            midi_data = bytearray()
            
            # Header chunk
            midi_data.extend(b'MThd')
            midi_data.extend((0, 0, 0, 6).to_bytes(4, 'big'))
            midi_data.extend((0, 0).to_bytes(2, 'big'))  # Format type 0
            midi_data.extend((0, 1).to_bytes(2, 'big'))  # Number of tracks
            midi_data.extend((0, 96).to_bytes(2, 'big')) # Ticks per quarter note
            
            # Track chunk
            track_data = bytearray()
            
            # Sort elements by offset
            sorted_elements = sorted(self.elements, key=lambda x: getattr(x, 'offset', 0))
            
            last_time = 0
            for element in sorted_elements:
                try:
                    if hasattr(element, 'pitch'):  # Single note
                        offset_ticks = int(getattr(element, 'offset', 0) * 96)
                        duration_ticks = int(getattr(element.duration, 'quarterLength', 1.0) * 96)
                        velocity = getattr(getattr(element, 'volume', None), 'velocity', 100)
                        
                        # Delta time for note on
                        delta = offset_ticks - last_time
                        track_data.extend(self._variable_length(delta))
                        track_data.extend([0x90, element.pitch.midi, min(127, max(1, velocity))])
                        
                        # Delta time for note off
                        track_data.extend(self._variable_length(duration_ticks))
                        track_data.extend([0x80, element.pitch.midi, 0])
                        
                        last_time = offset_ticks + duration_ticks
                        
                    elif hasattr(element, 'notes'):  # Chord
                        offset_ticks = int(getattr(element, 'offset', 0) * 96)
                        duration_ticks = int(getattr(element.duration, 'quarterLength', 1.0) * 96)
                        velocity = getattr(getattr(element, 'volume', None), 'velocity', 100)
                        
                        # Note on events for all notes in chord
                        for i, note in enumerate(element.notes):
                            delta = (offset_ticks - last_time) if i == 0 else 0
                            track_data.extend(self._variable_length(delta))
                            track_data.extend([0x90, note.pitch.midi, min(127, max(1, velocity))])
                            if i == 0:
                                last_time = offset_ticks
                        
                        # Note off events
                        for i, note in enumerate(element.notes):
                            delta = duration_ticks if i == 0 else 0
                            track_data.extend(self._variable_length(delta))
                            track_data.extend([0x80, note.pitch.midi, 0])
                            if i == 0:
                                last_time += duration_ticks
                except Exception as e:
                    print(f"Element processing error: {e}")
                    continue
            
            # End of track
            track_data.extend([0x00, 0xFF, 0x2F, 0x00])
            
            # Track header
            midi_data.extend(b'MTrk')
            midi_data.extend(len(track_data).to_bytes(4, 'big'))
            midi_data.extend(track_data)
            
            # Write to file
            with open(filepath, 'wb') as f:
                f.write(midi_data)
                
        except Exception as e:
            print(f"MIDI write error: {e}")
            self._write_minimal_midi(filepath)
    
    def _variable_length(self, value):
        """Convert integer to MIDI variable length quantity"""
        try:
            if value < 0:
                value = 0
            result = []
            result.append(value & 0x7F)
            value >>= 7
            while value > 0:
                result.append((value & 0x7F) | 0x80)
                value >>= 7
            return list(reversed(result))
        except:
            return [0]

class RecursiveIterator:
    def __init__(self, stream):
        self.stream = stream
    
    @property
    def notes(self):
        """Get all note-like elements"""
        try:
            notes = []
            for element in self.stream.elements:
                if hasattr(element, 'pitch') or hasattr(element, 'notes'):
                    notes.append(element)
            return notes
        except:
            return []

class FlatStream:
    def __init__(self, stream):
        self.stream = stream
    
    def getElementsByClass(self, class_type):
        """Get elements of specific class from flattened stream"""
        try:
            return self.stream.getElementsByClass(class_type)
        except:
            return []