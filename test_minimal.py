#!/usr/bin/env python3
"""
Minimal test version of SriDAW for Android build testing
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        
        label = Label(text='SriDAW Test - Build Successful!', 
                     font_size='20sp')
        button = Button(text='Test Button', 
                       size_hint_y=None, 
                       height='50dp')
        
        layout.add_widget(label)
        layout.add_widget(button)
        
        return layout

if __name__ == "__main__":
    TestApp().run()