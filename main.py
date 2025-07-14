import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


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

import os
import platform
import tempfile
import subprocess
import traceback
import time

# Conditional imports
try:
    from jnius import autoclass, cast, PythonJavaClass, java_method
    ANDROID = True
    VERSION = autoclass('android.os.Build$VERSION')
    SDK_INT = VERSION.SDK_INT
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = PythonActivity.mActivity
    print("Android environment detected")
except Exception as e:
    ANDROID = False
    SDK_INT = 0
    print(f"Android imports failed (not Android?): {e}")

try:
    from music21 import stream, note, tempo, chord, dynamics, articulations
    MUSIC21_AVAILABLE = True
    print("music21 imported successfully!")
except ImportError:
    MUSIC21_AVAILABLE = False
    print("music21 import failed.")

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
            print(f"Using font: {path}")
            break
    except Exception as e:
        print(f"Font registration failed for {path}: {e}")


if not font_registered:
    LabelBase.register(name="Mono", fn_regular=LabelBase.default_font)
    print("Using default font")

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
            font_size: sp(14)
            background_color: 0.1, 0.1, 0.1, 1
            foreground_color: 0.9, 0.9, 0.9, 1
            line_spacing: sp(4)
            scroll_distance: dp(100)
            cursor_color: 1, 0.5, 0, 1
            cursor_width: dp(2)
            selection_color: 0.2, 0.5, 0.8, 0.4
            base_direction: 'ltr'
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
    scale_pitches = ListProperty([])  # To store pitches that are part of the scale
    scale_intervals = ListProperty([])  # To store interval information
    drum_pitches = ListProperty([])    # To store drum pitches
    visible_pitches = ListProperty([]) # Combined list of pitches to display
    minimum_width = NumericProperty(0)  # For horizontal scrolling

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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

    def _init_key_colors(self):
        """Initialize colors for piano keys (black/white)"""
        black_keys = {1, 3, 6, 8, 10}  # Semitone offsets for black keys
        for pitch in self.pitch_range:
            if (pitch % 12) in black_keys:
                self._key_colors[pitch] = (0.15, 0.15, 0.15, 1)  # Black keys
            else:
                self._key_colors[pitch] = (0.95, 0.95, 0.95, 1)  # White keys

    def on_touch_down(self, touch):
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

        return super().on_touch_down(touch)

    def show_note_details(self, offset, pitch, duration, velocity):
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

    def midi_to_note_name(self, midi_note):
        """Convert MIDI note number to note name"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi_note // 12 - 1
        note_index = midi_note % 12
        return f"{note_names[note_index]}{octave}"

    def get_interval_name(self, semitones):
        """Convert semitone distance to interval name"""
        intervals = {
            0: "P1", 1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4",
            6: "TT", 7: "P5", 8: "m6", 9: "M6", 10: "m7", 11: "M7", 12: "P8"
        }
        return intervals.get(abs(semitones), f"{semitones}st")

    def _update_canvas(self, *args):
        self.canvas.after.clear()
        self.note_labels = {}

        # Calculate minimum width based on notes
        max_beat = max((offset + duration) for offset, _, duration, _ in self.notes) if self.notes else 10
        self.minimum_width = max_beat * self.beat_scale + dp(100)  # Add padding

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

            # Draw interval lines and labels
            if self.scale_intervals:
                for start_pitch, end_pitch, semitones, _, _ in self.scale_intervals:
                    if start_pitch in self.visible_pitches and end_pitch in self.visible_pitches:
                        start_i = self.visible_pitches.index(start_pitch)
                        end_i = self.visible_pitches.index(end_pitch)
                        start_y = self.y + start_i * dp(18) + dp(9)
                        end_y = self.y + end_i * dp(18) + dp(9)
                        
                        Color(0.9, 0.2, 0.9, 0.7) # Purple line
                        Line(points=[self.x + dp(10), start_y, self.x + dp(40), end_y], width=dp(1.5))
                        
                        interval_name = self.get_interval_name(semitones)
                        self.draw_text(interval_name, self.x + dp(25), (start_y + end_y)/2, dp(12), center=True)

            # Draw notes
            for i, (offset, pitch, duration, velocity) in enumerate(self.notes):
                if pitch in self.visible_pitches:
                    pitch_index = self.visible_pitches.index(pitch)
                    x = self.x + offset * self.beat_scale
                    y = self.y + pitch_index * dp(18)
                    w = duration * self.beat_scale
                    h = dp(17)
                    
                    highlight = 1.0 if i == self.selected_note else 0.8
                    if pitch in self.drum_pitches: Color(0.9, 0.2, 0.2, highlight)
                    elif velocity == 101: Color(1.0, 0.9, 0.2, highlight)
                    elif velocity == 102: Color(0.2, 0.9, 0.3, highlight)
                    elif velocity == 103: Color(0.2, 0.5, 1.0, highlight)
                    else: Color(0.8, 0.5, 0.5 + (velocity / 200), highlight)

                    self.draw_rounded_rect(x, y, w, h, dp(3))
                    Color(0, 0, 0, 0.3)
                    Line(rounded_rectangle=(x, y, w, h, dp(3)), width=1)
                    
                    if w > dp(20):
                        note_name = self.midi_to_note_name(pitch)
                        Color(0.1, 0.1, 0.1, 1) if velocity == 101 else Color(1, 1, 1, 1)
                        self.draw_text(note_name, x + dp(3), y + dp(2), dp(12))

            # Playhead line
            if self.is_playing:
                Color(1, 0.2, 0.2, 0.9)
                self.playhead_line = Line(points=[self.x + self.current_time * self.beat_scale, self.y,
                                                  self.x + self.current_time * self.beat_scale, self.top],
                                          width=dp(3))

    def draw_rounded_rect(self, x, y, w, h, r):
        if w < 2 * r or h < 2 * r: r = min(w / 2, h / 2)
        Rectangle(pos=(x + r, y), size=(w - 2*r, h))
        Rectangle(pos=(x, y + r), size=(w, h - 2*r))
        Ellipse(pos=(x, y), size=(2*r, 2*r))
        Ellipse(pos=(x + w - 2*r, y), size=(2*r, 2*r))
        Ellipse(pos=(x, y + h - 2*r), size=(2*r, 2*r))
        Ellipse(pos=(x + w - 2*r, y + h - 2*r), size=(2*r, 2*r))

    def draw_text(self, text, x, y, font_size, center=False):
        from kivy.core.text import Label as CoreLabel
        label = CoreLabel(text=text, font_size=font_size, font_name='Mono', color=(1,1,1,1))
        label.refresh()
        texture = label.texture
        if not texture: return
        pos = (x - texture.width/2, y - texture.height/2) if center else (x, y)
        Rectangle(texture=texture, pos=pos, size=texture.size)

    def _update_playhead(self, *args):
        if self.playhead_line: self.canvas.after.remove(self.playhead_line)
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

    def update_from_stream(self, music_stream):
        self.notes, self.scale_pitches, self.scale_intervals, self.drum_pitches, self.visible_pitches = [], [], [], [], []
        if not music_stream: return
        
        try:
            all_pitches, scale_notes_timed = set(), []
            for el in music_stream.recurse().notes:
                if not hasattr(el, 'offset'): continue
                
                vel = el.volume.velocity if hasattr(el.volume, 'velocity') else 100
                is_drum = (vel == 104)
                is_scale = (vel == 101)
                
                notes_to_add = el.notes if isinstance(el, chord.Chord) else [el]
                for n in notes_to_add:
                    all_pitches.add(n.pitch.midi)
                    if is_drum and n.pitch.midi not in self.drum_pitches: self.drum_pitches.append(n.pitch.midi)
                    if is_scale:
                        if n.pitch.midi not in self.scale_pitches: self.scale_pitches.append(n.pitch.midi)
                        scale_notes_timed.append({'offset': el.offset, 'pitch': n.pitch.midi})
                    
                    self.notes.append((el.offset, n.pitch.midi, el.duration.quarterLength, vel))

            scale_notes_timed.sort(key=lambda x: x['offset'])
            for i in range(1, len(scale_notes_timed)):
                prev_n, curr_n = scale_notes_timed[i-1], scale_notes_timed[i]
                if abs(curr_n['offset'] - prev_n['offset']) < 1.0: # Temporal proximity
                    semitones = curr_n['pitch'] - prev_n['pitch']
                    if semitones != 0:
                        self.scale_intervals.append((prev_n['pitch'], curr_n['pitch'], semitones, prev_n['offset'], curr_n['offset']))

            self.visible_pitches = sorted(list(all_pitches.union(self.scale_pitches, self.drum_pitches)))
            self.notes.sort(key=lambda x: x[1])
            self.height = max(dp(100), len(self.visible_pitches) * dp(18))
        except Exception as e:
            print(f"Error updating piano roll: {e}\n{traceback.format_exc()}")

class Music21DAW(App):
    status_text = StringProperty("Ready")

    def build(self):
        self.title = "Music21 Visual DAW"
        self.layout = MainLayout()
        self.status_label = self.layout.ids.status_label

        demo_code = '''from music21 import *

# Create a demo composition
s = stream.Stream()
s.append(tempo.MetronomeMark(number=100))
s.append(dynamics.Dynamic('mf'))

# 🎵 C Natural Minor scale with special velocity
scale_notes = ["C4", "D4", "Eb4", "F4", "G4", "Ab4", "Bb4", "C5"]
for i, p in enumerate(scale_notes):
    n = note.Note(p, quarterLength=0.5)
    n.volume.velocity = 101  # Yellow (scale)
    s.insert(i * 0.5, n)

# 🥁 Simple drum pattern
drum_map = {'kick': 36, 'snare': 38, 'hi-hat': 42}
for i in range(8):
    s.insert(i, note.Note(drum_map['kick'], quarterLength=1.0, volume=dynamics.Volume(velocity=104)))
    s.insert(i + 0.5, note.Note(drum_map['hi-hat'], quarterLength=0.5, volume=dynamics.Volume(velocity=104)))
s.insert(1, note.Note(drum_map['snare'], quarterLength=1.0, volume=dynamics.Volume(velocity=104)))
s.insert(3, note.Note(drum_map['snare'], quarterLength=1.0, volume=dynamics.Volume(velocity=104)))

# 🎶 Chords (Cmin, Fmin, Gmin)
chords = [("C3", "Eb3", "G3"), ("F3", "Ab3", "C4"), ("G3", "Bb3", "D4")]
for i, c_notes in enumerate(chords):
    c = chord.Chord(c_notes, quarterLength=2.0)
    c.volume.velocity = 102  # Green (chords)
    s.insert(i * 2.0, c)

# 🎤 Melody phrase
melody_notes = ["G4", "F4", "Eb4", "C4"]
for i, p in enumerate(melody_notes):
    n = note.Note(p, quarterLength=1.0)
    n.volume.velocity = 103  # Blue (melody)
    s.insert(i * 1.0 + 1.0, n)

result = s
'''
        self.layout.ids.editor.text = demo_code
        self.current_stream, self.media_player, self.temp_file, self.playback_clock = None, None, None, None
        self.playback_start_time, self.playback_duration, self.bpm, self.beat_duration = 0, 0, 60, 1.0
        Clock.schedule_once(lambda dt: self.run_code(), 0.5)
        return self.layout

    def run_code(self, *args):
        if not MUSIC21_AVAILABLE:
            self.status_text = "Error: music21 not available."
            return
        self.stop_audio()
        try:
            env = {'stream': stream, 'note': note, 'tempo': tempo, 'chord': chord, 'dynamics': dynamics, 'articulations': articulations}
            local = {}
            exec(self.layout.ids.editor.text, env, local)
            self.current_stream = local.get('result')
            
            if self.current_stream:
                self.status_text = "Successfully parsed music stream"
                self.layout.ids.piano_roll.scroll_view = self.layout.ids.piano_scroll
                self.layout.ids.piano_roll.update_from_stream(self.current_stream)
                
                self.bpm = next((tm.number for tm in self.current_stream.flat.getElementsByClass(tempo.MetronomeMark) if tm.number), 60)
                self.beat_duration = 60.0 / self.bpm
                self.playback_duration = self.current_stream.duration.quarterLength
            else:
                self.status_text = "Warning: No 'result' stream found"
                self.layout.ids.piano_roll.update_from_stream(None)
        except Exception as e:
            self.status_text = f"Execution Error: {str(e)}"
            print(traceback.format_exc())

    def export_midi(self, *args):
        if not self.current_stream:
            self.status_text = "No music to export"
            return
        try:
            if ANDROID:
                from android.storage import primary_external_storage_path
                export_dir = os.path.join(primary_external_storage_path(), "Download")
                os.makedirs(export_dir, exist_ok=True)
            else:
                export_dir = os.path.expanduser("~")
            
            midi_file = os.path.join(export_dir, f"sridaw_export_{int(time.time())}.mid")
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
            temp_dir = tempfile.gettempdir()
            if ANDROID:
                temp_dir = Context.getCacheDir().getAbsolutePath()
            self.temp_file = os.path.join(temp_dir, "playback.mid")
            self.current_stream.write('midi', fp=self.temp_file)

            if ANDROID: self._play_android()
            elif platform.system() == "Linux": self._play_linux()
            else: self.status_text = "Playback not supported on this OS"
        except Exception as e:
            self.status_text = f"Playback Error: {str(e)}"
            print(traceback.format_exc())

    def _play_android(self):
        try:
            MediaPlayer = autoclass('android.media.MediaPlayer')
            self.media_player = MediaPlayer()
            self.media_player.setDataSource(self.temp_file)

            def on_prepared(mp):
                self.layout.ids.piano_roll.is_playing = True
                self.playback_start_time = time.time()
                mp.start()
                self._start_playhead_animation()
                self.status_text = "Playing..."

            self.media_player.setOnPreparedListener(OnPreparedListener(on_prepared))
            self.media_player.setOnCompletionListener(OnCompletionListener(lambda mp: self.stop_audio()))
            self.media_player.setOnErrorListener(OnErrorListener(lambda mp, w, e: self.stop_audio()))
            self.media_player.prepareAsync()
        except Exception as e:
            self.status_text = f"Android Playback Error: {e}"
            print(traceback.format_exc())

    def _start_playhead_animation(self):
        self.playback_clock = Clock.schedule_interval(self._update_playback_progress, 1/60.)

    def _update_playback_progress(self, dt):
        elapsed = time.time() - self.playback_start_time
        current_beat = elapsed / self.beat_duration
        if current_beat > self.playback_duration:
            self.stop_audio()
        else:
            self.layout.ids.piano_roll.current_time = current_beat

    def _play_linux(self):
        # Implementation for Linux playback using fluidsynth or timidity
        pass # Placeholder

    def stop_audio(self, *args):
        if self.playback_clock:
            self.playback_clock.cancel()
            self.playback_clock = None
        
        if self.media_player:
            try:
                if self.media_player.isPlaying(): self.media_player.stop()
                self.media_player.release()
            except Exception as e:
                print(f"Error stopping mediaplayer: {e}")
            finally:
                self.media_player = None
                
        self.layout.ids.piano_roll.is_playing = False
        self.layout.ids.piano_roll.current_time = 0
        if "Playing" in self.status_text:
            self.status_text = "Playback stopped"

    def save_code(self):
        try:
            save_path = "last_music21_code.py"
            if ANDROID:
                from android.storage import primary_external_storage_path
                save_path = os.path.join(primary_external_storage_path(), "Download", "sridaw_code.py")
            with open(save_path, "w") as f: f.write(self.layout.ids.editor.text)
            self.status_text = f"Code saved to {save_path}"
        except Exception as e: self.status_text = f"Save error: {e}"

    def load_code(self):
        try:
            load_path = "last_music21_code.py"
            if ANDROID:
                from android.storage import primary_external_storage_path
                load_path = os.path.join(primary_external_storage_path(), "Download", "sridaw_code.py")
            if os.path.exists(load_path):
                with open(load_path, "r") as f: self.layout.ids.editor.text = f.read()
                self.status_text = "Code loaded. Press 'Run'."
            else: self.status_text = "No saved code found."
        except Exception as e: self.status_text = f"Load error: {e}"

    def on_stop(self):
        self.stop_audio()
        if self.temp_file and os.path.exists(self.temp_file):
            try: os.remove(self.temp_file)
            except: pass

if __name__ == "__main__":
    Music21DAW().run()
