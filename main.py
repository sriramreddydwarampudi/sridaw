#!/usr/bin/env python3
"""
Music21 Visual DAW - Professional MIDI Visualization with Enhanced Syntax Highlighting
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Triangle
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.codeinput import CodeInput
from kivy.extras.highlight import PythonLexer
from pygments.token import Token

import os
import threading
import tempfile
import math
from collections import defaultdict

# Music21 imports
try:
    from music21 import stream, note, tempo, meter, key, chord, dynamics
    from music21 import expressions, articulations, scale, pitch
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    print("Install music21: pip install music21")

# Audio playback
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Install pygame: pip install pygame")

class CustomMusic21Lexer(PythonLexer):
    """Custom lexer for enhanced music21 syntax highlighting"""
    def get_tokens_unprocessed(self, text):
        # First get all tokens from PythonLexer
        for index, token, value in super().get_tokens_unprocessed(text):
            # Highlight music21 specific terms
            if token in Token.Name and value in ['stream', 'note', 'tempo', 'meter', 'key', 'chord', 
                                               'dynamics', 'expressions', 'articulations', 'repeat', 
                                               'instrument', 'metadata', 'layout', 'scale', 'pitch']:
                yield index, Token.Keyword, value
            elif token in Token.Name and value in ['Stream', 'Note', 'Rest', 'Chord', 'TempoIndication', 
                                                 'TimeSignature', 'KeySignature', 'MetronomeMark', 
                                                 'RehearsalMark', 'Dynamic', 'Expression', 'Articulation',
                                                 'Staccato', 'Accent', 'Tenuto', 'MajorScale']:
                yield index, Token.Name.Class, value
            elif token in Token.Name and value in ['quarterLength', 'offset', 'pitch', 'midi', 'volume',
                                                 'velocity', 'type', 'append', 'insert', 'flatten']:
                yield index, Token.Name.Attribute, value
            elif token in Token.Name and value in ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 
                                                  'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5',
                                                  'C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3']:
                yield index, Token.Literal.String, value
            else:
                yield index, token, value

class VisualPianoRoll(Widget):
    """Professional piano roll visualization with DAW-like features"""
    notes = ListProperty([])
    current_time = NumericProperty(0)
    is_playing = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid_size = 25
        self.octaves = 5  # C2 to C7
        self.note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.total_keys = self.octaves * 12
        
        # Set size
        self.width = 800
        self.height = self.total_keys * self.grid_size
        
        # Time tracking
        self.playback_speed = 0.5  # seconds per beat
        self.playback_clock = None
        
        # Bind properties to redraw
        self.bind(notes=self.draw_grid, pos=self.draw_grid, size=self.draw_grid, 
                 current_time=self.draw_grid, is_playing=self.draw_grid)
        Clock.schedule_once(self.draw_grid, 0.1)
    
    def draw_grid(self, *args):
        """Draw professional piano roll grid"""
        self.canvas.clear()
        
        with self.canvas:
            # Background
            Color(0.08, 0.08, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Piano keys on the left
            key_width = 50
            for i in range(self.total_keys):
                note_index = i % 12
                is_black = note_index in [1, 3, 6, 8, 10]
                octave = 2 + i // 12
                
                y = self.y + (self.total_keys - i - 1) * self.grid_size
                
                # White keys
                if not is_black:
                    Color(0.95, 0.95, 0.95, 1)
                    Rectangle(pos=(self.x, y), size=(key_width, self.grid_size))
                
                # Black keys
                if is_black:
                    Color(0.2, 0.2, 0.2, 1)
                    Rectangle(pos=(self.x, y), size=(key_width * 0.7, self.grid_size))
                
                # Note labels
                if not is_black:
                    Color(0.3, 0.3, 0.3, 1)
                    label_x = self.x + 5
                    label_y = y + self.grid_size / 2 - 7
                    label_text = f"{self.note_names[note_index]}{octave}"
                    
                    # Use a simple text rendering approach
                    Line(points=[label_x, label_y + 10, label_x + 15, label_y + 10], width=1)
                    Line(points=[label_x, label_y + 5, label_x + 10, label_y + 5], width=1)
            
            # Grid area
            grid_x = self.x + key_width
            grid_width = self.width - key_width
            
            # Vertical grid lines (time)
            num_bars = max(16, int(grid_width / (self.grid_size * 4)) + 1)
            for bar in range(num_bars + 1):
                for beat in range(4):
                    x = grid_x + (bar * 4 + beat) * self.grid_size
                    
                    # Bar line
                    if beat == 0:
                        Color(0.5, 0.5, 0.6, 1)
                        Line(points=[x, self.y, x, self.y + self.height], width=1.5)
                    # Beat line
                    else:
                        Color(0.3, 0.3, 0.4, 1)
                        Line(points=[x, self.y, x, self.y + self.height], width=1)
            
            # Horizontal grid lines (notes)
            for i in range(self.total_keys + 1):
                y = self.y + i * self.grid_size
                note_index = i % 12
                is_black = note_index in [1, 3, 6, 8, 10]
                
                if is_black:
                    Color(0.25, 0.25, 0.3, 1)
                else:
                    Color(0.35, 0.35, 0.4, 1)
                
                Line(points=[grid_x, y, self.x + self.width, y], width=1)
            
            # Draw notes with velocity-based coloring
            for note_data in self.notes:
                x = grid_x + note_data['time'] * self.grid_size
                y = self.y + (self.total_keys - note_data['pitch'] - 1) * self.grid_size
                w = note_data['duration'] * self.grid_size
                h = self.grid_size
                
                # Velocity-based color (brighter = higher velocity)
                velocity = note_data.get('velocity', 100)
                velocity_factor = velocity / 127.0
                r = 0.1 + 0.6 * velocity_factor
                g = 0.4 + 0.4 * velocity_factor
                b = 0.8
                
                Color(r, g, b, 0.9)
                Rectangle(pos=(x, y), size=(w, h), radius=[3, 3, 3, 3])
                
                # Note border
                Color(0.2, 0.2, 0.3, 1)
                Line(rounded_rectangle=(x, y, w, h, 3), width=1)
                
                # Note name for long notes
                if w > 30:
                    Color(1, 1, 1, 0.8)
                    # Simplified text rendering
                    note_name = self.note_names[note_data['pitch'] % 12]
                    octave = 2 + note_data['pitch'] // 12
                    text = f"{note_name}{octave}"
                    
                    # Draw note name as lines
                    mid_x = x + w/2 - 5
                    mid_y = y + h/2
                    Line(points=[mid_x, mid_y + 5, mid_x + 5, mid_y + 5], width=1)
                    Line(points=[mid_x, mid_y, mid_x + 5, mid_y], width=1)
            
            # Playhead
            if self.is_playing:
                playhead_x = grid_x + self.current_time * self.grid_size
                Color(1, 0.2, 0.2, 1)
                Line(points=[playhead_x, self.y, playhead_x, self.y + self.height], width=2)
                
                # Playhead triangle
                points = [playhead_x, self.y + self.height, 
                          playhead_x - 5, self.y + self.height - 10,
                          playhead_x + 5, self.y + self.height - 10]
                Color(1, 0.2, 0.2, 1)
                Triangle(points=points)
    
    def clear_notes(self):
        """Clear all notes"""
        self.notes = []
    
    def update_from_stream(self, stream_obj):
        """Update piano roll from music21 stream"""
        if not MUSIC21_AVAILABLE or not stream_obj:
            return
        
        self.notes = []
        max_time = 0
        
        # Process all notes in the stream
        for element in stream_obj.flatten().notesAndRests:
            if hasattr(element, 'pitch'):  # Handle both Note and Chord
                if hasattr(element, 'notes'):  # It's a Chord
                    for n in element.notes:
                        self._add_note_to_roll(n, element.offset, element.quarterLength)
                else:  # It's a Note
                    self._add_note_to_roll(element, element.offset, element.quarterLength)
                
                max_time = max(max_time, element.offset + element.quarterLength)
        
        # Update width based on content
        self.width = max(800, (max_time / 0.5) * self.grid_size + 200)
        self.draw_grid()
    
    def _add_note_to_roll(self, note_obj, offset, duration):
        """Add a single note to piano roll visualization"""
        try:
            midi_pitch = note_obj.pitch.midi
            pitch_index = midi_pitch - 36  # Start from C2 (MIDI 36)
            
            # Convert music21 timing to grid units
            time_pos = offset / 0.5  # 0.5 quarter notes per grid unit
            duration = duration / 0.5
            
            # Get velocity (volume)
            velocity = 100
            if hasattr(note_obj, 'volume') and hasattr(note_obj.volume, 'velocity'):
                velocity = note_obj.volume.velocity
            elif hasattr(note_obj, 'volume') and hasattr(note_obj.volume, 'velocityScalar'):
                velocity = note_obj.volume.velocityScalar * 127
            
            # Only show notes within visible range
            if 0 <= pitch_index < self.total_keys:
                self.notes.append({
                    'time': time_pos,
                    'pitch': pitch_index,
                    'duration': duration,
                    'midi_note': midi_pitch,
                    'velocity': velocity
                })
        except Exception as e:
            print(f"Error adding note to roll: {e}")
    
    def start_playback(self, stream_length):
        """Start playback visualization"""
        if self.is_playing:
            self.stop_playback()
            
        self.is_playing = True
        self.current_time = 0
        self.playback_speed = 0.5  # seconds per beat
        self.playback_clock = Clock.schedule_interval(
            lambda dt: self.update_playback(stream_length), 
            self.playback_speed / 4  # update 4 times per beat
        )
    
    def update_playback(self, stream_length):
        """Update playback position"""
        self.current_time += 0.25  # 1/4 beat per update
        if self.current_time > stream_length / 0.5:
            self.stop_playback()
    
    def stop_playback(self):
        """Stop playback visualization"""
        self.is_playing = False
        if self.playback_clock:
            self.playback_clock.cancel()
            self.playback_clock = None

class Music21CodeEditor(CodeInput):
    """Enhanced code editor with music21-specific syntax highlighting"""
    piano_roll = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lexer = CustomMusic21Lexer()
        self.style_name = 'monokai'
        self.background_color = (0.1, 0.1, 0.12, 1)
        self.foreground_color = (0.9, 0.9, 0.9, 1)
        self.cursor_color = (1, 1, 1, 1)
        self.font_name = 'DejaVuSansMono'
        self.font_size = 14
        self.text = self.get_initial_code()
        
        # Line numbers
        self.line_number = 1
        self.bind(text=self.update_line_number)
    
    def update_line_number(self, instance, value):
        """Update line number display"""
        self.line_number = len(value.splitlines())
    
    def get_initial_code(self):
        """Return example music21 code with more features"""
        return """# Music21 Visual DAW - Example Composition
