from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.audio import SoundLoader
from kivy.logger import Logger

import numpy as np
import io
import os
from datetime import datetime

# Music21 imports
try:
    from music21 import converter, stream, midi, note, chord, environment
    from music21.graph import PlotStream
    music21_available = True
except ImportError:
    music21_available = False
    Logger.error("Music21 not available - some features disabled")

class Music21Player(BoxLayout):
    def __init__(self, **kwargs):
        super(Music21Player, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10
        
        # Status label
        self.status_label = Label(text="Music21 Player - Ready", size_hint=(1, 0.1))
        self.add_widget(self.status_label)
        
        # Piano roll display
        self.piano_roll = Image(size_hint=(1, 0.6))
        self.add_widget(self.piano_roll)
        
        # Buttons layout
        buttons_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        
        self.load_btn = Button(text="Load MIDI")
        self.load_btn.bind(on_press=self.show_file_chooser)
        buttons_layout.add_widget(self.load_btn)
        
        self.play_btn = Button(text="Play")
        self.play_btn.bind(on_press=self.play_music)
        buttons_layout.add_widget(self.play_btn)
        
        self.stop_btn = Button(text="Stop")
        self.stop_btn.bind(on_press=self.stop_music)
        buttons_layout.add_widget(self.stop_btn)
        
        self.download_btn = Button(text="Save MIDI")
        self.download_btn.bind(on_press=self.save_midi)
        buttons_layout.add_widget(self.download_btn)
        
        self.add_widget(buttons_layout)
        
        # File chooser (hidden initially)
        self.file_chooser = FileChooserListView(size_hint=(1, 0.7), filters=['*.mid', '*.midi'])
        self.file_chooser.bind(on_submit=self.load_midi_file)
        self.file_chooser.opacity = 0
        self.add_widget(self.file_chooser)
        
        # Audio and music21 objects
        self.sound = None
        self.current_stream = None
        self.midi_filepath = None
        
        # Set music21 environment for Android
        if music21_available:
            env = environment.Environment()
            env['musicxmlPath'] = ''
            env['musescoreDirectPNGPath'] = ''
            env['lilypondPath'] = ''
        
    def show_file_chooser(self, instance):
        self.file_chooser.opacity = 1
        
    def load_midi_file(self, instance, selection, *args):
        if not selection:
            return
            
        self.file_chooser.opacity = 0
        self.midi_filepath = selection[0]
        
        if not music21_available:
            self.status_label.text = "Music21 not available - cannot load MIDI"
            return
            
        try:
            self.current_stream = converter.parse(self.midi_filepath)
            self.status_label.text = f"Loaded: {os.path.basename(self.midi_filepath)}"
            self.update_piano_roll()
        except Exception as e:
            self.status_label.text = f"Error loading MIDI: {str(e)}"
            Logger.error(f"Error loading MIDI: {str(e)}")
    
    def update_piano_roll(self):
        if not self.current_stream or not music21_available:
            return
            
        try:
            # Create piano roll plot
            plot = PlotStream(self.current_stream)
            plot.title = 'Piano Roll'
            plot.process()
            
            # Convert music21 plot to numpy array
            fig = plot.getFigure()
            fig.canvas.draw()
            
            # Convert matplotlib figure to Kivy texture
            buf = io.BytesIO()
            fig.savefig(buf, format='rgba', dpi=100)
            buf.seek(0)
            img_array = np.frombuffer(buf.getvalue(), dtype=np.uint8)
            buf.close()
            
            # Reshape and create texture
            w, h = fig.canvas.get_width_height()
            img_array = img_array.reshape((h, w, 4))
            texture = Texture.create(size=(w, h), colorfmt='rgba')
            texture.blit_buffer(img_array.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
            self.piano_roll.texture = texture
            
        except Exception as e:
            self.status_label.text = f"Error creating piano roll: {str(e)}"
            Logger.error(f"Error creating piano roll: {str(e)}")
    
    def play_music(self, instance):
        if not self.current_stream or not music21_available:
            self.status_label.text = "No MIDI loaded or Music21 unavailable"
            return
            
        try:
            # Convert stream to MIDI and save temporarily
            temp_path = os.path.join(os.getcwd(), 'temp.mid')
            self.current_stream.write('midi', temp_path)
            
            # Play with Kivy's SoundLoader
            if self.sound:
                self.sound.stop()
                self.sound.unload()
                
            self.sound = SoundLoader.load(temp_path)
            if self.sound:
                self.sound.play()
                self.status_label.text = "Playing..."
            else:
                self.status_label.text = "Could not play MIDI"
                
        except Exception as e:
            self.status_label.text = f"Error playing music: {str(e)}"
            Logger.error(f"Error playing music: {str(e)}")
    
    def stop_music(self, instance):
        if self.sound and self.sound.state == 'play':
            self.sound.stop()
            self.status_label.text = "Stopped playback"
    
    def save_midi(self, instance):
        if not self.current_stream or not music21_available:
            self.status_label.text = "No MIDI loaded or Music21 unavailable"
            return
            
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(os.getcwd(), f"composition_{timestamp}.mid")
            
            # Save MIDI file
            self.current_stream.write('midi', save_path)
            self.status_label.text = f"MIDI saved to: {save_path}"
            
        except Exception as e:
            self.status_label.text = f"Error saving MIDI: {str(e)}"
            Logger.error(f"Error saving MIDI: {str(e)}")

class Music21App(App):
    def build(self):
        return Music21Player()

if __name__ == '__main__':
    Music21App().run()
