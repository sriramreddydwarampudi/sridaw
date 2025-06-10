from kivy.app import App
from kivy.uix.label import Label

class SridawApp(App):
    def build(self):
        return Label(text="🎵 Hello from music21!")

if __name__ == "__main__":
    SridawApp().run()