from music21 import stream, note, tempo, chord, dynamics, expressions, articulations

# Create a stream with tempo and dynamics
s = stream.Stream()
s.append(tempo.MetronomeMark(number=120))
s.append(dynamics.Dynamic('mf'))

# Melody with articulations
melody = [
    note.Note('C4', quarterLength=0.5),
    note.Note('E4', quarterLength=0.5),
    note.Note('G4', quarterLength=0.5),
    note.Note('C5', quarterLength=0.5),
    note.Note('A4', quarterLength=0.5),
    note.Note('G4', quarterLength=0.5),
    note.Note('E4', quarterLength=0.5),
    note.Note('C4', quarterLength=1.0)
]

# Add staccato articulation to some notes
melody[0].articulations.append(articulations.Staccato())
melody[2].articulations.append(articulations.Staccato())
melody[4].articulations.append(articulations.Staccato())
melody[6].articulations.append(articulations.Staccato())

# Add accent to strong beats
melody[3].articulations.append(articulations.Accent())
melody[7].articulations.append(articulations.Accent())

# Add melody to stream with increasing volume
for i, n in enumerate(melody):
    n.volume.velocity = min(110, 80 + i*5)
    s.insert(i * 0.5, n)

# Chord accompaniment
chords = [
    chord.Chord(['C3', 'E3', 'G3'], quarterLength=1.0),
    chord.Chord(['A2', 'C3', 'E3'], quarterLength=1.0),
    chord.Chord(['F2', 'A2', 'C3'], quarterLength=1.0),
    chord.Chord(['G2', 'B2', 'D3'], quarterLength=1.0)
]

