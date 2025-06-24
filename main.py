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
from kivy.core.audio import SoundLoader

import os
import threading
import tempfile
import math
import wave
import struct
from pathlib import Path

# Music21 imports
try:
    from music21 import stream, note, pitch, duration, tempo, meter, key, scale
    from music21 import midi as music21_midi
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    print("Warning: music21 not available. Install with: pip install music21")

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
    
    def on_touch_down(self, touch):
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
    
    def on_touch_move(self, touch):
        if self.drawing and self.collide_point(*touch.pos):
            # Extend note duration while dragging
            if self.notes:
                grid_x = int((touch.pos[0] - self.x) // self.grid_width)
                last_note = self.notes[-1]
                last_note['duration'] = max(1, grid_x - last_note['time'])
                self.draw_grid()
    
    def on_touch_up(self, touch):
        self.drawing = False
    
    def play_note_sound(self, grid_pitch):
        """Play sound for a note at given grid pitch"""
        try:
            # Convert grid pitch to MIDI note
            midi_note = 60 + (grid_pitch - 20)  # C4 = 60
            midi_note = max(21, min(127, midi_note))  # Clamp to valid MIDI range
            
            # Play using app's sample player
            app = App.get_running_app()
            app.play_note_sample(midi_note)
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
    """Code editor with syntax highlighting (basic)"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = True
        self.background_color = (0.1, 0.1, 0.1, 1)
        self.foreground_color = (1, 1, 1, 1)
        # Set initial text after widget is ready
        Clock.schedule_once(self.set_initial_text, 0.1)
    
    def set_initial_text(self, dt):
        """Set initial text content"""
        initial_code = """# SriDAW Music21 Code Editor - Sound Examples
# Create rich musical compositions with harmony and rhythm

from music21 import stream, note, pitch, scale, tempo, meter, key
from music21 import chord, duration, interval

# Example 1: Simple Melody with Chords
def create_melody_with_chords():
    s = stream.Stream()
    s.append(tempo.TempoIndication(number=120))
    s.append(meter.TimeSignature('4/4'))
    s.append(key.KeySignature(0))  # C major
    
    # Melody line
    melody_notes = ['C4', 'E4', 'G4', 'C5', 'G4', 'E4', 'C4']
    durations = [1, 0.5, 0.5, 1, 0.5, 0.5, 1]
    
    for i, (note_name, dur) in enumerate(zip(melody_notes, durations)):
        n = note.Note(note_name, quarterLength=dur)
        n.offset = sum(durations[:i])
        s.append(n)
    
    # Add bass line
    bass_notes = ['C2', 'G2', 'C2', 'F2']
    for i, bass_note in enumerate(bass_notes):
        n = note.Note(bass_note, quarterLength=1)
        n.offset = i * 1
        s.append(n)
    
    return s

# Example 2: Chord Progression
def create_chord_progression():
    s = stream.Stream()
    s.append(tempo.TempoIndication(number=100))
    
    # I-vi-IV-V progression in C major
    chords = [
        chord.Chord(['C4', 'E4', 'G4']),  # C major
        chord.Chord(['A3', 'C4', 'E4']),  # A minor
        chord.Chord(['F3', 'A3', 'C4']),  # F major
        chord.Chord(['G3', 'B3', 'D4'])   # G major
    ]
    
    for i, c in enumerate(chords):
        c.quarterLength = 2
        c.offset = i * 2
        s.append(c)
    
    return s

# Example 3: Scale-based Melody
def create_scale_melody():
    s = stream.Stream()
    s.append(tempo.TempoIndication(number=140))
    
    # Create C major scale
    c_major = scale.MajorScale('C4')
    scale_notes = c_major.pitches
    
    # Ascending and descending
    for i, p in enumerate(scale_notes[:8]):  # One octave up
        n = note.Note(p, quarterLength=0.5)
        n.offset = i * 0.5
        s.append(n)
    
    for i, p in enumerate(reversed(scale_notes[:8])):  # One octave down
        n = note.Note(p, quarterLength=0.5)
        n.offset = (i + 8) * 0.5
        s.append(n)
    
    return s

# Example 4: Rhythmic Pattern
def create_rhythm_pattern():
    s = stream.Stream()
    s.append(tempo.TempoIndication(number=130))
    s.append(meter.TimeSignature('4/4'))
    
    # Create a syncopated rhythm
    rhythm_pattern = [
        ('C4', 0.5), ('D4', 0.25), ('E4', 0.25),
        ('F4', 0.75), ('G4', 0.25), ('A4', 0.5),
        ('G4', 0.25), ('F4', 0.25), ('E4', 1.0)
    ]
    
    offset = 0
    for note_name, dur in rhythm_pattern:
        n = note.Note(note_name, quarterLength=dur)
        n.offset = offset
        offset += dur
        s.append(n)
    
    return s

# Choose which example to run (change the function call)
result = create_melody_with_chords()

# Uncomment one of these to try different examples:
# result = create_chord_progression()
# result = create_scale_melody()
# result = create_rhythm_pattern()
"""
        try:
            self.text = initial_code
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
        # Create cache directory for WAV files
        self.cache_dir = self.user_data_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.update_status("Audio initialized (sine wave generator)")
    
    def midi_to_freq(self, midi_note):
        """Convert MIDI note number to frequency"""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
    
    def generate_wav(self, freq, filename, duration=0.5, sample_rate=44100):
        """Generate a WAV file for a sine wave of the given frequency"""
        # Generate the sine wave data
        num_samples = int(sample_rate * duration)
        # Open the WAV file
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)   # 2 bytes (16 bits) per sample
            wav_file.setframerate(sample_rate)
            # Generate the samples
            for i in range(num_samples):
                t = float(i) / sample_rate
                # Generate a sine wave at the given frequency
                sample_val = int(32767.0 * math.sin(2 * math.pi * freq * t))
                # Pack the sample as a short (16-bit) in little-endian
                wav_file.writeframesraw(struct.pack('<h', sample_val))
    
    def play_note_sample(self, midi_note):
        """Play a note using Kivy's SoundLoader, generating the WAV if needed"""
        try:
            # Convert MIDI note to frequency
            freq = self.midi_to_freq(midi_note)
            # The filename for this note
            filename = os.path.join(self.cache_dir, f"note_{midi_note}.wav")
            
            # If the WAV file doesn't exist, generate it
            if not os.path.exists(filename):
                self.generate_wav(freq, filename)
            
            # Load the sound
            sound = SoundLoader.load(filename)
            if sound:
                sound.play()
            else:
                print(f"Failed to load sound: {filename}")
        except Exception as e:
            print(f"Error playing note sample: {e}")
    
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
                # Convert note name to MIDI
                p = pitch.Pitch(note_name)
                self.play_note_sample(p.midi)
            except Exception as e:
                self.update_status(f"Error playing note: {e}")
    
    def play_music(self, button):
        """Play current composition"""
        if self.is_playing:
            return
        
        try:
            # Get current stream from piano roll
            stream_obj = self.piano_roll.get_music21_stream()
            
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
            if not MUSIC21_AVAILABLE:
                return
                
            # Create temporary MIDI file for playback
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, "sridaw_temp.mid")
            
            # Write MIDI file
            stream_obj.write('midi', fp=temp_file)
            
            # We'll play each note individually (simplified version)
            self.update_status("Playing composition...")
            for element in stream_obj.flatten().notes:
                if isinstance(element, note.Note):
                    self.play_note_sample(element.pitch.midi)
                    # Wait for note duration
                    time.sleep(element.duration.quarterLength * 0.25)
                elif isinstance(element, chord.Chord):
                    for p in element.pitches:
                        self.play_note_sample(p.midi)
                    time.sleep(element.duration.quarterLength * 0.25)
                
                # Check if we should stop
                if not self.is_playing:
                    break
                    
        except Exception as e:
            print(f"Playback error: {e}")
            self.update_status(f"Playback error: {e}")
        finally:
            # Reset play state
            Clock.schedule_once(self.reset_play_state, 0)
    
    def play_demo(self, button):
        """Play a demo composition"""
        self.update_status("Playing demo...")
        try:
            # Play a simple scale
            for midi_note in range(60, 73):  # C4 to C5
                self.play_note_sample(midi_note)
                # Short delay between notes
                time.sleep(0.2)
        except Exception as e:
            self.update_status(f"Demo error: {e}")
    
    def reset_play_state(self, dt):
        """Reset play button state"""
        self.is_playing = False
        self.play_btn.text = '▶ Play'
        self.update_status("Playback finished")
    
    def stop_music(self, button):
        """Stop music playback"""
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
    import time
    
    # Check dependencies
    if not MUSIC21_AVAILABLE:
        print("Warning: music21 not available. Install with: pip install music21")
    
    # Run the app
    SriDAWApp().run()
