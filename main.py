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
                interval_info = f"\nInterval: {interval[1]} â†’ {interval[2]} ({interval[3]} semitones)"
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
            0: "P1",
            1: "m2",
            2: "M2",
            3: "m3",
            4: "M3",
            5: "P4",
            6: "TT",
            7: "P5",
            8: "m6",
            9: "M6",
            10: "m7",
            11: "M7",
            12: "P8"
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
                Color(*self._key_colors[pitch])
                Rectangle(
                    pos=(self.x, y),
                    size=(self.width, dp(18)))
                
                # Draw key border
                Color(0.3, 0.3, 0.3, 1)
                Line(rectangle=(self.x, y, self.width, dp(18)), width=0.5)
                
                # Draw pitch label for every visible pitch
                if pitch in self.pitch_range:
                    note_name = self.midi_to_note_name(pitch)
                    if pitch in self.drum_pitches:
                        Color(1, 0.5, 0.5, 1)  # Red for drums
                    else:
                        Color(0.5, 0.5, 0.5, 1)
                    self.draw_text(note_name, self.x + dp(5), y + dp(3), dp(12))
            
            # Highlight scale rows (full length) - only for visible pitches
            if self.scale_pitches:
                Color(1.0, 0.9, 0.2, 0.15)  # Semi-transparent yellow
                for pitch in self.scale_pitches:
                    if pitch in self.visible_pitches:
                        i = self.visible_pitches.index(pitch)
                        y = self.y + i * dp(18)
                        Rectangle(
                            pos=(self.x, y),
                            size=(self.width, dp(18)))
            
            # Draw measure/beat lines
            max_x = max((o + d) * self.beat_scale for o, _, d, _ in self.notes) if self.notes else 10
            Color(0.4, 0.4, 0.4, 0.6)
            for beat in range(0, int(self.minimum_width / self.beat_scale) + 2):
                x = self.x + beat * self.beat_scale
                Line(points=[x, self.y, x, self.top], width=1)
                
                # Label every 4 beats
                if beat % 4 == 0:
                    self.draw_text(str(beat), x + dp(2), self.y - dp(15), dp(12))
            
            # Draw interval lines and labels - only for visible pitches
            if self.scale_intervals:
                for interval in self.scale_intervals:
                    start_pitch, end_pitch, semitones = interval[:3]
                    
                    # Only draw if both pitches are visible
                    if (start_pitch in self.visible_pitches and 
                        end_pitch in self.visible_pitches):
                        start_i = self.visible_pitches.index(start_pitch)
                        end_i = self.visible_pitches.index(end_pitch)
                        start_y = self.y + start_i * dp(18) + dp(9)
                        end_y = self.y + end_i * dp(18) + dp(9)
                        
                        # Draw connecting line
                        Color(0.9, 0.2, 0.9, 0.7)  # Purple line
                        Line(
                            points=[self.x + dp(10), start_y, 
                                   self.x + dp(40), end_y],
                            width=dp(1.5))
                        
                        # Draw interval label
                        interval_name = self.get_interval_name(semitones)
                        Color(0.9, 0.9, 0.9, 1)  # White text
                        self.draw_text(interval_name, self.x + dp(25), (start_y + end_y)/2, dp(12), center=True)
            
            # Draw notes with velocity-based coloring
            for i, (offset, pitch, duration, velocity) in enumerate(self.notes):
                if pitch not in self.visible_pitches:
                    continue
                    
                pitch_index = self.visible_pitches.index(pitch)
                x = self.x + offset * self.beat_scale
                y = self.y + pitch_index * dp(18)
                w = duration * self.beat_scale
                h = dp(17)
                
                # Color based on velocity (blue gradient)
                blue_intensity = 0.5 + (velocity / 200)
                highlight = 1.0 if i == self.selected_note else 0.7
                
                # Custom color mapping
                if pitch in self.drum_pitches:  # Drums
                    Color(0.9, 0.2, 0.2, highlight)  # Red
                elif velocity == 101:  # scale
                    Color(1.0, 0.9, 0.2, highlight)  # Yellow
                elif velocity == 102:  # chords
                    Color(0.2, 0.9, 0.3, highlight)  # Green
                elif velocity == 103:  # melody
                    Color(0.2, 0.5, 1.0, highlight)  # Blue
                else:
                    Color(0.8, 0.5, blue_intensity, highlight)  # Default
                
                # Draw rounded rectangle for note
                self.draw_rounded_rect(x, y, w, h, dp(3))
                
                # Draw note border
                Color(0, 0, 0, 0.3)
                Line(rounded_rectangle=(x, y, w, h, dp(3)), width=1)
                
                # Draw note label
                if w > dp(20):  # Only draw label if note is wide enough
                    note_name = self.midi_to_note_name(pitch)
                    text_color = (0.1, 0.1, 0.1, 1) if velocity == 101 else (1, 1, 1, 1)
                    Color(*text_color)
                    self.draw_text(note_name, x + dp(3), y + dp(2), dp(12))
            
            # Playhead line (thicker and more visible)
            if self.is_playing:
                Color(1, 0.2, 0.2, 0.9)
                self.playhead_line = Line(
                    points=[self.x + self.current_time * self.beat_scale, self.y, 
                           self.x + self.current_time * self.beat_scale, self.top],
                    width=dp(3))
    
    def draw_rounded_rect(self, x, y, w, h, r):
        """Draw a rounded rectangle"""
        # Main rectangle
        Rectangle(pos=(x + r, y), size=(w - 2*r, h))
        Rectangle(pos=(x, y + r), size=(w, h - 2*r))
        
        # Corners
        Ellipse(pos=(x, y), size=(2*r, 2*r))
        Ellipse(pos=(x + w - 2*r, y), size=(2*r, 2*r))
        Ellipse(pos=(x, y + h - 2*r), size=(2*r, 2*r))
        Ellipse(pos=(x + w - 2*r, y + h - 2*r), size=(2*r, 2*r))
    
    def draw_text(self, text, x, y, font_size, center=False):
        """Draw text directly on canvas"""
        from kivy.core.text import Label as CoreLabel
        label = CoreLabel(text=text, font_size=font_size, font_name='Mono')
        label.refresh()
        texture = label.texture
        if center:
            pos = (x - texture.width/2, y - texture.height/2)
        else:
            pos = (x, y)
        Color(0, 0, 0, 1)
        Rectangle(texture=texture, pos=pos, size=texture.size)
    
    def _update_playhead(self, *args):
        self.canvas.after.remove(self.playhead_line) if self.playhead_line else None
        with self.canvas.after:
            Color(1, 0, 0, 0.9)
            x_pos = self.x + self.current_time * self.beat_scale
            self.playhead_line = Line(
                points=[x_pos, self.y, x_pos, self.top],
                width=dp(2)
            )
        # Auto-scroll to follow playhead
        if self.scroll_view:
            playhead_x = self.x + self.current_time * self.beat_scale
            viewport_width = self.scroll_view.width
            content_width = self.width
            scroll_x_px = self.scroll_view.scroll_x * (content_width - viewport_width)

            visible_left = scroll_x_px
            visible_right = scroll_x_px + viewport_width
            margin = dp(50)

            if playhead_x < visible_left + margin or playhead_x > visible_right - margin:
                target_scroll_px = max(0, playhead_x - viewport_width / 2)
                target_scroll = min(1.0, target_scroll_px / (content_width - viewport_width))
                self.scroll_view.scroll_x = target_scroll
    
    def update_from_stream(self, music_stream):
        """Update piano roll from music21 stream"""
        self.notes = []
        self.scale_pitches = []  # Reset scale pitches
        self.scale_intervals = []  # Reset interval data
        self.drum_pitches = []    # Reset drum pitches
        self.visible_pitches = [] # Reset visible pitches
        self.selected_note = None
        if not music_stream:
            return
            
        try:
            # First pass: collect all scale notes and drum notes
            scale_notes = []
            for el in music_stream.recurse().notes:
                if hasattr(el, 'offset'):
                    offset = el.offset
                    duration = el.duration.quarterLength
                    velocity = el.volume.velocity if hasattr(el.volume, 'velocity') else 100
                    
                    # Mark drum notes (velocity 104)
                    if velocity == 104:
                        if isinstance(el, note.Note):
                            if el.pitch.midi not in self.drum_pitches:
                                self.drum_pitches.append(el.pitch.midi)
                        elif isinstance(el, chord.Chord):
                            for n in el.notes:
                                if n.pitch.midi not in self.drum_pitches:
                                    self.drum_pitches.append(n.pitch.midi)
                    
                    # Collect scale pitches (velocity 101)
                    if velocity == 101:
                        if isinstance(el, note.Note):
                            if el.pitch.midi not in self.scale_pitches:
                                self.scale_pitches.append(el.pitch.midi)
                            scale_notes.append((offset, el.pitch.midi, duration, velocity))
                        elif isinstance(el, chord.Chord):
                            for n in el.notes:
                                if n.pitch.midi not in self.scale_pitches:
                                    self.scale_pitches.append(n.pitch.midi)
                                scale_notes.append((offset, n.pitch.midi, duration, velocity))
            
            # Sort scale notes by offset
            scale_notes.sort(key=lambda x: x[0])
            
            # Calculate intervals between consecutive scale notes
            for i in range(1, len(scale_notes)):
                prev_note = scale_notes[i-1]
                curr_note = scale_notes[i]
                
                # Only calculate if they're in the same voice/part (temporal proximity)
                if abs(curr_note[0] - prev_note[0]) < 1.0:  # Within 1 beat
                    semitones = curr_note[1] - prev_note[1]
                    if semitones != 0:  # Skip unison intervals
                        # Store: (prev_pitch, curr_pitch, semitones, prev_offset, curr_offset)
                        self.scale_intervals.append((
                            prev_note[1], 
                            curr_note[1], 
                            semitones,
                            prev_note[0],
                            curr_note[0]
                        ))
            
            # Second pass: collect all notes and visible pitches
            all_pitches = set()
            for el in music_stream.recurse().notes:
                if hasattr(el, 'offset'):
                    offset = el.offset
                    duration = el.duration.quarterLength
                    velocity = el.volume.velocity if hasattr(el.volume, 'velocity') else 100
                    
                    if isinstance(el, note.Note):
                        self.notes.append((offset, el.pitch.midi, duration, velocity))
                        all_pitches.add(el.pitch.midi)
                    elif isinstance(el, chord.Chord):
                        for n in el.notes:
                            self.notes.append((offset, n.pitch.midi, duration, velocity))
                            all_pitches.add(n.pitch.midi)
            
            # Add scale pitches even if they don't have notes (for highlighting)
            for pitch in self.scale_pitches:
                all_pitches.add(pitch)
                
            # Add drum pitches
            for pitch in self.drum_pitches:
                all_pitches.add(pitch)
                
            # Create sorted list of visible pitches
            self.visible_pitches = sorted(all_pitches)
            
            # Sort notes by pitch for better visualization
            self.notes.sort(key=lambda x: x[1])
            
            # Update height based on visible pitches
            self.height = max(dp(100), len(self.visible_pitches) * dp(18))
        except Exception as e:
            print(f"Error updating piano roll: {e}")

