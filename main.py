#!/usr/bin/env python3
"""
Enhanced Music21 Visual DAW - Scale Interval Display with Horizontal Scroll
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.codeinput import CodeInput
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.metrics import dp, sp
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.logger import Logger

import os
import platform
import tempfile
import subprocess
import traceback
import time
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Enhanced logging for debugging
def debug_log(message, level="INFO"):
    """Enhanced logging that works on both desktop and Android"""
    timestamp = time.strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] SriDAW-{level}: {str(message)}"
    
    # Always use Kivy logger
    if level == "ERROR":
        Logger.error(f"SriDAW: {message}")
    elif level == "WARN":
        Logger.warning(f"SriDAW: {message}")
    else:
        Logger.info(f"SriDAW: {message}")
    
    # Also print to stdout for ADB logcat
    print(log_msg)
    
    # On Android, also log to system
    if ANDROID:
        try:
            import android
            android.log(log_msg)
        except:
            pass

debug_log("Starting application...")

# Detect Android environment
ANDROID = False
SDK_INT = 0
try:
    from jnius import autoclass, cast, PythonJavaClass, java_method
    ANDROID = True
    VERSION = autoclass('android.os.Build$VERSION')
    SDK_INT = VERSION.SDK_INT
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = PythonActivity.mActivity
    debug_log(f"Android environment detected, SDK: {SDK_INT}")
except Exception as e:
    debug_log(f"Desktop environment (Android imports failed): {e}")

# Import music21 with error handling
MUSIC21_AVAILABLE = False
try:
    from music21 import stream, note, tempo, chord, dynamics, articulations
    MUSIC21_AVAILABLE = True
    debug_log("music21 imported successfully!")
except ImportError as e:
    debug_log(f"music21 import failed: {e}", "ERROR")
    # Create dummy modules to prevent crashes
    class DummyModule:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    stream = note = tempo = chord = dynamics = articulations = DummyModule()

# Font registration with better error handling
def register_fonts():
    try:
        if ANDROID:
            font_paths = [
                '/system/fonts/RobotoMono-Regular.ttf',
                '/system/fonts/DroidSansMono.ttf',
                '/system/fonts/monospace.ttf',
            ]
        else:
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                '/System/Library/Fonts/Monaco.ttf',
                '/Windows/Fonts/consola.ttf',
            ]
        
        for path in font_paths:
            if os.path.exists(path):
                LabelBase.register(name="Mono", fn_regular=path)
                debug_log(f"Using font: {path}")
                return True
        
        # Fallback to default
        LabelBase.register(name="Mono", fn_regular=LabelBase.default_font)
        debug_log("Using default font")
        return True
    except Exception as e:
        debug_log(f"Font registration failed: {e}", "ERROR")
        return False

register_fonts()

# Android MediaPlayer Listeners
if ANDROID:
    try:
        class OnPreparedListener(PythonJavaClass):
            __javainterfaces__ = ['android/media/MediaPlayer$OnPreparedListener']
            __javacontext__ = 'app'

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method('(Landroid/media/MediaPlayer;)V')
            def onPrepared(self, mp):
                try:
                    self.callback(mp)
                except Exception as e:
                    Logger.error(f"SriDAW: OnPrepared error: {e}")

        class OnCompletionListener(PythonJavaClass):
            __javainterfaces__ = ['android/media/MediaPlayer$OnCompletionListener']
            __javacontext__ = 'app'

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method('(Landroid/media/MediaPlayer;)V')
            def onCompletion(self, mp):
                try:
                    self.callback(mp)
                except Exception as e:
                    Logger.error(f"SriDAW: OnCompletion error: {e}")

        class OnErrorListener(PythonJavaClass):
            __javainterfaces__ = ['android/media/MediaPlayer$OnErrorListener']
            __javacontext__ = 'app'

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method('(Landroid/media/MediaPlayer;II)Z')
            def onError(self, mp, what, extra):
                try:
                    return self.callback(mp, what, extra)
                except Exception as e:
                    Logger.error(f"SriDAW: OnError error: {e}")
                    return True
    except Exception as e:
        Logger.error(f"SriDAW: Failed to create Android listeners: {e}")

# UI Layout Definition with error handling
try:
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
            font_size: sp(14)
            background_color: 0.1, 0.1, 0.1, 1
            foreground_color: 0.9, 0.9, 0.9, 1
            line_spacing: sp(4)
            scroll_distance: dp(100)
            cursor_color: 1, 0.5, 0, 1
            cursor_width: dp(2)
            selection_color: 0.2, 0.5, 0.8, 0.4
            auto_indent: True
            tab_width: 4
            use_bubble: True
            do_wrap: False

    BoxLayout:
        size_hint_y: 0.4
        ScrollView:
            id: piano_scroll
            do_scroll_x: True
            do_scroll_y: True
            bar_width: dp(10)
            bar_color: 1, 1, 1, 0.5
            bar_inactive_color: 0.7, 0.7, 0.7, 0.5
            scroll_type: ['bars', 'content']
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
            size_hint_x: 0.12
            background_color: 0.2, 0.8, 0.2, 1
            on_press: app.run_code()

        Button:
            text: 'Play'
            size_hint_x: 0.12
            background_color: 0.2, 0.5, 0.9, 1
            on_press: app.play_audio()

        Button:
            text: 'Stop'
            size_hint_x: 0.12
            background_color: 0.9, 0.2, 0.2, 1
            on_press: app.stop_audio()

        Button:
            text: 'Export'
            size_hint_x: 0.12
            background_color: 0.8, 0.6, 0.2, 1
            on_press: app.export_midi()

        Button:
            text: 'Save'
            size_hint_x: 0.12
            background_color: 0.4, 0.4, 0.8, 1
            on_press: app.save_code()

        Button:
            text: 'Load'
            size_hint_x: 0.12
            background_color: 0.6, 0.4, 0.8, 1
            on_press: app.load_code()

        Label:
            id: status_label
            text: app.status_text
            size_hint_x: 0.28
            halign: 'left'
            valign: 'middle'
            text_size: self.width, None
            padding: dp(5), 0
            canvas.before:
                Color:
                    rgba: 0.1, 0.1, 0.15, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

<NoteDetailsPopup>:
    size_hint: 0.8, 0.6
    title: 'Note Details'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        Label:
            text: root.note_details
            font_name: 'Mono'
            font_size: sp(14)
            text_size: self.width, None
            size_hint_y: 0.9
        Button:
            text: 'Close'
            size_hint_y: 0.1
            on_press: root.dismiss()
''')
    debug_log("UI layout loaded successfully")
except Exception as e:
    debug_log(f"Failed to load UI layout: {e}", "ERROR")
    # Create minimal fallback layout
    Builder.load_string('''
<MainLayout>:
    orientation: 'vertical'
    Label:
        text: 'SriDAW - Loading Error'
    Button:
        text: 'OK'
        size_hint_y: None
        height: dp(50)
''')

class MainLayout(BoxLayout):
    pass

class NoteDetailsPopup(Popup):
    note_details = StringProperty("")

class PianoRollWidget(BoxLayout):
    notes = ListProperty([])
    beat_scale = NumericProperty(dp(50))
    pitch_range = range(36, 84)  # MIDI note range (C2 to B5)
    current_time = NumericProperty(0)
    is_playing = BooleanProperty(False)
    note_labels = {}
    scale_pitches = ListProperty([])
    scale_intervals = ListProperty([])
    drum_pitches = ListProperty([])
    visible_pitches = ListProperty([])
    minimum_width = NumericProperty(dp(800))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.size_hint_y = None
            self.height = len(self.pitch_range) * dp(18)
            self.bind(
                size=self._update_canvas,
                pos=self._update_canvas,
                notes=self._update_canvas,
                current_time=self._update_playhead,
                scale_pitches=self._update_canvas,
                scale_intervals=self._update_canvas,
                drum_pitches=self._update_canvas,
                visible_pitches=self._update_canvas
            )
            self.playhead_line = None
            self._key_colors = {}
            self._init_key_colors()
            self.selected_note = None
            self.note_popup = None
            self.scroll_view = None
            debug_log("PianoRollWidget initialized")
        except Exception as e:
            debug_log(f"PianoRollWidget init error: {e}", "ERROR")

    def _init_key_colors(self):
        """Initialize colors for piano keys (black/white)"""
        try:
            black_keys = {1, 3, 6, 8, 10}  # Semitone offsets for black keys
            for pitch in self.pitch_range:
                if (pitch % 12) in black_keys:
                    self._key_colors[pitch] = (0.15, 0.15, 0.15, 1)  # Black keys
                else:
                    self._key_colors[pitch] = (0.95, 0.95, 0.95, 1)  # White keys
        except Exception as e:
            Logger.error(f"SriDAW: Key color init error: {e}")

    def on_touch_down(self, touch):
        try:
            if self.collide_point(*touch.pos) and not self.is_playing:
                # Find which note was clicked
                for i, (offset, pitch, duration, velocity) in enumerate(self.notes):
                    if pitch not in self.visible_pitches:
                        continue

                    pitch_index = self.visible_pitches.index(pitch)
                    x = self.x + offset * self.beat_scale
                    y = self.y + pitch_index * dp(18)
                    w = duration * self.beat_scale
                    h = dp(17)

                    if (x <= touch.x <= x + w) and (y <= touch.y <= y + h):
                        self.selected_note = i
                        self.show_note_details(offset, pitch, duration, velocity)
                        return True
        except Exception as e:
            debug_log(f"Touch error: {e}", "ERROR")

        return super().on_touch_down(touch)

    def show_note_details(self, offset, pitch, duration, velocity):
        try:
            pitch_name = self.midi_to_note_name(pitch)

            # Find interval information if available
            interval_info = ""
            for interval in self.scale_intervals:
                if interval[0] == pitch:
                    interval_info = f"\nInterval: {interval[1]} -> {interval[2]} ({interval[3]} semitones)"
                    break

            # Check if drum note
            drum_info = "\nDrum Note" if pitch in self.drum_pitches else ""

            details = (
                f"Pitch: {pitch_name} ({pitch})\n"
                f"Offset: {offset:.2f} beats\n"
                f"Duration: {duration:.2f} beats\n"
                f"Velocity: {velocity}"
                f"{drum_info}"
                f"{interval_info}"
            )

            if not self.note_popup:
                self.note_popup = NoteDetailsPopup()

            self.note_popup.note_details = details
            self.note_popup.open()
        except Exception as e:
            debug_log(f"Note details error: {e}", "ERROR")

    def midi_to_note_name(self, midi_note):
        """Convert MIDI note number to note name"""
        try:
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = midi_note // 12 - 1
            note_index = midi_note % 12
            return f"{note_names[note_index]}{octave}"
        except:
            return f"Note{midi_note}"

    def get_interval_name(self, semitones):
        """Convert semitone distance to interval name"""
        try:
            intervals = {
                0: "P1", 1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4",
                6: "TT", 7: "P5", 8: "m6", 9: "M6", 10: "m7", 11: "M7", 12: "P8"
            }
            return intervals.get(abs(semitones), f"{semitones}st")
        except:
            return "?"

    def _update_canvas(self, *args):
        try:
            self.canvas.after.clear()
            self.note_labels = {}

            # Calculate minimum width based on notes
            if self.notes:
                try:
                    max_beat = max((offset + duration) for offset, _, duration, _ in self.notes if duration > 0)
                except ValueError:
                    max_beat = 10.0
                self.minimum_width = max(dp(800), max_beat * self.beat_scale + dp(100))
            else:
                self.minimum_width = dp(800)

            with self.canvas.after:
                # Draw piano keys background only for visible pitches
                for i, pitch in enumerate(self.visible_pitches):
                    y = self.y + i * dp(18)
                    Color(*self._key_colors.get(pitch, (0.95, 0.95, 0.95, 1)))
                    Rectangle(pos=(self.x, y), size=(self.width, dp(18)))

                    # Draw key border
                    Color(0.3, 0.3, 0.3, 1)
                    Line(rectangle=(self.x, y, self.width, dp(18)), width=0.5)

                    # Draw pitch label
                    note_name = self.midi_to_note_name(pitch)
                    Color(1, 0.5, 0.5, 1) if pitch in self.drum_pitches else Color(0.1, 0.1, 0.1, 1)
                    self.draw_text(note_name, self.x + dp(5), y + dp(3), dp(12))

                # Highlight scale rows
                if self.scale_pitches:
                    Color(1.0, 0.9, 0.2, 0.15)  # Semi-transparent yellow
                    for pitch in self.scale_pitches:
                        if pitch in self.visible_pitches:
                            i = self.visible_pitches.index(pitch)
                            Rectangle(pos=(self.x, self.y + i * dp(18)), size=(self.width, dp(18)))

                # Draw measure/beat lines
                Color(0.4, 0.4, 0.4, 0.6)
                for beat in range(int(self.minimum_width / self.beat_scale) + 2):
                    x = self.x + beat * self.beat_scale
                    Line(points=[x, self.y, x, self.top], width=1)
                    if beat % 4 == 0:
                        self.draw_text(str(beat), x + dp(2), self.y + self.height + dp(2), dp(12))

                # Draw notes
                for i, (offset, pitch, duration, velocity) in enumerate(self.notes):
                    if pitch in self.visible_pitches:
                        pitch_index = self.visible_pitches.index(pitch)
                        x = self.x + offset * self.beat_scale
                        y = self.y + pitch_index * dp(18)
                        w = duration * self.beat_scale
                        h = dp(17)
                        
                        highlight = 1.0 if i == self.selected_note else 0.8
                        if pitch in self.drum_pitches: 
                            Color(0.9, 0.2, 0.2, highlight)
                        elif velocity == 101: 
                            Color(1.0, 0.9, 0.2, highlight)
                        elif velocity == 102: 
                            Color(0.2, 0.9, 0.3, highlight)
                        elif velocity == 103: 
                            Color(0.2, 0.5, 1.0, highlight)
                        else: 
                            Color(0.8, 0.5, 0.5 + (velocity / 200), highlight)

                        self.draw_rounded_rect(x, y, w, h, dp(3))
                        Color(0, 0, 0, 0.3)
                        Line(rounded_rectangle=(x, y, w, h, dp(3)), width=1)
                        
                        if w > dp(20):
                            note_name = self.midi_to_note_name(pitch)
                            Color(0.1, 0.1, 0.1, 1) if velocity == 101 else Color(1, 1, 1, 1)
                            self.draw_text(note_name, x + dp(3), y + dp(2), dp(12))

        except Exception as e:
            debug_log(f"Canvas update error: {e}", "ERROR")

    def draw_rounded_rect(self, x, y, w, h, r):
        try:
            if w < 2 * r or h < 2 * r: 
                r = min(w / 2, h / 2)
            Rectangle(pos=(x + r, y), size=(w - 2*r, h))
            Rectangle(pos=(x, y + r), size=(w, h - 2*r))
            Ellipse(pos=(x, y), size=(2*r, 2*r))
            Ellipse(pos=(x + w - 2*r, y), size=(2*r, 2*r))
            Ellipse(pos=(x, y + h - 2*r), size=(2*r, 2*r))
            Ellipse(pos=(x + w - 2*r, y + h - 2*r), size=(2*r, 2*r))
        except Exception as e:
            debug_log(f"Draw rect error: {e}", "ERROR")

    def draw_text(self, text, x, y, font_size, center=False):
        try:
            from kivy.core.text import Label as CoreLabel
            label = CoreLabel(text=str(text), font_size=font_size, font_name='Mono', color=(1,1,1,1))
            label.refresh()
            texture = label.texture
            if not texture: 
                return
            pos = (x - texture.width/2, y - texture.height/2) if center else (x, y)
            Rectangle(texture=texture, pos=pos, size=texture.size)
        except Exception as e:
            debug_log(f"Draw text error: {e}", "ERROR")

    def _update_playhead(self, *args):
        try:
            if self.playhead_line: 
                self.canvas.after.remove(self.playhead_line)
            x_pos = self.x + self.current_time * self.beat_scale
            with self.canvas.after:
                Color(1, 0, 0, 0.9)
                self.playhead_line = Line(points=[x_pos, self.y, x_pos, self.top], width=dp(2))
            
            # Auto-scroll
            if self.scroll_view and self.is_playing:
                vp_width = self.scroll_view.width
                if self.width > vp_width:
                    scroll_x_norm = max(0, (x_pos - vp_width / 2) / (self.width - vp_width))
                    self.scroll_view.scroll_x = min(1.0, scroll_x_norm)
        except Exception as e:
            debug_log(f"Playhead update error: {e}", "ERROR")

    def update_from_stream(self, music_stream):
        try:
            self.notes, self.scale_pitches, self.scale_intervals, self.drum_pitches, self.visible_pitches = [], [], [], [], []
            if not music_stream: 
                return
            
            all_pitches, scale_notes_timed = set(), []
            for el in music_stream.recurse().notes:
                if not hasattr(el, 'offset'): 
                    continue
                
                vel = getattr(el.volume, 'velocity', 100) if hasattr(el, 'volume') else 100
                is_drum = (vel == 104)
                is_scale = (vel == 101)
                
                notes_to_add = getattr(el, 'notes', [el])
                for n in notes_to_add:
                    pitch_midi = getattr(n.pitch, 'midi', 60)
                    all_pitches.add(pitch_midi)
                    if is_drum and pitch_midi not in self.drum_pitches: 
                        self.drum_pitches.append(pitch_midi)
                    if is_scale:
                        if pitch_midi not in self.scale_pitches: 
                            self.scale_pitches.append(pitch_midi)
                        scale_notes_timed.append({'offset': el.offset, 'pitch': pitch_midi})
                    
                    duration = getattr(el.duration, 'quarterLength', 1.0)
                    self.notes.append((el.offset, pitch_midi, duration, vel))

            # Calculate intervals
            scale_notes_timed.sort(key=lambda x: x['offset'])
            for i in range(1, len(scale_notes_timed)):
                prev_n, curr_n = scale_notes_timed[i-1], scale_notes_timed[i]
                if abs(curr_n['offset'] - prev_n['offset']) < 1.0:
                    semitones = curr_n['pitch'] - prev_n['pitch']
                    if semitones != 0:
                        self.scale_intervals.append((prev_n['pitch'], curr_n['pitch'], semitones, prev_n['offset'], curr_n['offset']))

            self.visible_pitches = sorted(list(all_pitches.union(self.scale_pitches, self.drum_pitches)))
            self.notes.sort(key=lambda x: x[1])
            self.height = max(dp(100), len(self.visible_pitches) * dp(18))
            
        except Exception as e:
            debug_log(f"Stream update error: {e}", "ERROR")

class Music21DAW(App):
    status_text = StringProperty("Ready")

    def build(self):
        try:
            debug_log("Building app...")
            self.title = "Music21 Visual DAW"
            self.layout = MainLayout()
            
            # Get status label safely
            try:
                self.status_label = self.layout.ids.status_label
            except:
                self.status_label = None

            demo_code = '''from music21 import *

# Create a demo composition
s = stream.Stream()
s.append(tempo.MetronomeMark(number=100))
s.append(dynamics.Dynamic('mf'))

# Simple scale
scale_notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
for i, p in enumerate(scale_notes):
    n = note.Note(p, quarterLength=0.5)
    n.volume.velocity = 101  # Yellow (scale)
    s.insert(i * 0.5, n)

result = s
'''
            
            try:
                self.layout.ids.editor.text = demo_code
            except:
                Logger.error("SriDAW: Could not set editor text")

            self.current_stream = None
            self.media_player = None
            self.temp_file = None
            self.playback_clock = None
            self.playback_start_time = 0
            self.playback_duration = 0
            self.bpm = 60
            self.beat_duration = 1.0
            
            # Run demo code after a delay
            Clock.schedule_once(lambda dt: self.run_code(), 1.0)
            
            debug_log("App built successfully")
            return self.layout
            
        except Exception as e:
            debug_log(f"Build error: {e}", "ERROR")
            # Return minimal layout on error
            from kivy.uix.label import Label
            return Label(text=f"SriDAW Error: {e}")

    def run_code(self, *args):
        try:
            if not MUSIC21_AVAILABLE:
                self.status_text = "Error: music21 not available."
                return
                
            self.stop_audio()
            
            try:
                editor_text = self.layout.ids.editor.text
            except:
                editor_text = "result = stream.Stream()"
            
            env = {
                'stream': stream, 
                'note': note, 
                'tempo': tempo, 
                'chord': chord, 
                'dynamics': dynamics, 
                'articulations': articulations
            }
            local = {}
            
            exec(editor_text, env, local)
            self.current_stream = local.get('result')
            
            if self.current_stream:
                self.status_text = "Successfully parsed music stream"
                try:
                    self.layout.ids.piano_roll.scroll_view = self.layout.ids.piano_scroll
                    self.layout.ids.piano_roll.update_from_stream(self.current_stream)
                except:
                    pass
                
                # Get tempo
                try:
                    tempo_marks = self.current_stream.flat.getElementsByClass(tempo.MetronomeMark)
                    self.bpm = tempo_marks[0].number if tempo_marks else 60
                    self.beat_duration = 60.0 / self.bpm
                    self.playback_duration = self.current_stream.duration.quarterLength
                except:
                    self.bpm = 60
                    self.beat_duration = 1.0
                    self.playback_duration = 10.0
            else:
                self.status_text = "Warning: No 'result' stream found"
                try:
                    self.layout.ids.piano_roll.update_from_stream(None)
                except:
                    pass
                    
        except Exception as e:
            self.status_text = f"Execution Error: {str(e)}"
            Logger.error(f"SriDAW: Run code error: {e}")

    def export_midi(self, *args):
        try:
            if not self.current_stream:
                self.status_text = "No music to export"
                return
                
            if ANDROID:
                try:
                    from android.storage import primary_external_storage_path
                    export_dir = os.path.join(primary_external_storage_path(), "Download")
                    os.makedirs(export_dir, exist_ok=True)
                except:
                    export_dir = "/sdcard/Download"
                    os.makedirs(export_dir, exist_ok=True)
            else:
                export_dir = os.path.expanduser("~")
            
            midi_file = os.path.join(export_dir, f"sridaw_export_{int(time.time())}.mid")
            self.current_stream.write('midi', fp=midi_file)
            self.status_text = f"Exported to: {midi_file}"
            
        except Exception as e:
            self.status_text = f"Export failed: {str(e)}"
            Logger.error(f"SriDAW: Export error: {e}")

    def play_audio(self, *args):
        try:
            if not self.current_stream:
                self.status_text = "No music to play"
                return
                
            self.stop_audio()
            
            # Create temp file
            if ANDROID:
                try:
                    temp_dir = Context.getCacheDir().getAbsolutePath()
                except:
                    temp_dir = "/data/data/org.example.sridaw/cache"
                    os.makedirs(temp_dir, exist_ok=True)
            else:
                temp_dir = tempfile.gettempdir()
                
            self.temp_file = os.path.join(temp_dir, "playback.mid")
            self.current_stream.write('midi', fp=self.temp_file)

            if ANDROID: 
                self._play_android()
            else: 
                self.status_text = "Playback not supported on this platform"
                
        except Exception as e:
            self.status_text = f"Playback Error: {str(e)}"
            Logger.error(f"SriDAW: Play error: {e}")

    def _play_android(self):
        try:
            MediaPlayer = autoclass('android.media.MediaPlayer')
            self.media_player = MediaPlayer()
            self.media_player.setDataSource(self.temp_file)

            def on_prepared(mp):
                try:
                    self.layout.ids.piano_roll.is_playing = True
                    self.playback_start_time = time.time()
                    mp.start()
                    self._start_playhead_animation()
                    self.status_text = "Playing..."
                except Exception as e:
                    Logger.error(f"SriDAW: Prepared error: {e}")

            def on_completion(mp):
                self.stop_audio()

            def on_error(mp, what, extra):
                Logger.error(f"SriDAW: MediaPlayer error: {what}, {extra}")
                self.stop_audio()
                return True

            self.media_player.setOnPreparedListener(OnPreparedListener(on_prepared))
            self.media_player.setOnCompletionListener(OnCompletionListener(on_completion))
            self.media_player.setOnErrorListener(OnErrorListener(on_error))
            self.media_player.prepareAsync()
            
        except Exception as e:
            self.status_text = f"Android Playback Error: {e}"
            Logger.error(f"SriDAW: Android play error: {e}")

    def _start_playhead_animation(self):
        try:
            self.playback_clock = Clock.schedule_interval(self._update_playback_progress, 1/30.)
        except Exception as e:
            Logger.error(f"SriDAW: Playhead animation error: {e}")

    def _update_playback_progress(self, dt):
        try:
            elapsed = time.time() - self.playback_start_time
            current_beat = elapsed / self.beat_duration
            if current_beat > self.playback_duration:
                self.stop_audio()
            else:
                self.layout.ids.piano_roll.current_time = current_beat
        except Exception as e:
            Logger.error(f"SriDAW: Playback progress error: {e}")

    def stop_audio(self, *args):
        try:
            if self.playback_clock:
                self.playback_clock.cancel()
                self.playback_clock = None
            
            if self.media_player:
                try:
                    if self.media_player.isPlaying(): 
                        self.media_player.stop()
                    self.media_player.release()
                except:
                    pass
                finally:
                    self.media_player = None
            
            # Clean up temp file
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.remove(self.temp_file)
                except:
                    pass
                self.temp_file = None
                    
            try:
                self.layout.ids.piano_roll.is_playing = False
                self.layout.ids.piano_roll.current_time = 0
            except:
                pass
                
            if "Playing" in self.status_text:
                self.status_text = "Playback stopped"
                
        except Exception as e:
            Logger.error(f"SriDAW: Stop error: {e}")

    def save_code(self):
        try:
            if ANDROID:
                try:
                    from android.storage import primary_external_storage_path
                    save_path = os.path.join(primary_external_storage_path(), "Download", "sridaw_code.py")
                except:
                    save_path = "/sdcard/Download/sridaw_code.py"
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
            else:
                save_path = "last_music21_code.py"
                
            with open(save_path, "w") as f: 
                f.write(self.layout.ids.editor.text)
            self.status_text = f"Code saved to {save_path}"
            
        except Exception as e: 
            self.status_text = f"Save error: {e}"
            Logger.error(f"SriDAW: Save error: {e}")

    def load_code(self):
        try:
            if ANDROID:
                try:
                    from android.storage import primary_external_storage_path
                    load_path = os.path.join(primary_external_storage_path(), "Download", "sridaw_code.py")
                except:
                    load_path = "/sdcard/Download/sridaw_code.py"
            else:
                load_path = "last_music21_code.py"
                
            if os.path.exists(load_path):
                with open(load_path, "r") as f: 
                    self.layout.ids.editor.text = f.read()
                self.status_text = "Code loaded. Press 'Run'."
            else: 
                self.status_text = "No saved code found."
                
        except Exception as e: 
            self.status_text = f"Load error: {e}"
            Logger.error(f"SriDAW: Load error: {e}")

    def on_stop(self):
        try:
            self.stop_audio()
            if self.temp_file and os.path.exists(self.temp_file):
                try: 
                    os.remove(self.temp_file)
                except: 
                    pass
        except Exception as e:
            Logger.error(f"SriDAW: Stop cleanup error: {e}")

if __name__ == "__main__":
    try:
        Logger.info("SriDAW: Starting main application")
        Music21DAW().run()
    except Exception as e:
        Logger.error(f"SriDAW: Main error: {e}")
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()