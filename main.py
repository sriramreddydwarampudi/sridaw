import os
os.environ['MUSIC21_NO_DOWNLOAD'] = '1'

import numpy as np
from music21 import converter, environment, midi, note, stream
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.audio import SoundLoader

class MidiTools(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        self.btn_open = Button(text="Convert MIDI to Piano Roll")
        self.btn_open.bind(on_press=self.midi_to_piano_roll)
        self.add_widget(self.btn_open)

        self.btn_save = Button(text="Convert Piano Roll to MIDI")
        self.btn_save.bind(on_press=self.piano_roll_to_midi)
        self.add_widget(self.btn_save)

        self.play_btn = Button(text="Play Audio")
        self.play_btn.bind(on_press=self.play_audio)
        self.add_widget(self.play_btn)

        self.status = Label(text="Ready")
        self.add_widget(self.status)

    def midi_to_piano_roll(self, instance):
        try:
            midi_path = os.path.join(os.getcwd(), 'input.mid')
            score = converter.parse(midi_path)

            piano_roll = np.zeros((128, 1000))
            for part in score.parts:
                for event in part.flat.notes:
                    if isinstance(event, note.Note):
                        pitch = event.pitch.midi
                        start = int(event.offset * 4)
                        end = start + int(event.duration.quarterLength * 4)
                        piano_roll[pitch, start:end] = 1

            np.save('piano_roll.npy', piano_roll)

            plt.figure(figsize=(15, 6))
            plt.imshow(piano_roll[:72], aspect='auto', origin='lower')
            plt.title('Piano Roll')
            plt.ylabel('Pitch (MIDI)')
            plt.xlabel('Time (16th notes)')
            plt.savefig('piano_roll.png')

            self.status.text = "Created piano_roll.png"
        except Exception as e:
            self.status.text = f"Error: {str(e)}"

    def piano_roll_to_midi(self, instance):
        try:
            piano_roll = np.load('piano_roll.npy')
            s = stream.Stream()
            for pitch, row in enumerate(piano_roll):
                note_on = None
                for time_step, value in enumerate(row):
                    if value and note_on is None:
                        note_on = time_step
                    elif not value and note_on is not None:
                        n = note.Note(pitch)
                        n.quarterLength = (time_step - note_on) / 4.0
                        n.offset = note_on / 4.0
                        s.append(n)
                        note_on = None

            s.write('midi', fp='output.mid')

            # You must convert this to OGG/WAV manually on PC for now
            self.status.text = "Created output.mid (convert to output.ogg to play)"
        except Exception as e:
            self.status.text = f"Error: {str(e)}"

    def play_audio(self, instance):
        try:
            sound = SoundLoader.load('output.ogg')
            if sound:
                sound.play()
                self.status.text = "Playing output.ogg"
            else:
                self.status.text = "Cannot load output.ogg"
        except Exception as e:
            self.status.text = f"Play error: {str(e)}"

class MidiApp(App):
    def build(self):
        return MidiTools()

if __name__ == '__main__':
    if not os.path.exists('corpus'):
        os.makedirs('corpus')
        open(os.path.join('corpus', '__init__.py'), 'w').close()
    MidiApp().run()