class Music21DAW(App):
    status_text = StringProperty("Ready")
    
    def build(self):
        self.title = "Music21 Visual DAW"
        self.layout = MainLayout()
        self.status_label = self.layout.ids.status_label
        
        # Load demo music21 code with a scale showing intervals
        demo_code = '''from music21 import *

# Create a demo composition with scale intervals
s = stream.Stream()
s.append(tempo.MetronomeMark(number=90))
s.append(dynamics.Dynamic('mf'))

# 🎵 Natabhairavi scale (C natural minor) with interval annotations
scale_notes = ["C4", "D4", "Eb4", "F4", "G4", "Ab4", "Bb4", "C5"]
for i, p in enumerate(scale_notes):
    n = note.Note(p, quarterLength=0.5)
    n.volume.velocity = 101  # Yellow for scale
    s.insert(i * 0.5, n)

# 🥁 Drum track (velocity 104)
drum_notes = ["F#3", "G3", "G#3", "A3"]
for i, p in enumerate(drum_notes):
    n = note.Note(p, quarterLength=0.5)
    n.volume.velocity = 104  # Red for drums
    s.insert(i * 0.5 + 2.0, n)

# 🎶 Chords (Cmin, Fmin, Gmin)
chords = [
    chord.Chord(["C3", "Eb3", "G3"], quarterLength=2.0),
    chord.Chord(["F3", "Ab3", "C4"], quarterLength=2.0),
    chord.Chord(["G3", "Bb3", "D4"], quarterLength=2.0)
]

for i, c in enumerate(chords):
    c.volume.velocity = 102  # Green for chords
    s.insert(i * 2.0, c)

# 🎤 Melody phrase showing intervals
melody = [
    note.Note("G4", quarterLength=0.5),
    note.Note("F4", quarterLength=0.5),
    note.Note("Eb4", quarterLength=1.0),
    note.Note("C4", quarterLength=1.0)
]

for i, n in enumerate(melody):
    n.volume.velocity = 103  # Blue for melody
    s.insert(i * 0.5 + 1.0, n)

result = s
'''
        self.layout.ids.editor.text = demo_code
        
        self.current_stream = None
        self.media_player = None
        self.temp_file = None
        self.playback_clock = None
        self.playback_start_time = 0
        self.playback_duration = 0
        self.bpm = 60
        self.beat_duration = 1.0  # Seconds per beat

        # Auto-run the demo code
        Clock.schedule_once(lambda dt: self.run_code(), 0.5)
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
                self.layout.ids.piano_roll.scroll_view = self.layout.ids.piano_scroll
                self.layout.ids.piano_roll.update_from_stream(self.current_stream)
                
                # Get BPM from stream (default to 60 if not found)
                self.bpm = 60
                for mark in self.current_stream.flat.getElementsByClass(tempo.MetronomeMark):
                    if mark.number:
                        self.bpm = mark.number
                        break
                
                # Calculate beat duration in seconds
                self.beat_duration = 60.0 / self.bpm
                
                # Store total duration in beats
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
            
            # Convert real-time to musical time using BPM
            current_beat = elapsed / self.beat_duration
            
            # Limit to total duration
            self.layout.ids.piano_roll.current_time = min(current_beat, self.playback_duration)
            
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
        
    def save_code(self):
        """Save editor content to file"""
        try:
            if ANDROID:
                from android.storage import primary_external_storage_path
                save_path = os.path.join(primary_external_storage_path(), "last_music21_code.py")
            else:
                save_path = os.path.join(os.path.expanduser("~"), "last_music21_code.py")
                
            with open(save_path, "w") as f:
                f.write(self.layout.ids.editor.text)
                
            self.status_text = f"Code saved to {save_path}"
        except Exception as e:
            self.status_text = f"Save error: {str(e)}"
            
    def load_code(self):
        """Load editor content from file"""
        try:
            if ANDROID:
                from android.storage import primary_external_storage_path
                load_path = os.path.join(primary_external_storage_path(), "last_music21_code.py")
            else:
                load_path = os.path.join(os.path.expanduser("~"), "last_music21_code.py")
                
            if os.path.exists(load_path):
                with open(load_path, "r") as f:
                    self.layout.ids.editor.text = f.read()
                self.status_text = f"Code loaded from {load_path}"
                self.run_code()
            else:
                self.status_text = "No saved code found"
        except Exception as e:
            self.status_text = f"Load error: {str(e)}"

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
