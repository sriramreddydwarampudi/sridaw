import os
import tempfile
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.utils import platform
import threading
import time

# Import music21 components
try:
    from music21 import stream, note, chord, scale, duration, tempo, meter, key
    from music21.midi import MidiFile
    from music21 import environment
    # Set music21 to work offline
    environment.set('autoDownload', 'False')
    environment.set('debug', 0)
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False

# Audio playback imports
if platform == 'android':
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        from android.permissions import request_permissions, Permission
        MediaPlayer = autoclass('android.media.MediaPlayer')
        Uri = autoclass('android.net.Uri')
        File = autoclass('java.io.File')
        Environment = autoclass('android.os.Environment')
        AUDIO_AVAILABLE = True
    except ImportError:
        AUDIO_AVAILABLE = False
else:
    try:
        import pygame
        pygame.mixer.init()
        AUDIO_AVAILABLE = True
    except ImportError:
        AUDIO_AVAILABLE = False


class PianoRollWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notes_data = []
        self.bind(size=self.redraw, pos=self.redraw)
    
    def set_notes(self, notes_data):
        self.notes_data = notes_data
        self.redraw()
    
    def redraw(self, *args):
        self.canvas.clear()
        if not self.notes_data:
            return
        
        with self.canvas:
            # Background
            Color(0.1, 0.1, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Piano roll grid
            Color(0.3, 0.3, 0.3, 1)
            # Horizontal lines (pitches)
            for i in range(128):  # MIDI pitch range
                y = self.y + (i / 127) * self.height
                Line(points=[self.x, y, self.x + self.width, y], width=0.5)
            
            # Vertical lines (time)
            if self.notes_data:
                max_time = max(note['end'] for note in self.notes_data)
                for i in range(int(max_time) + 1):
                    x = self.x + (i / max_time) * self.width
                    Line(points=[x, self.y, x, self.y + self.height], width=0.5)
            
            # Draw notes
            for note_data in self.notes_data:
                pitch = note_data['pitch']
                start_time = note_data['start']
                end_time = note_data['end']
                
                # Note color based on pitch
                hue = (pitch % 12) / 12.0
                Color(hue, 0.8, 1, 0.8, mode='hsv')
                
                # Calculate positions
                if self.notes_data:
                    x = self.x + (start_time / max_time) * self.width
                    width = ((end_time - start_time) / max_time) * self.width
                    y = self.y + (pitch / 127) * self.height
                    height = self.height / 127 * 2  # Note height
                    
                    Rectangle(pos=(x, y), size=(width, height))


class MusicApp(App):
    def build(self):
        if not MUSIC21_AVAILABLE:
            return Label(text="music21 not available. Install with: pip install music21")
        
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Title
        title = Label(text='Music21 Android App', size_hint_y=None, height=50,
                     font_size=20, bold=True)
        main_layout.add_widget(title)
        
        # Control buttons
        controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        self.generate_btn = Button(text='Generate Music', size_hint_x=0.33)
        self.generate_btn.bind(on_press=self.generate_music)
        controls.add_widget(self.generate_btn)
        
        self.play_btn = Button(text='Play', size_hint_x=0.33, disabled=True)
        self.play_btn.bind(on_press=self.play_music)
        controls.add_widget(self.play_btn)
        
        self.download_btn = Button(text='Download MIDI', size_hint_x=0.33, disabled=True)
        self.download_btn.bind(on_press=self.download_midi)
        controls.add_widget(self.download_btn)
        
        main_layout.add_widget(controls)
        
        # Music parameters
        params_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        params_layout.add_widget(Label(text='Key:', width=50, size_hint_x=None))
        
        self.key_input = TextInput(text='C', multiline=False, size_hint_x=0.5)
        params_layout.add_widget(self.key_input)
        
        params_layout.add_widget(Label(text='Tempo:', width=60, size_hint_x=None))
        self.tempo_input = TextInput(text='120', multiline=False, size_hint_x=0.5)
        params_layout.add_widget(self.tempo_input)
        
        main_layout.add_widget(params_layout)
        
        # Status display
        self.status_label = Label(text='Ready to generate music', 
                                size_hint_y=None, height=30)
        main_layout.add_widget(self.status_label)
        
        # Piano roll display
        piano_roll_container = BoxLayout(orientation='vertical')
        piano_roll_container.add_widget(Label(text='Piano Roll View:', 
                                            size_hint_y=None, height=30))
        
        self.piano_roll = PianoRollWidget()
        piano_roll_container.add_widget(self.piano_roll)
        main_layout.add_widget(piano_roll_container)
        
        # Music info display
        info_scroll = ScrollView(size_hint_y=0.3)
        self.info_label = Label(text='Music information will appear here...',
                              text_size=(None, None), halign='left', valign='top')
        info_scroll.add_widget(self.info_label)
        main_layout.add_widget(info_scroll)
        
        # Initialize
        self.current_stream = None
        self.midi_file_path = None
        
        if platform == 'android' and AUDIO_AVAILABLE:
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, 
                               Permission.READ_EXTERNAL_STORAGE])
        
        return main_layout
    
    def generate_music(self, instance):
        self.status_label.text = 'Generating music...'
        threading.Thread(target=self._generate_music_thread).start()
    
    def _generate_music_thread(self):
        try:
            # Create a new stream
            s = stream.Stream()
            
            # Set key and tempo
            key_name = self.key_input.text or 'C'
            tempo_val = int(self.tempo_input.text or '120')
            
            s.append(key.Key(key_name))
            s.append(tempo.TempoIndication(number=tempo_val))
            s.append(meter.TimeSignature('4/4'))
            
            # Generate a simple melody using the key's scale
            scale_obj = scale.MajorScale(key_name)
            scale_notes = scale_obj.pitches
            
            # Create a simple melody pattern
            melody_notes = []
            durations = [0.5, 1.0, 0.5, 1.0, 2.0, 1.0, 0.5, 0.5]
            
            for i in range(8):
                pitch = scale_notes[i % len(scale_notes)]
                dur = durations[i % len(durations)]
                n = note.Note(pitch, quarterLength=dur)
                melody_notes.append(n)
                s.append(n)
            
            # Add some chords
            chord_progression = ['I', 'V', 'vi', 'IV']
            for chord_symbol in chord_progression:
                c = chord.Chord(scale_obj.pitchFromDegree(1).name + chord_symbol,
                               quarterLength=2.0)
                s.append(c)
            
            self.current_stream = s
            
            # Extract notes data for piano roll
            notes_data = []
            current_time = 0
            
            for element in s.flat.notes:
                if hasattr(element, 'pitch'):  # Single note
                    notes_data.append({
                        'pitch': element.pitch.midi,
                        'start': current_time,
                        'end': current_time + float(element.quarterLength)
                    })
                elif hasattr(element, 'pitches'):  # Chord
                    for pitch in element.pitches:
                        notes_data.append({
                            'pitch': pitch.midi,
                            'start': current_time,
                            'end': current_time + float(element.quarterLength)
                        })
                current_time += float(element.quarterLength)
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_ui_after_generation(notes_data))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(str(e)))
    
    def _update_ui_after_generation(self, notes_data):
        self.status_label.text = 'Music generated successfully!'
        self.play_btn.disabled = False
        self.download_btn.disabled = False
        
        # Update piano roll
        self.piano_roll.set_notes(notes_data)
        
        # Update info display
        if self.current_stream:
            info_text = f"Generated music in {self.key_input.text} major\n"
            info_text += f"Tempo: {self.tempo_input.text} BPM\n"
            info_text += f"Number of notes: {len([n for n in self.current_stream.flat.notes])}\n"
            info_text += f"Duration: {self.current_stream.duration.quarterLength} beats\n"
            
            # Update text size for wrapping
            self.info_label.text_size = (400, None)
            self.info_label.text = info_text
    
    def _show_error(self, error_msg):
        self.status_label.text = f'Error: {error_msg}'
    
    def play_music(self, instance):
        if not self.current_stream:
            return
        
        self.status_label.text = 'Playing music...'
        threading.Thread(target=self._play_music_thread).start()
    
    def _play_music_thread(self):
        try:
            # Convert to MIDI and play
            temp_dir = tempfile.gettempdir()
            midi_path = os.path.join(temp_dir, 'temp_music.mid')
            
            # Write MIDI file
            mf = self.current_stream.write('midi', fp=midi_path)
            
            if platform == 'android' and AUDIO_AVAILABLE:
                self._play_android(midi_path)
            elif AUDIO_AVAILABLE:
                self._play_desktop(midi_path)
            else:
                Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                     'Audio playback not available'))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(f"Playback error: {str(e)}"))
    
    def _play_android(self, midi_path):
        try:
            media_player = MediaPlayer()
            media_player.setDataSource(midi_path)
            media_player.prepare()
            media_player.start()
            
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                 'Playing... (Android)'))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(f"Android playback error: {str(e)}"))
    
    def _play_desktop(self, midi_path):
        try:
            # Simple beep pattern for desktop (since pygame doesn't play MIDI directly)
            for i in range(5):
                pygame.mixer.Sound.play(pygame.mixer.Sound(
                    buffer=b'\x00\x7f' * 1000))  # Simple tone
                time.sleep(0.5)
            
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                 'Playback complete'))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(f"Desktop playback error: {str(e)}"))
    
    def download_midi(self, instance):
        if not self.current_stream:
            return
        
        self.status_label.text = 'Downloading MIDI...'
        threading.Thread(target=self._download_midi_thread).start()
    
    def _download_midi_thread(self):
        try:
            if platform == 'android':
                # Save to Downloads folder on Android
                downloads_dir = Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
                midi_path = os.path.join(downloads_dir, 'generated_music.mid')
            else:
                # Save to current directory on desktop
                midi_path = 'generated_music.mid'
            
            # Write MIDI file
            self.current_stream.write('midi', fp=midi_path)
            self.midi_file_path = midi_path
            
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 
                                                 f'MIDI saved to: {midi_path}'))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(f"Download error: {str(e)}"))


if __name__ == '__main__':
    MusicApp().run()
