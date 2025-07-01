#!/usr/bin/env python3
"""
Music21 Visual DAW - Final Fixed Version with Android Playback
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.codeinput import CodeInput
from kivy.graphics import Color, Rectangle, Line
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.metrics import dp
from kivy.lang import Builder

import os
import platform
import tempfile
import subprocess
import traceback

# Conditional imports
try:
    from jnius import autoclass, cast, PythonJavaClass, java_method
    ANDROID = True
    VERSION = autoclass('android.os.Build$VERSION')
    SDK_INT = VERSION.SDK_INT
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = PythonActivity.mActivity
except:
    ANDROID = False
    SDK_INT = 0

try:
    from music21 import stream, note, tempo, chord, dynamics, articulations
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False

# Font registration with fallbacks
font_registered = False
font_paths = [
    '/system/fonts/RobotoMono-Regular.ttf',
    '/system/fonts/DroidSansMono.ttf',
    '/system/fonts/CutiveMono.ttf',
]

for path in font_paths:
    try:
        if os.path.exists(path):
            LabelBase.register(name="Mono", fn_regular=path)
            font_registered = True
            break
    except:
        pass

if not font_registered:
    LabelBase.register(name="Mono", fn_regular=LabelBase.default_font)

# Android MediaPlayer Listeners
if ANDROID:
    class OnPreparedListener(PythonJavaClass):
        __javainterfaces__ = ['android/media/MediaPlayer$OnPreparedListener']
        __javacontext__ = 'app'

        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method('(Landroid/media/MediaPlayer;)V')
        def onPrepared(self, mp):
            self.callback(mp)

    class OnCompletionListener(PythonJavaClass):
        __javainterfaces__ = ['android/media/MediaPlayer$OnCompletionListener']
        __javacontext__ = 'app'

        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method('(Landroid/media/MediaPlayer;)V')
        def onCompletion(self, mp):
            self.callback(mp)

    class OnErrorListener(PythonJavaClass):
        __javainterfaces__ = ['android/media/MediaPlayer$OnErrorListener']
        __javacontext__ = 'app'

        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method('(Landroid/media/MediaPlayer;II)Z')
        def onError(self, mp, what, extra):
            return self.callback(mp, what, extra)

# UI Layout Definition
Builder.load_string('''
<MainLayout>:
    orientation: 'vertical'
    spacing: dp(5)
    padding: dp(5)
    
    BoxLayout:
        size_hint_y: 0.6
        CodeInput:
            id: editor
            font_name: 'Mono'
            font_size: dp(14)
            background_color: 0.1, 0.1, 0.1, 1
            foreground_color: 0.9, 0.9, 0.9, 1
    
    BoxLayout:
        size_hint_y: 0.4
        ScrollView:
            do_scroll_x: True
            do_scroll_y: True
            bar_width: dp(10)
            PianoRollWidget:
                id: piano_roll
                size_hint_x: None
                width: max(self.minimum_width, root.width)
    
    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(5)
        
        Button:
            text: 'Run'
            size_hint_x: 0.15
            on_press: app.run_code()
        
        Button:
            text: 'Play'
            size_hint_x: 0.15
            on_press: app.play_audio()
        
        Button:
            text: 'Stop'
            size_hint_x: 0.15
            on_press: app.stop_audio()
        
        Button:
            text: 'Export'
            size_hint_x: 0.15
            on_press: app.export_midi()
        
        Label:
            text: app.status_text
            size_hint_x: 0.4
            halign: 'left'
            text_size: self.width, None
''')

class MainLayout(BoxLayout):
    pass

class PianoRollWidget(BoxLayout):
    notes = ListProperty([])
    beat_scale = NumericProperty(dp(50))
    pitch_range = range(36, 84)  # MIDI note range (C2 to B5)
    current_time = NumericProperty(0)
    is_playing = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = len(self.pitch_range) * dp(15)
        self.bind(
            size=self._update_canvas,
            pos=self._update_canvas,
            notes=self._update_canvas,
            current_time=self._update_playhead
        )
        self.playhead_line = None
        self._key_colors = {}
        self._init_key_colors()
        
    def _init_key_colors(self):
        """Initialize colors for piano keys (black/white)"""
        black_keys = {1, 3, 6, 8, 10}  # Semitone offsets for black keys
        for pitch in self.pitch_range:
            if (pitch % 12) in black_keys:
                self._key_colors[pitch] = (0.2, 0.2, 0.2, 1)  # Black keys
            else:
                self._key_colors[pitch] = (0.9, 0.9, 0.9, 1)  # White keys
    
    def _update_canvas(self, *args):
        self.canvas.after.clear()
        if not self.notes:
            return
            
        with self.canvas.after:
            # Draw piano keys background
            for i, pitch in enumerate(self.pitch_range):
                y = self.y + i * dp(15)
                Color(*self._key_colors[pitch])
                Rectangle(
                    pos=(self.x, y),
                    size=(self.width, dp(15)))
            
            # Draw measure/beat lines
            max_x = max((o + d) * self.beat_scale for o, _, d, _ in self.notes) if self.notes else 10
            Color(0.5, 0.5, 0.5, 0.5)
            for beat in range(0, int(max_x / self.beat_scale) + 2):
                x = self.x + beat * self.beat_scale
                Line(points=[x, self.y, x, self.top], width=1)
            
            # Draw notes with velocity-based coloring
            for offset, pitch, duration, velocity in self.notes:
                x = self.x + offset * self.beat_scale
                y = self.y + (pitch - min(self.pitch_range)) * dp(15)
                w = duration * self.beat_scale
                h = dp(14)
                
                # Color based on velocity (blue gradient)
                blue_intensity = 0.5 + (velocity / 200)
                Color(0.2, 0.4, blue_intensity, 0.9)
                Rectangle(pos=(x, y), size=(w, h))
                
                # Note border
                Color(0, 0, 0, 0.3)
                Line(rectangle=(x, y, w, h), width=1)
            
            # Playhead line
            if self.is_playing:
                Color(1, 0, 0, 0.7)
                self.playhead_line = Line(
                    points=[self.x + self.current_time * self.beat_scale, self.y, 
                           self.x + self.current_time * self.beat_scale, self.top],
                    width=2)
    
    def _update_playhead(self, *args):
        if self.playhead_line and self.is_playing:
            self.playhead_line.points = [
                self.x + self.current_time * self.beat_scale, self.y,
                self.x + self.current_time * self.beat_scale, self.top
            ]
    
    def update_from_stream(self, music_stream):
        """Update piano roll from music21 stream"""
        self.notes = []
        if not music_stream:
            return
            
        try:
            for el in music_stream.recurse().notes:
                if hasattr(el, 'offset'):
                    offset = el.offset
                    duration = el.duration.quarterLength
                    velocity = el.volume.velocity if hasattr(el.volume, 'velocity') else 100
                    
                    if isinstance(el, note.Note):
                        self.notes.append((offset, el.pitch.midi, duration, velocity))
                    elif isinstance(el, chord.Chord):
                        for n in el.notes:
                            self.notes.append((offset, n.pitch.midi, duration, velocity))
            
            # Calculate required width
            max_x = max((o + d) * self.beat_scale for o, _, d, _ in self.notes) if self.notes else 0
            self.minimum_width = max_x + dp(100)
        except Exception as e:
            print(f"Error updating piano roll: {e}")

class Music21DAW(App):
    status_text = StringProperty("Ready")
    
    def build(self):
        self.title = "Music21 Visual DAW"
        self.layout = MainLayout()
        
        # Load demo music21 code
        demo_code = '''from music21 import *

# Create a cheerful demo composition
s = stream.Stream()
s.append(tempo.MetronomeMark(number=120))
s.append(dynamics.Dynamic('mf'))

# Melody - Simple C Major arpeggio
melody = [
    note.Note("C4", quarterLength=0.5),
    note.Note("E4", quarterLength=0.5),
    note.Note("G4", quarterLength=0.5),
    note.Note("C5", quarterLength=0.5),
    note.Note("G4", quarterLength=0.5),
    note.Note("E4", quarterLength=0.5),
    note.Note("C4", quarterLength=1.0)
]

# Add melody with increasing velocity
for i, n in enumerate(melody):
    n.volume.velocity = 70 + i*10
    s.insert(i*0.5, n)

# Add simple chord accompaniment
chords = [
    chord.Chord(["C3", "E3", "G3"], quarterLength=2.0),
    chord.Chord(["F3", "A3", "C4"], quarterLength=2.0),
    chord.Chord(["G3", "B3", "D4"], quarterLength=2.0),
    chord.Chord(["C3", "E3", "G3"], quarterLength=2.0)
]

for i, c in enumerate(chords):
    c.volume.velocity = 50
    s.insert(i*2.0, c)

result = s
'''
        self.layout.ids.editor.text = demo_code
        
        self.current_stream = None
        self.media_player = None
        self.temp_file = None
        self.playback_clock = None
        self.playback_start_time = 0
        self.playback_duration = 0

        # Auto-run the demo code
        self.run_code()
        return self.layout

    def run_code(self, *args):
        if not MUSIC21_AVAILABLE:
            self.status_text = "Error: music21 not installed"
            return

        try:
            env = {
                'stream': stream,
                'note': note,
                'tempo': tempo,
                'chord': chord,
                'dynamics': dynamics,
                'articulations': articulations,
                '__builtins__': __builtins__
            }
            local = {}
            
            exec(self.layout.ids.editor.text, env, local)
            
            self.current_stream = local.get('result')
            if self.current_stream:
                self.status_text = "Successfully parsed music stream"
                self.layout.ids.piano_roll.update_from_stream(self.current_stream)
                self.playback_duration = self.current_stream.duration.quarterLength
            else:
                self.status_text = "Warning: No 'result' variable found"
        except Exception as e:
            self.status_text = f"Error: {str(e)}"
            print(traceback.format_exc())

    def export_midi(self, *args):
        if not self.current_stream:
            self.status_text = "No music to export"
            return

        try:
            if ANDROID:
                from android.storage import primary_external_storage_path
                export_dir = primary_external_storage_path()
            else:
                export_dir = os.path.expanduser("~")
                
            midi_file = os.path.join(export_dir, "music21_demo.mid")
            self.current_stream.write('midi', fp=midi_file)
            self.status_text = f"Exported to: {midi_file}"
        except Exception as e:
            self.status_text = f"Export failed: {str(e)}"
            print(traceback.format_exc())

    def play_audio(self, *args):
        if not self.current_stream:
            self.status_text = "No music to play"
            return

        self.stop_audio()
            
        try:
            # Create temp MIDI file
            if ANDROID:
                from android.storage import app_storage_path
                self.temp_file = os.path.join(app_storage_path(), "playback.mid")
            else:
                self.temp_file = os.path.join(tempfile.gettempdir(), "playback.mid")
                
            self.current_stream.write('midi', fp=self.temp_file)

            if ANDROID:
                self._play_android()
            elif platform.system() == "Linux":
                self._play_linux()
            else:
                self.status_text = "Playback not supported"
        except Exception as e:
            self.status_text = f"Playback error: {str(e)}"
            print(traceback.format_exc())

    def _play_android(self):
        try:
            MediaPlayer = autoclass('android.media.MediaPlayer')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')
            
            # Create MediaPlayer instance
            self.media_player = MediaPlayer()
            
            # Prepare URI based on API level
            if SDK_INT >= 24:
                uri = Uri.parse(f"file://{self.temp_file}")
            else:
                file_obj = File(self.temp_file)
                uri = Uri.fromFile(file_obj)
            
            self.media_player.setDataSource(Context, uri)
            
            # Define callback functions
            def on_prepared(mp):
                self.layout.ids.piano_roll.is_playing = True
                self.playback_start_time = Clock.get_time()
                mp.start()
                self._start_playhead_animation()
                self.status_text = "Playing..."
                
            def on_completion(mp):
                Clock.schedule_once(lambda dt: self._on_playback_completed())
                
            def on_error(mp, what, extra):
                Clock.schedule_once(lambda dt: self._on_playback_error(what, extra))
                return True
            
            # Create listener instances
            prepared_listener = OnPreparedListener(on_prepared)
            completion_listener = OnCompletionListener(on_completion)
            error_listener = OnErrorListener(on_error)
            
            # Set listeners
            self.media_player.setOnPreparedListener(prepared_listener)
            self.media_player.setOnCompletionListener(completion_listener)
            self.media_player.setOnErrorListener(error_listener)
            
            # Prepare asynchronously
            self.media_player.prepareAsync()
            
        except Exception as e:
            self.status_text = f"Playback setup error: {str(e)}"
            print(traceback.format_exc())
            if self.media_player:
                self.media_player.release()
                self.media_player = None

    def _start_playhead_animation(self):
        """Start updating the playhead position"""
        if self.playback_clock:
            self.playback_clock.cancel()
        
        def update_playhead(dt):
            elapsed = Clock.get_time() - self.playback_start_time
            progress = elapsed / self.playback_duration
            self.layout.ids.piano_roll.current_time = min(progress * self.playback_duration, self.playback_duration)
            
        self.playback_clock = Clock.schedule_interval(update_playhead, 0.05)

    def _on_playback_completed(self):
        """Called when playback finishes"""
        self.layout.ids.piano_roll.is_playing = False
        self.layout.ids.piano_roll.current_time = 0
        self.status_text = "Playback completed"
        if self.playback_clock:
            self.playback_clock.cancel()
        if self.media_player:
            self.media_player.release()
            self.media_player = None

    def _on_playback_error(self, what, extra):
        """Handle playback errors"""
        self.layout.ids.piano_roll.is_playing = False
        self.status_text = f"Playback error: {what}, {extra}"
        if self.playback_clock:
            self.playback_clock.cancel()
        if self.media_player:
            self.media_player.release()
            self.media_player = None

    def _play_linux(self):
        try:
            self.layout.ids.piano_roll.is_playing = True
            self.playback_start_time = Clock.get_time()
            self._start_playhead_animation()
            
            # Try fluidsynth first
            try:
                soundfont = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
                self.linux_process = subprocess.Popen(
                    ["fluidsynth", "-a", "alsa", "-g", "1.0", soundfont, self.temp_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.status_text = "Playing with FluidSynth"
                return
            except FileNotFoundError:
                pass
                
            # Fallback to timidity
            try:
                self.linux_process = subprocess.Popen(
                    ["timidity", self.temp_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.status_text = "Playing with TiMidity++"
                return
            except FileNotFoundError:
                pass
                
            self.status_text = "No MIDI player found"
            self.layout.ids.piano_roll.is_playing = False
        except Exception as e:
            self.status_text = f"Linux playback error: {str(e)}"
            self.layout.ids.piano_roll.is_playing = False

    def stop_audio(self, *args):
        self.layout.ids.piano_roll.is_playing = False
        self.layout.ids.piano_roll.current_time = 0
        
        if self.playback_clock:
            self.playback_clock.cancel()
            self.playback_clock = None
            
        if ANDROID and self.media_player:
            try:
                self.media_player.stop()
                self.media_player.release()
            except:
                pass
            finally:
                self.media_player = None
                
        elif hasattr(self, 'linux_process'):
            try:
                self.linux_process.terminate()
            except:
                pass
                
        self.status_text = "Playback stopped"

    def on_stop(self):
        """Clean up when app stops"""
        self.stop_audio()
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass

if __name__ == "__main__":
    Music21DAW().run()