# Add chords with decreasing volume
for i, c in enumerate(chords):
    c.volume.velocity = max(60, 100 - i*10)
    s.insert(i * 2.0, c)

# Final cadence
cadence = [
    chord.Chord(['G3', 'B3', 'D4'], quarterLength=0.5),
    chord.Chord(['C4', 'E4', 'G4'], quarterLength=0.5)
]

for i, c in enumerate(cadence):
    s.insert(8.0 + i * 0.5, c)

# Set result for visualization and playback
result = s

"""

class SimpleDAWApp(App):
    """Main application with enhanced visualization"""
    
    def build(self):
        self.title = "Music21 Visual DAW"
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical')
        
        # Controls
        controls = BoxLayout(size_hint_y=0.08, spacing=10, padding=10)
        
        run_btn = Button(text='Run & Visualize', background_color=(0.2, 0.6, 0.9, 1))
        play_btn = Button(text='Play', background_color=(0.3, 0.8, 0.3, 1))
        stop_btn = Button(text='Stop', background_color=(0.9, 0.3, 0.3, 1))
        clear_btn = Button(text='Reset', background_color=(0.9, 0.6, 0.2, 1))
        export_btn = Button(text='Export MIDI', background_color=(0.7, 0.4, 0.9, 1))
        
        run_btn.bind(on_press=self.run_code)
        play_btn.bind(on_press=self.play_music)
        stop_btn.bind(on_press=self.stop_music)
        clear_btn.bind(on_press=self.clear_all)
        export_btn.bind(on_press=self.export_midi)
        
        controls.add_widget(run_btn)
        controls.add_widget(play_btn)
        controls.add_widget(stop_btn)
        controls.add_widget(clear_btn)
        controls.add_widget(export_btn)
        
        # Content area
        content = BoxLayout(orientation='vertical')
        
        # Piano roll in scroll view
        piano_layout = BoxLayout(orientation='vertical', size_hint_y=0.4)
        piano_layout.add_widget(Label(text='MIDI Visualization - Professional Piano Roll', 
                                     size_hint_y=0.08, color=(0.8, 0.8, 1, 1),
                                     bold=True, font_size=14))
        
        scroll_view = ScrollView(do_scroll_x=True, do_scroll_y=True)
        self.piano_roll = VisualPianoRoll(size_hint=(None, None))
        scroll_view.add_widget(self.piano_roll)
        piano_layout.add_widget(scroll_view)
        
        # Code editor
        code_layout = BoxLayout(orientation='vertical', size_hint_y=0.6)
        code_layout.add_widget(Label(text='Music21 Code Editor - Enhanced Syntax Highlighting', 
                                    size_hint_y=0.08, color=(0.8, 0.8, 1, 1),
                                    bold=True, font_size=14))
        
        self.code_editor = Music21CodeEditor()
        self.code_editor.piano_roll = self.piano_roll
        code_layout.add_widget(self.code_editor)
        
        content.add_widget(piano_layout)
        content.add_widget(code_layout)
        
        # Status
        self.status = Label(text='Ready', size_hint_y=0.04, color=(0.7, 0.7, 1, 1))
        
        # Assemble
        main_layout.add_widget(controls)
        main_layout.add_widget(content)
        main_layout.add_widget(self.status)
        
        # Initialize
        self.current_stream = None
        self.is_playing = False
        self.init_audio()
        
        return main_layout
    
    def init_audio(self):
        """Initialize audio"""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                self.status.text = "Audio system ready"
            except:
                self.status.text = "Audio initialization failed"
        else:
            self.status.text = "Audio disabled (install pygame)"
    
    def run_code(self, btn):
        """Run code editor content and update visualization"""
        try:
            if not MUSIC21_AVAILABLE:
                self.status.text = "Music21 not available"
                return
            
            # Create execution environment
            exec_globals = {
                'stream': stream,
                'note': note,
                'tempo': tempo,
                'meter': meter,
                'key': key,
                'chord': chord,
                'dynamics': dynamics,
                'expressions': expressions,
                'articulations': articulations
            }
            exec_locals = {}
            
            # Execute code
            exec(self.code_editor.text, exec_globals, exec_locals)
            
            # Check for result
            if 'result' in exec_locals:
                self.current_stream = exec_locals['result']
                note_count = len(self.current_stream.flatten().notesAndRests)
                self.status.text = f"Code executed - {note_count} notes visualized"
                self.piano_roll.update_from_stream(self.current_stream)
            else:
                self.status.text = "Code executed (no 'result' variable found)"
                
        except Exception as e:
            self.status.text = f"Error: {str(e)}"
            # Clear visualization on error
            self.piano_roll.clear_notes()
    
    def play_music(self, btn):
        """Play current music with visualization"""
        if self.is_playing:
            return
        
        if self.current_stream and len(self.current_stream.flatten().notesAndRests) > 0:
            self.is_playing = True
            self.status.text = "Playing with visualization..."
            
            # Calculate stream length
            last_element = max(self.current_stream.flatten().notesAndRests, 
                              key=lambda x: x.offset + x.quarterLength)
            stream_length = last_element.offset + last_element.quarterLength
            
            # Start visualization
            self.piano_roll.start_playback(stream_length)
            
            # Start audio playback in separate thread
            threading.Thread(target=self.play_stream, args=(self.current_stream,), daemon=True).start()
        else:
            self.status.text = "No music to play"
    
    def play_stream(self, stream_obj):
        """Play music21 stream"""
        try:
            if MUSIC21_AVAILABLE and PYGAME_AVAILABLE:
                # Create temp MIDI file
                temp_file = os.path.join(tempfile.gettempdir(), "temp_playback.mid")
                stream_obj.write('midi', fp=temp_file)
                
                # Play with pygame
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                # Wait for finish
                while pygame.mixer.music.get_busy() and self.is_playing:
                    pygame.time.wait(100)
                
                # Cleanup
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        except Exception as e:
            print(f"Play error: {e}")
        finally:
            Clock.schedule_once(self.reset_play, 0)
    
    def reset_play(self, dt):
        """Reset play state"""
        self.is_playing = False
        self.piano_roll.stop_playback()
        self.status.text = "Playback finished"
    
    def stop_music(self, btn):
        """Stop playback and visualization"""
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()
        self.is_playing = False
        self.piano_roll.stop_playback()
        self.status.text = "Playback stopped"
    
    def clear_all(self, btn):
        """Reset everything"""
        self.code_editor.text = self.code_editor.get_initial_code()
        self.piano_roll.clear_notes()
        self.piano_roll.stop_playback()
        self.current_stream = None
        self.status.text = "Reset to initial state"
    
    def export_midi(self, btn):
        """Export as MIDI"""
        try:
            if self.current_stream and MUSIC21_AVAILABLE:
                filename = "composition.mid"
                self.current_stream.write('midi', fp=filename)
                self.status.text = f"Exported: {filename}"
            else:
                self.status.text = "Nothing to export"
                
        except Exception as e:
            self.status.text = f"Export error: {e}"

if __name__ == '__main__':
    SimpleDAWApp().run()
