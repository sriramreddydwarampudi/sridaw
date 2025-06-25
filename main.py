#!/usr/bin/env python3
"""
SriDAW - Digital Audio Workstation
A Kivy-based DAW with music21 integration, piano roll, and MIDI capabilities
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, StringProperty, BooleanProperty

import os
import threading
import tempfile
from pathlib import Path

# Music21 imports
try:
    from music21 import stream, note, pitch, duration, tempo, meter, key, scale
    from music21 import midi as music21_midi
    from music21.midi import realtime as rt
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    print("Warning: music21 not available. Install with: pip install music21")

# Audio playback (optional, fallback to basic MIDI)
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available for audio. Install with: pip install pygame")

class PianoKey(Button):
    """Individual piano key widget"""
    def __init__(self, note_name, is_black=False, **kwargs):
        super().__init__(**kwargs)
        self.note_name = note_name
        self.is_black = is_black
        self.background_color = (0.2, 0.2, 0.2, 1) if is_black else (1, 1, 1, 1)
        self.color = (1, 1, 1, 1) if is_black else (0, 0, 0, 1)
        self.text = note_name
        self.size_hint_y = 0.6 if is_black else 1.0

class PianoRoll(Widget):
    """Piano roll editor widget"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notes = []  # List of note objects
        self.grid_width = 20
        self.grid_height = 15
        self.selected_note = None
        self.drawing = False
        
        # Bind events (remove old bindings)
        # Events will be handled by the overridden methods
        
        # Draw initial grid
        Clock.schedule_once(lambda dt: self.draw_grid(), 0.1)
    
    def draw_grid(self):
        """Draw the piano roll grid"""
        try:
            self.canvas.clear()
            with self.canvas:
                # Background
                Color(0.1, 0.1, 0.1, 1)
                Rectangle(pos=self.pos, size=self.size)
                
                # Grid lines
                Color(0.3, 0.3, 0.3, 1)
                # Vertical lines (time)
                if self.width > 0 and self.height > 0:
                    for x in range(0, int(self.width), self.grid_width):
                        Line(points=[x, 0, x, self.height], width=1)
                    
                    # Horizontal lines (pitch)
                    for y in range(0, int(self.height), self.grid_height):
                        Line(points=[0, y, self.width, y], width=1)
                
                # Draw notes
                self.draw_notes()
        except Exception as e:
            print(f"Error drawing grid: {e}")
    
    def draw_notes(self):
        """Draw all notes on the piano roll"""
        try:
            with self.canvas:
                Color(0.2, 0.7, 0.2, 0.8)  # Green notes
                for note_data in self.notes:
                    x = note_data['time'] * self.grid_width
                    y = note_data['pitch'] * self.grid_height
                    w = note_data['duration'] * self.grid_width
                    h = max(2, self.grid_height - 2)  # Ensure minimum height
                    if w > 0 and h > 0:  # Only draw if dimensions are valid
                        Rectangle(pos=(x, y), size=(w, h))
        except Exception as e:
            print(f"Error drawing notes: {e}")
    
    def on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            # Convert touch position to grid coordinates
            grid_x = int((touch.pos[0] - self.x) // self.grid_width)
            grid_y = int((touch.pos[1] - self.y) // self.grid_height)
            
            # Add new note
            new_note = {
                'time': grid_x,
                'pitch': grid_y,
                'duration': 2,  # Default duration
                'velocity': 80
            }
            self.notes.append(new_note)
            self.drawing = True
            self.draw_grid()
            
            # Play note sound when added
            self.play_note_sound(grid_y)
            return True
        return False
    
    def on_touch_move(self, instance, touch):
        if self.drawing and self.collide_point(*touch.pos):
            # Extend note duration while dragging
            if self.notes:
                grid_x = int((touch.pos[0] - self.x) // self.grid_width)
                last_note = self.notes[-1]
                last_note['duration'] = max(1, grid_x - last_note['time'])
                self.draw_grid()
    
    def on_touch_up(self, instance, touch):
        self.drawing = False
    
    def play_note_sound(self, grid_pitch):
        """Play sound for a note at given grid pitch"""
        try:
            if MUSIC21_AVAILABLE:
                # Convert grid pitch to MIDI note
                midi_note = 60 + (grid_pitch - 20)  # C4 = 60
                midi_note = max(21, min(127, midi_note))  # Clamp to valid MIDI range
                
                # Create and play note
                n = note.Note(midi=midi_note)
                n.quarterLength = 0.5
                s = stream.Stream()
                s.append(n)
                
                # Quick playback
                self.parent.parent.parent.parent.play_stream_quick(s)
        except Exception as e:
            print(f"Error playing note: {e}")
    
    def clear_notes(self):
        """Clear all notes"""
        self.notes = []
        self.draw_grid()
    
    def get_music21_stream(self):
        """Convert piano roll notes to music21 stream"""
        if not MUSIC21_AVAILABLE:
            return None
        
        s = stream.Stream()
        s.append(tempo.TempoIndication(number=120))
        s.append(meter.TimeSignature('4/4'))
        s.append(key.KeySignature(0))
        
        # Convert grid notes to music21 notes
        for note_data in self.notes:
            # Convert grid pitch to MIDI note (C4 = 60)
            midi_note = 60 + (note_data['pitch'] - 20)  # Adjust offset as needed
            
            # Create note
            n = note.Note(midi=midi_note)
            n.quarterLength = note_data['duration'] * 0.25  # Convert grid to quarter notes
            n.volume.velocity = note_data['velocity']
            
            # Set offset (timing)
            n.offset = note_data['time'] * 0.25
            
            s.append(n)
        
        return s


class CodeEditor(TextInput):
    """Enhanced code editor with music21 syntax highlighting and autocompletion"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = True
        self.background_color = (0.1, 0.1, 0.1, 1)
        self.foreground_color = (1, 1, 1, 1)
        self.font_name = 'Courier'  # Monospace font for code
        self.font_size = 14
        self.cursor_color = (1, 1, 1, 1)
        self.hint_text = "Write your music21 code here..."
        
        # Syntax highlighting colors
        self.keyword_color = (0.8, 0.2, 0.6, 1)    # Pink
        self.string_color = (0.2, 0.8, 0.2, 1)       # Green
        self.comment_color = (0.5, 0.5, 0.5, 1)      # Gray
        self.function_color = (0.4, 0.6, 1.0, 1)     # Blue
        self.class_color = (0.8, 0.6, 0.2, 1)        # Orange
        self.constant_color = (0.8, 0.8, 0.2, 1)     # Yellow
        
        # Music21 specific keywords and functions
        self.music21_keywords = [
            'stream', 'note', 'pitch', 'duration', 'tempo', 'meter', 
            'key', 'scale', 'chord', 'interval', 'clef', 'articulations',
            'dynamics', 'instrument', 'midi', 'realtime', 'environment',
            'corpus', 'common', 'configure', 'analysis', 'graph'
        ]
        
        self.python_keywords = [
            'def', 'class', 'return', 'if', 'elif', 'else', 'for', 'while',
            'break', 'continue', 'import', 'from', 'as', 'try', 'except',
            'finally', 'with', 'lambda', 'yield', 'None', 'True', 'False'
        ]
        
        # Setup autocompletion
        self.completion_list = self._build_completion_list()
        self.completion_popup = None
        self.completion_start = 0
        self.completion_end = 0
        
        # Bind events
        self.bind(text=self.on_text)
        self.bind(focus=self.on_focus)
        
        # Set initial text after widget is ready
        Clock.schedule_once(self.set_initial_text, 0.1)
    
    def _build_completion_list(self):
        """Build the autocompletion list with music21-specific items"""
        base_list = self.python_keywords + self.music21_keywords
        
        # Add music21 class methods and properties
        if MUSIC21_AVAILABLE:
            music21_classes = {
                'stream.Stream': ['append', 'insert', 'measure', 'show', 'write', 
                                'flat', 'notes', 'parts', 'recurse', 'transpose'],
                'note.Note': ['pitch', 'duration', 'offset', 'volume', 'articulations',
                             'lyric', 'tie', 'name', 'octave', 'midi'],
                'chord.Chord': ['pitches', 'root', 'bass', 'inversion', 'isMajorTriad',
                               'isMinorTriad', 'isDiminishedTriad', 'isAugmentedTriad'],
                'scale.Scale': ['getPitches', 'derive', 'getTonic', 'getDominant']
            }
            
            for cls, methods in music21_classes.items():
                base_list.extend([f"{cls}.{m}" for m in methods])
        
        return sorted(list(set(base_list)))
    
    def on_text(self, instance, value):
        """Triggered when text changes - handles syntax highlighting"""
        self._highlight_syntax()
        
        # Show completion popup when typing
        if self.focus and len(self.text) > 0:
            self._update_completion()
    
    def on_focus(self, instance, value):
        """Handle focus changes"""
        if value:  # Got focus
            self._highlight_syntax()
            self._update_completion()
        else:      # Lost focus
            if self.completion_popup:
                self.completion_popup.dismiss()
                self.completion_popup = None
    
    def _highlight_syntax(self):
        """Apply syntax highlighting to the code"""
        try:
            # Get the text and clear previous highlighting
            text = self.text
            self._clear_highlighting()
            
            # Highlight Python and music21 keywords
            for word in self.python_keywords + self.music21_keywords:
                self._highlight_word(word, self.keyword_color)
            
            # Highlight strings
            self._highlight_pattern(r'(\'[^\']*\'|\"[^\"]*\")', self.string_color)
            
            # Highlight comments
            self._highlight_pattern(r'#[^\n]*', self.comment_color)
            
            # Highlight function definitions
            self._highlight_pattern(r'def\s+(\w+)', self.function_color, group=1)
            
            # Highlight class definitions
            self._highlight_pattern(r'class\s+(\w+)', self.class_color, group=1)
            
        except Exception as e:
            print(f"Syntax highlighting error: {e}")
    
    def _clear_highlighting(self):
        """Clear all syntax highlighting"""
        if hasattr(self, '_highlight_rectangles'):
            for rect in self._highlight_rectangles:
                self.canvas.before.remove(rect)
            del self._highlight_rectangles
        self._highlight_rectangles = []
    
    def _highlight_word(self, word, color):
        """Highlight all occurrences of a specific word"""
        text = self.text
        start_idx = 0
        word_len = len(word)
        
        while True:
            idx = text.find(word, start_idx)
            if idx == -1:
                break
                
            # Check if it's a whole word (not part of another word)
            if (idx == 0 or not text[idx-1].isalnum()) and \
               (idx + word_len >= len(text) or not text[idx + word_len].isalnum()):
                self._highlight_range(idx, idx + word_len, color)
                
            start_idx = idx + word_len
    
    def _highlight_pattern(self, pattern, color, group=0):
        """Highlight text matching a regex pattern"""
        import re
        text = self.text
        for match in re.finditer(pattern, text):
            start, end = match.span(group)
            self._highlight_range(start, end, color)
    
    def _highlight_range(self, start, end, color):
        """Highlight a specific range of text"""
        # Get line information
        lines = self.text.split('\n')
        line_start = 0
        for line in lines:
            line_end = line_start + len(line)
            if start < line_end:
                break
            line_start = line_end + 1  # +1 for the newline
        
        # Calculate positions
        x, y = self.get_cursor_from_index(start)
        x2, y2 = self.get_cursor_from_index(end)
        
        # Create highlight rectangle
        with self.canvas.before:
            Color(*color)
            rect = Rectangle(
                pos=(self.x + x, self.y + y),
                size=(x2 - x, self.line_height)
            )
            self._highlight_rectangles.append(rect)
    
    def _update_completion(self):
        """Update the autocompletion popup"""
        # Get current word
        text = self.text[:self.cursor_index()]
        if not text:
            return
            
        # Find the start of the current word
        start = max(text.rfind(' '), text.rfind('\n'), text.rfind('('), 
                text.rfind('.'), text.rfind('[')) + 1
        current_word = text[start:]
        
        # Filter completion list
        matches = [w for w in self.completion_list if w.startswith(current_word)]
        
        if matches and current_word:
            self.completion_start = start
            self.completion_end = self.cursor_index()
            self._show_completion_popup(matches)
        elif self.completion_popup:
            self.completion_popup.dismiss()
            self.completion_popup = None
    
    def _show_completion_popup(self, items):
        """Show the autocompletion popup"""
        if self.completion_popup:
            self.completion_popup.dismiss()
        
        # Create popup content
        content = GridLayout(cols=1, spacing=5, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Add completion items
        for item in items[:10]:  # Limit to 10 items
            btn = Button(text=item, size_hint_y=None, height=30)
            btn.bind(on_press=lambda btn: self._apply_completion(btn.text))
            content.add_widget(btn)
        
        # Create and open popup
        popup = Popup(content=content, size_hint=(0.3, 0.4),
                     pos_hint={'x': 0.1, 'top': 0.9})
        self.completion_popup = popup
        popup.open()
    
    def _apply_completion(self, text):
        """Apply the selected completion"""
        if self.completion_popup:
            self.completion_popup.dismiss()
            self.completion_popup = None
            
        # Replace current word with completion
        current_text = self.text
        new_text = (current_text[:self.completion_start] + 
                   text + 
                   current_text[self.completion_end:])
        self.text = new_text
        
        # Move cursor to end of inserted text
        self.cursor = (self.completion_start + len(text), self.cursor[1])
    
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        """Handle keyboard events for autocompletion"""
        # Tab key completes the first suggestion
        if keycode[1] == 'tab' and self.completion_popup:
            if self.completion_popup.content.children:
                first_item = self.completion_popup.content.children[-1].text
                self._apply_completion(first_item)
            return True
        
        # Enter key confirms completion if popup is open
        if keycode[1] == 'enter' and self.completion_popup:
            return True
            
        # Arrow keys navigate completion popup
        if keycode[1] in ('up', 'down') and self.completion_popup:
            return True
            
        return super().keyboard_on_key_down(window, keycode, text, modifiers)
    
    def set_initial_text(self, dt):
        """Set initial text content with improved examples"""
        initial_code = """# SriDAW Music21 Code Editor
# Create rich musical compositions with harmony and rhythm

from music21 import *

# Example 1: Simple Melody with Chords
def create_melody_with_chords():
    \"\"\"Create a melody with chord accompaniment\"\"\"
    s = stream.Stream()
    s.append(tempo.MetronomeMark(number=120))
    s.append(meter.TimeSignature('4/4'))
    s.append(key.KeySignature(0))  # C major
    
    # Melody line
    melody_notes = ['C4', 'E4', 'G4', 'C5', 'G4', 'E4', 'C4']
    durations = [1, 0.5, 0.5, 1, 0.5, 0.5, 1]
    
    for i, (note_name, dur) in enumerate(zip(melody_notes, durations)):
        n = note.Note(note_name, quarterLength=dur)
        n.offset = sum(durations[:i])
        s.append(n)
    
    # Add simple chord accompaniment
    chords = [
        chord.Chord(['C3', 'E3', 'G3'], quarterLength=2),
        chord.Chord(['F3', 'A3', 'C4'], quarterLength=2),
        chord.Chord(['G3', 'B3', 'D4'], quarterLength=2),
        chord.Chord(['C3', 'E3', 'G3'], quarterLength=2)
    ]
    
    for i, c in enumerate(chords):
        c.offset = i * 2
        s.append(c)
    
    return s

# Example 2: Scale-based Melody with Dynamics
def create_scaled_melody():
    \"\"\"Create a melody from a scale with dynamic shaping\"\"\"
    s = stream.Stream()
    s.append(tempo.MetronomeMark(number=100))
    
    # Create D minor scale
    d_minor = scale.MinorScale('D4')
    scale_notes = d_minor.getPitches('D4', 'D5')
    
    # Create melody with crescendo
    for i, p in enumerate(scale_notes):
        n = note.Note(p, quarterLength=0.5)
        n.offset = i * 0.5
        n.volume.velocity = 60 + (i * 5)  # Crescendo
        s.append(n)
    
    # Add simple bass line
    bass_notes = ['D2', 'A2', 'G2', 'A2']
    for i, bn in enumerate(bass_notes):
        n = note.Note(bn, quarterLength=1)
        n.offset = i * 1
        n.volume.velocity = 50
        s.append(n)
    
    return s

# Example 3: Rhythmic Pattern with Articulations
def create_rhythmic_pattern():
    \"\"\"Create a syncopated rhythm with articulations\"\"\"
    s = stream.Stream()
    s.append(tempo.MetronomeMark(number=130))
    s.append(meter.TimeSignature('4/4'))
    
    # Create a syncopated rhythm pattern
    pattern = [
        ('C4', 0.5, 'accent'), 
        ('D4', 0.25, 'staccato'), 
        ('E4', 0.25, None),
        ('F4', 0.75, 'tenuto'), 
        ('G4', 0.25, 'staccato'), 
        ('A4', 0.5, None),
        ('G4', 0.25, 'staccato'), 
        ('F4', 0.25, None), 
        ('E4', 1.0, 'fermata')
    ]
    
    offset = 0
    for note_name, dur, artic in pattern:
        n = note.Note(note_name, quarterLength=dur)
        n.offset = offset
        offset += dur
        
        if artic:
            art = articulations.Articulation(artic)
            n.articulations.append(art)
        
        s.append(n)
    
    return s

# Choose which example to run (change the function call)
result = create_melody_with_chords()

# Uncomment to try different examples:
# result = create_scaled_melody()
# result = create_rhythmic_pattern()
"""
        try:
            self.text = initial_code
            self._highlight_syntax()
        except Exception as e:
            print(f"Error setting initial text: {e}")
            self.text = "# SriDAW Code Editor\n# Ready for music21 code"






class SriDAWApp(App):
    """Main application class"""
    
    def build(self):
        self.title = "SriDAW - Digital Audio Workstation"
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical')
        
        # Top toolbar
        toolbar = BoxLayout(size_hint_y=0.1, spacing=5)
        
        # Transport controls
        self.play_btn = Button(text='▶ Play', size_hint_x=0.15)
        self.stop_btn = Button(text='⏹ Stop', size_hint_x=0.15)
        self.record_btn = Button(text='⏺ Rec', size_hint_x=0.15)
        
        self.play_btn.bind(on_press=self.play_music)
        self.stop_btn.bind(on_press=self.stop_music)
        self.record_btn.bind(on_press=self.toggle_record)
        
        # File operations
        self.export_midi_btn = Button(text='Export MIDI', size_hint_x=0.15)
        self.export_code_btn = Button(text='Export Code', size_hint_x=0.15)
        self.demo_btn = Button(text='🎵 Demo', size_hint_x=0.1)
        
        self.export_midi_btn.bind(on_press=self.export_midi)
        self.export_code_btn.bind(on_press=self.export_code)
        self.demo_btn.bind(on_press=self.play_demo)
        
        # Tempo control
        tempo_label = Label(text='BPM:', size_hint_x=0.1)
        self.tempo_slider = Slider(min=60, max=200, value=120, size_hint_x=0.2)
        
        toolbar.add_widget(self.play_btn)
        toolbar.add_widget(self.stop_btn)
        toolbar.add_widget(self.record_btn)
        toolbar.add_widget(Label(text='|', size_hint_x=0.05))  # Separator
        toolbar.add_widget(self.export_midi_btn)
        toolbar.add_widget(self.export_code_btn)
        toolbar.add_widget(self.demo_btn)
        toolbar.add_widget(Label(text='|', size_hint_x=0.05))  # Separator
        toolbar.add_widget(tempo_label)
        toolbar.add_widget(self.tempo_slider)
        
        # Tabbed interface
        tab_panel = TabbedPanel(do_default_tab=False)
        
        # Piano Roll Tab
        piano_roll_tab = TabbedPanelItem(text='Piano Roll')
        piano_roll_layout = BoxLayout(orientation='horizontal')
        
        # Piano keys (left side)
        piano_keys_layout = BoxLayout(orientation='vertical', size_hint_x=0.15)
        
        # Create piano keys (simplified - just white keys for now)
        note_names = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        octaves = [5, 4, 3, 2]  # Top to bottom
        
        for octave in octaves:
            for note_name in reversed(note_names):  # Reverse for top-to-bottom
                key = PianoKey(f'{note_name}{octave}')
                key.bind(on_press=self.play_piano_key)
                piano_keys_layout.add_widget(key)
        
        # Piano roll editor
        self.piano_roll = PianoRoll()
        piano_roll_scroll = ScrollView()
        piano_roll_scroll.add_widget(self.piano_roll)
        
        piano_roll_layout.add_widget(piano_keys_layout)
        piano_roll_layout.add_widget(piano_roll_scroll)
        
        # Piano roll controls
        piano_controls = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        clear_btn = Button(text='Clear', size_hint_x=0.2)
        clear_btn.bind(on_press=lambda x: self.piano_roll.clear_notes())
        piano_controls.add_widget(clear_btn)
        piano_controls.add_widget(Label())  # Spacer
        
        piano_roll_content = BoxLayout(orientation='vertical')
        piano_roll_content.add_widget(piano_roll_layout)
        piano_roll_content.add_widget(piano_controls)
        
        piano_roll_tab.add_widget(piano_roll_content)
        tab_panel.add_widget(piano_roll_tab)
        
        # Code Editor Tab
        code_tab = TabbedPanelItem(text='Code Editor')
        code_layout = BoxLayout(orientation='vertical')
        
        # Code editor
        self.code_editor = CodeEditor()
        
        # Code controls
        code_controls = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        run_code_btn = Button(text='Run Code', size_hint_x=0.2)
        run_code_btn.bind(on_press=self.run_code)
        code_controls.add_widget(run_code_btn)
        code_controls.add_widget(Label())  # Spacer
        
        code_layout.add_widget(self.code_editor)
        code_layout.add_widget(code_controls)
        code_tab.add_widget(code_layout)
        tab_panel.add_widget(code_tab)
        
        # Add components to main layout
        main_layout.add_widget(toolbar)
        main_layout.add_widget(tab_panel)
        
        # Status bar
        self.status_label = Label(text='Ready', size_hint_y=0.05)
        main_layout.add_widget(self.status_label)
        
        # Initialize audio
        self.init_audio()
        
        # Current stream for playback
        self.current_stream = None
        self.is_playing = False
        
        return main_layout
    
    def init_audio(self):
        """Initialize audio system"""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.update_status("Audio initialized (pygame)")
            except:
                self.update_status("Audio initialization failed")
        else:
            self.update_status("Audio not available - install pygame")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.text = f"Status: {message}"
    
    def play_piano_key(self, button):
        """Play individual piano key"""
        note_name = button.note_name
        self.update_status(f"Playing {note_name}")
        
        # Visual feedback
        original_color = button.background_color
        button.background_color = (0.8, 0.8, 0.2, 1)  # Yellow when pressed
        
        def reset_color(dt):
            button.background_color = original_color
        
        Clock.schedule_once(reset_color, 0.2)
        
        if MUSIC21_AVAILABLE:
            try:
                # Create and play single note with better sound
                n = note.Note(note_name, quarterLength=1)
                n.volume.velocity = 80
                s = stream.Stream()
                s.append(tempo.TempoIndication(number=120))
                s.append(n)
                
                # Use threading to avoid blocking UI
                self.play_stream_quick(s)
            except Exception as e:
                self.update_status(f"Error playing note: {e}")
    
    
    def play_music(self, button):
        """Play current composition"""
        if self.is_playing:
            return

        try:
            # Try to get music from piano roll
            stream_obj = self.piano_roll.get_music21_stream()

            # Fallback: use last code result if piano roll is empty
            if (not stream_obj or len(stream_obj.notes) == 0) and self.current_stream:
                stream_obj = self.current_stream

            if stream_obj and len(stream_obj.notes) > 0:
                self.current_stream = stream_obj
                self.is_playing = True
                self.play_btn.text = '⏸ Pause'
                self.update_status("Playing...")

                # Play in separate thread
                threading.Thread(target=self.play_stream_threaded, args=(stream_obj,)).start()
            else:
                self.update_status("No notes to play")
        except Exception as e:
            self.update_status(f"Playback error: {e}")


    def play_stream_threaded(self, stream_obj):
        """Play music21 stream in separate thread"""
        try:
            if MUSIC21_AVAILABLE:
                # Try to use music21's built-in playback
                try:
                    # Create temporary MIDI file for playback
                    temp_dir = tempfile.gettempdir()
                    temp_file = os.path.join(temp_dir, "sridaw_temp.mid")
                    
                    # Write MIDI file
                    stream_obj.write('midi', fp=temp_file)
                    
                    # Play using pygame if available
                    if PYGAME_AVAILABLE:
                        pygame.mixer.music.load(temp_file)
                        pygame.mixer.music.play()
                        
                        # Wait for playback to finish
                        while pygame.mixer.music.get_busy():
                            pygame.time.wait(100)
                    
                    # Clean up
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        
                except Exception as e:
                    print(f"Playback error: {e}")
                    
        except Exception as e:
            print(f"Stream playback error: {e}")
        finally:
            # Reset play state
            Clock.schedule_once(self.reset_play_state, 0)
    
    def play_stream_quick(self, stream_obj):
        """Quick playback for single notes"""
        try:
            if PYGAME_AVAILABLE and stream_obj:
                # Create temporary MIDI file for quick playback
                temp_dir = tempfile.gettempdir()
                temp_file = os.path.join(temp_dir, f"sridaw_quick_{id(stream_obj)}.mid")
                
                # Write and play MIDI file
                stream_obj.write('midi', fp=temp_file)
                
                # Non-blocking playback
                def play_quick():
                    try:
                        pygame.mixer.music.load(temp_file)
                        pygame.mixer.music.play(loops=0)
                        # Clean up after a short delay
                        Clock.schedule_once(lambda dt: self.cleanup_temp_file(temp_file), 2)
                    except Exception as e:
                        print(f"Quick playback error: {e}")
                
                threading.Thread(target=play_quick, daemon=True).start()
        except Exception as e:
            print(f"Stream quick play error: {e}")
    
    def cleanup_temp_file(self, filepath):
        """Clean up temporary files"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def play_demo(self, button):
        """Play a demo composition"""
        try:
            if MUSIC21_AVAILABLE:
                # Create a nice demo composition
                s = stream.Stream()
                s.append(tempo.TempoIndication(number=120))
                s.append(meter.TimeSignature('4/4'))
                s.append(key.KeySignature(0))  # C major
                
                # Melody: Twinkle Twinkle Little Star
                melody = [
                    ('C4', 1), ('C4', 1), ('G4', 1), ('G4', 1),
                    ('A4', 1), ('A4', 1), ('G4', 2),
                    ('F4', 1), ('F4', 1), ('E4', 1), ('E4', 1),
                    ('D4', 1), ('D4', 1), ('C4', 2)
                ]
                
                offset = 0
                for note_name, dur in melody:
                    n = note.Note(note_name, quarterLength=dur)
                    n.volume.velocity = 70
                    n.offset = offset
                    offset += dur
                    s.append(n)
                
                # Add some harmony
                harmony_notes = [
                    ('C3', 4, 0), ('F3', 4, 4), ('G3', 4, 8), ('C3', 4, 12)
                ]
                
                for note_name, dur, offset_time in harmony_notes:
                    n = note.Note(note_name, quarterLength=dur)
                    n.volume.velocity = 50
                    n.offset = offset_time
                    s.append(n)
                
                self.current_stream = s
                self.update_status("Playing demo composition...")
                
                # Play the demo
                if not self.is_playing:
                    self.is_playing = True
                    self.play_btn.text = '⏸ Pause'
                    threading.Thread(target=self.play_stream_threaded, args=(s,)).start()
            else:
                self.update_status("Music21 not available for demo")
        except Exception as e:
            self.update_status(f"Demo error: {e}")
    
    def reset_play_state(self, dt):
        """Reset play button state"""
        self.is_playing = False
        self.play_btn.text = '▶ Play'
        self.update_status("Playback finished")
    
    def stop_music(self, button):
        """Stop music playback"""
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()
        
        self.is_playing = False
        self.play_btn.text = '▶ Play'
        self.update_status("Stopped")
    
    def toggle_record(self, button):
        """Toggle recording mode"""
        # Placeholder for recording functionality
        self.update_status("Recording not implemented yet")
    
    def run_code(self, button):
        """Execute code from editor"""
        code = self.code_editor.text
        
        try:
            # Create execution environment
            exec_globals = {
                'stream': stream if MUSIC21_AVAILABLE else None,
                'note': note if MUSIC21_AVAILABLE else None,
                'pitch': pitch if MUSIC21_AVAILABLE else None,
                'duration': duration if MUSIC21_AVAILABLE else None,
                'tempo': tempo if MUSIC21_AVAILABLE else None,
                'meter': meter if MUSIC21_AVAILABLE else None,
                'key': key if MUSIC21_AVAILABLE else None,
                'scale': scale if MUSIC21_AVAILABLE else None,
            }
            
            exec_locals = {}
            
            # Execute code
            exec(code, exec_globals, exec_locals)
            
            # Check if result is a stream
            if 'result' in exec_locals and MUSIC21_AVAILABLE:
                result = exec_locals['result']
                if hasattr(result, 'notes'):  # It's likely a music21 stream
                    self.current_stream = result
                    self.update_status(f"Code executed - {len(result.notes)} notes generated")
                else:
                    self.update_status("Code executed successfully")
            else:
                self.update_status("Code executed successfully")
                
        except Exception as e:
            self.update_status(f"Code error: {str(e)}")
    
    def export_midi(self, button):
        """Export current composition as MIDI file"""
        try:
            # Get stream from piano roll or code execution
            stream_obj = self.current_stream or self.piano_roll.get_music21_stream()
            
            if stream_obj and MUSIC21_AVAILABLE:
                # Create file chooser popup
                content = BoxLayout(orientation='vertical')
                
                # File path input
                path_input = TextInput(text='composition.mid', multiline=False)
                content.add_widget(Label(text='Enter filename:', size_hint_y=0.3))
                content.add_widget(path_input)
                
                # Buttons
                btn_layout = BoxLayout(size_hint_y=0.3)
                save_btn = Button(text='Save')
                cancel_btn = Button(text='Cancel')
                
                popup = Popup(title='Export MIDI', content=content, size_hint=(0.8, 0.6))
                
                def save_midi(btn):
                    try:
                        filename = path_input.text
                        if not filename.endswith('.mid'):
                            filename += '.mid'
                        
                        stream_obj.write('midi', fp=filename)
                        self.update_status(f"MIDI exported: {filename}")
                        popup.dismiss()
                    except Exception as e:
                        self.update_status(f"Export error: {e}")
                
                save_btn.bind(on_press=save_midi)
                cancel_btn.bind(on_press=popup.dismiss)
                
                btn_layout.add_widget(save_btn)
                btn_layout.add_widget(cancel_btn)
                content.add_widget(btn_layout)
                
                popup.open()
            else:
                self.update_status("No composition to export")
                
        except Exception as e:
            self.update_status(f"Export error: {e}")
    
    def export_code(self, button):
        """Export current code to file"""
        try:
            content = BoxLayout(orientation='vertical')
            
            # File path input
            path_input = TextInput(text='composition.py', multiline=False)
            content.add_widget(Label(text='Enter filename:', size_hint_y=0.3))
            content.add_widget(path_input)
            
            # Buttons
            btn_layout = BoxLayout(size_hint_y=0.3)
            save_btn = Button(text='Save')
            cancel_btn = Button(text='Cancel')
            
            popup = Popup(title='Export Code', content=content, size_hint=(0.8, 0.6))
            
            def save_code(btn):
                try:
                    filename = path_input.text
                    if not filename.endswith('.py'):
                        filename += '.py'
                    
                    with open(filename, 'w') as f:
                        f.write(self.code_editor.text)
                    
                    self.update_status(f"Code exported: {filename}")
                    popup.dismiss()
                except Exception as e:
                    self.update_status(f"Export error: {e}")
            
            save_btn.bind(on_press=save_code)
            cancel_btn.bind(on_press=popup.dismiss)
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup.open()
            
        except Exception as e:
            self.update_status(f"Export error: {e}")

if __name__ == '__main__':
    # Check dependencies
    if not MUSIC21_AVAILABLE:
        print("Warning: music21 not available. Install with: pip install music21")
    
    if not PYGAME_AVAILABLE:
        print("Warning: pygame not available. Install with: pip install pygame")
    
    # Run the app
    SriDAWApp().run()
