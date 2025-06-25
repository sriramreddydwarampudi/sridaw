#!/usr/bin/env python3
"""
VersePad Clone - Offline Poetry Writing App
A comprehensive Kivy app for poetry writing with all features working offline
"""

import os
import re
import json
import sqlite3
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.splitter import Splitter
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.widget import Widget

# NLP and dictionary libraries
try:
    import nltk
    from nltk.corpus import cmudict, wordnet
    from nltk.tokenize import word_tokenize, syllable_tokenize
    nltk.download('cmudict', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    import pronouncing
    PRONOUNCING_AVAILABLE = True
except ImportError:
    PRONOUNCING_AVAILABLE = False

try:
    from textstat import flesch_reading_ease, syllable_count
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

try:
    import pyphen
    PYPHEN_AVAILABLE = True
except ImportError:
    PYPHEN_AVAILABLE = False


class PoetryAnalyzer:
    """Core analysis engine for poetry features"""
    
    def __init__(self):
        self.cmu_dict = None
        self.wordnet_dict = None
        self.pyphen_dic = None
        self.initialize_resources()
    
    def initialize_resources(self):
        """Initialize offline resources"""
        if NLTK_AVAILABLE:
            try:
                self.cmu_dict = cmudict.dict()
            except:
                pass
            
            try:
                self.wordnet_dict = wordnet
            except:
                pass
        
        if PYPHEN_AVAILABLE:
            try:
                self.pyphen_dic = pyphen.Pyphen(lang='en')
            except:
                pass
    
    def get_word_definition(self, word: str) -> List[str]:
        """Get word definitions"""
        definitions = []
        word = word.lower().strip()
        
        if self.wordnet_dict:
            try:
                synsets = self.wordnet_dict.synsets(word)
                for synset in synsets[:3]:  # Limit to first 3 definitions
                    definitions.append(f"{synset.pos()}: {synset.definition()}")
            except:
                pass
        
        if not definitions:
            definitions = [f"Definition for '{word}' not found offline"]
        
        return definitions
    
    def get_phonetics(self, word: str) -> str:
        """Get phonetic representation of word"""
        word = word.lower().strip()
        
        if PRONOUNCING_AVAILABLE:
            try:
                phones = pronouncing.phones_for_word(word)
                if phones:
                    return phones[0]
            except:
                pass
        
        if self.cmu_dict and word in self.cmu_dict:
            return ' '.join(self.cmu_dict[word][0])
        
        return f"Phonetics for '{word}' not available offline"
    
    def get_rhymes(self, word: str) -> List[str]:
        """Get rhyming words"""
        word = word.lower().strip()
        rhymes = []
        
        if PRONOUNCING_AVAILABLE:
            try:
                rhymes = pronouncing.rhymes(word)[:20]  # Limit to 20 rhymes
            except:
                pass
        
        if not rhymes and self.cmu_dict:
            # Simple rhyme detection using CMU dict
            word_phones = self.cmu_dict.get(word, [])
            if word_phones:
                word_ending = word_phones[0][-2:]  # Last 2 phonemes
                for dict_word, phones_list in self.cmu_dict.items():
                    if dict_word != word and phones_list[0][-2:] == word_ending:
                        rhymes.append(dict_word)
                        if len(rhymes) >= 20:
                            break
        
        return rhymes
    
    def count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower().strip()
        
        if TEXTSTAT_AVAILABLE:
            try:
                return syllable_count(word)
            except:
                pass
        
        if self.pyphen_dic:
            try:
                return len(self.pyphen_dic.inserted(word).split('-'))
            except:
                pass
        
        if self.cmu_dict and word in self.cmu_dict:
            return len([ph for ph in self.cmu_dict[word][0] if ph[-1].isdigit()])
        
        # Fallback syllable counting
        vowels = 'aeiouyAEIOUY'
        syllables = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllables += 1
            prev_was_vowel = is_vowel
        
        return max(1, syllables)
    
    def analyze_meter(self, text: str) -> Dict:
        """Analyze meter of text"""
        lines = text.strip().split('\n')
        meter_analysis = {
            'lines': [],
            'pattern': '',
            'consistency': 0.0
        }
        
        syllable_counts = []
        
        for line in lines:
            if not line.strip():
                continue
                
            words = re.findall(r'\b\w+\b', line.lower())
            line_syllables = sum(self.count_syllables(word) for word in words)
            syllable_counts.append(line_syllables)
            
            # Simple stress pattern (alternating for now)
            stress_pattern = ''.join(['/' if i % 2 == 1 else 'u' for i in range(line_syllables)])
            
            meter_analysis['lines'].append({
                'text': line,
                'syllables': line_syllables,
                'stress_pattern': stress_pattern,
                'words': words
            })
        
        if syllable_counts:
            most_common = Counter(syllable_counts).most_common(1)[0]
            consistency = syllable_counts.count(most_common[0]) / len(syllable_counts)
            meter_analysis['consistency'] = consistency
            meter_analysis['common_length'] = most_common[0]
        
        return meter_analysis
    
    def analyze_rhyme_scheme(self, text: str) -> Dict:
        """Analyze rhyme scheme of poem"""
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        rhyme_scheme = []
        rhyme_groups = {}
        current_letter = 'A'
        
        for line in lines:
            words = re.findall(r'\b\w+\b', line.lower())
            if not words:
                rhyme_scheme.append('-')
                continue
            
            last_word = words[-1]
            
            # Find rhyming group
            found_group = None
            for letter, group_words in rhyme_groups.items():
                if any(self.words_rhyme(last_word, word) for word in group_words):
                    found_group = letter
                    break
            
            if found_group:
                rhyme_scheme.append(found_group)
                rhyme_groups[found_group].append(last_word)
            else:
                rhyme_scheme.append(current_letter)
                rhyme_groups[current_letter] = [last_word]
                current_letter = chr(ord(current_letter) + 1)
        
        return {
            'scheme': ' '.join(rhyme_scheme),
            'groups': rhyme_groups,
            'lines': lines
        }
    
    def words_rhyme(self, word1: str, word2: str) -> bool:
        """Check if two words rhyme"""
        if word1 == word2:
            return True
        
        if PRONOUNCING_AVAILABLE:
            try:
                return word2 in pronouncing.rhymes(word1)
            except:
                pass
        
        if self.cmu_dict:
            phones1 = self.cmu_dict.get(word1, [])
            phones2 = self.cmu_dict.get(word2, [])
            if phones1 and phones2:
                return phones1[0][-2:] == phones2[0][-2:]
        
        # Simple ending-based rhyme detection
        return word1.endswith(word2[-2:]) or word2.endswith(word1[-2:])


class VisualMeterWidget(Widget):
    """Widget for visual meter representation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.meter_data = None
        self.bind(size=self.update_graphics)
    
    def set_meter_data(self, meter_data):
        self.meter_data = meter_data
        self.update_graphics()
    
    def update_graphics(self, *args):
        self.canvas.clear()
        if not self.meter_data or not self.meter_data.get('lines'):
            return
        
        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)  # Dark gray
            Rectangle(pos=self.pos, size=self.size)
            
            Color(1, 1, 1, 1)  # White
            
            line_height = self.height / max(len(self.meter_data['lines']), 1)
            
            for i, line_data in enumerate(self.meter_data['lines']):
                y = self.y + self.height - (i + 1) * line_height
                
                stress_pattern = line_data.get('stress_pattern', '')
                if not stress_pattern:
                    continue
                
                syllable_width = self.width / max(len(stress_pattern), 1)
                
                for j, stress in enumerate(stress_pattern):
                    x = self.x + j * syllable_width + syllable_width / 2
                    
                    if stress == '/':  # Stressed
                        Line(points=[x, y, x, y + line_height * 0.6], width=2)
                    else:  # Unstressed
                        Line(points=[x - 5, y + line_height * 0.3, x + 5, y + line_height * 0.3], width=2)


class PoemEditor(TextInput):
    """Enhanced text input for poem editing"""
    
    def __init__(self, analyzer, **kwargs):
        super().__init__(**kwargs)
        self.analyzer = analyzer
        self.multiline = True
        self.font_size = dp(16)
        self.bind(text=self.on_text_change)
        self.analysis_callback = None
    
    def set_analysis_callback(self, callback):
        self.analysis_callback = callback
    
    def on_text_change(self, instance, value):
        if self.analysis_callback:
            Clock.unschedule(self.delayed_analysis)
            Clock.schedule_once(self.delayed_analysis, 1.0)  # Delay analysis by 1 second
    
    def delayed_analysis(self, dt):
        if self.analysis_callback:
            self.analysis_callback(self.text)


class VersePadApp(App):
    """Main application class"""
    
    def build(self):
        self.analyzer = PoetryAnalyzer()
        self.title = "VersePad - Offline Poetry Writer"
        
        # Main layout
        main_layout = BoxLayout(orientation='horizontal')
        
        # Create splitter for resizable panels
        splitter = Splitter(sizable_from='right')
        
        # Left panel - Text editor
        editor_panel = BoxLayout(orientation='vertical')
        
        # Toolbar
        toolbar = BoxLayout(size_hint_y=None, height=dp(50))
        
        new_btn = Button(text='New', size_hint_x=None, width=dp(80))
        new_btn.bind(on_press=self.new_poem)
        
        save_btn = Button(text='Save', size_hint_x=None, width=dp(80))
        save_btn.bind(on_press=self.save_poem)
        
        load_btn = Button(text='Load', size_hint_x=None, width=dp(80))
        load_btn.bind(on_press=self.load_poem)
        
        toolbar.add_widget(new_btn)
        toolbar.add_widget(save_btn)
        toolbar.add_widget(load_btn)
        toolbar.add_widget(Label())  # Spacer
        
        # Text editor
        self.poem_editor = PoemEditor(self.analyzer)
        self.poem_editor.set_analysis_callback(self.analyze_poem)
        
        editor_panel.add_widget(toolbar)
        editor_panel.add_widget(self.poem_editor)
        
        splitter.add_widget(editor_panel)
        
        # Right panel - Analysis tools
        analysis_panel = TabbedPanel(do_default_tab=False, tab_width=dp(120))
        
        # Dictionary tab
        dict_tab = TabbedPanelItem(text='Dictionary')
        dict_layout = BoxLayout(orientation='vertical')
        
        dict_input = TextInput(hint_text='Enter word to look up...', 
                              size_hint_y=None, height=dp(40), multiline=False)
        dict_input.bind(on_text_validate=lambda x: self.lookup_word(dict_input.text))
        
        self.dict_results = Label(text='Enter a word to see its definition',
                                 text_size=(None, None), valign='top')
        dict_scroll = ScrollView()
        dict_scroll.add_widget(self.dict_results)
        
        dict_layout.add_widget(dict_input)
        dict_layout.add_widget(dict_scroll)
        dict_tab.add_widget(dict_layout)
        
        # Rhymes tab
        rhymes_tab = TabbedPanelItem(text='Rhymes')
        rhymes_layout = BoxLayout(orientation='vertical')
        
        rhyme_input = TextInput(hint_text='Enter word to find rhymes...',
                               size_hint_y=None, height=dp(40), multiline=False)
        rhyme_input.bind(on_text_validate=lambda x: self.find_rhymes(rhyme_input.text))
        
        self.rhyme_results = Label(text='Enter a word to find rhymes',
                                  text_size=(None, None), valign='top')
        rhyme_scroll = ScrollView()
        rhyme_scroll.add_widget(self.rhyme_results)
        
        rhymes_layout.add_widget(rhyme_input)
        rhymes_layout.add_widget(rhyme_scroll)
        rhymes_tab.add_widget(rhymes_layout)
        
        # Phonetics tab
        phonetics_tab = TabbedPanelItem(text='Phonetics')
        phonetics_layout = BoxLayout(orientation='vertical')
        
        phonetic_input = TextInput(hint_text='Enter word for phonetics...',
                                  size_hint_y=None, height=dp(40), multiline=False)
        phonetic_input.bind(on_text_validate=lambda x: self.get_phonetics(phonetic_input.text))
        
        self.phonetic_results = Label(text='Enter a word to see phonetics',
                                     text_size=(None, None), valign='top')
        phonetic_scroll = ScrollView()
        phonetic_scroll.add_widget(self.phonetic_results)
        
        phonetics_layout.add_widget(phonetic_input)
        phonetics_layout.add_widget(phonetic_scroll)
        phonetics_tab.add_widget(phonetics_layout)
        
        # Meter Analysis tab
        meter_tab = TabbedPanelItem(text='Meter')
        meter_layout = BoxLayout(orientation='vertical')
        
        self.meter_results = Label(text='Type your poem to see meter analysis',
                                  text_size=(None, None), valign='top')
        meter_scroll = ScrollView(size_hint_y=0.7)
        meter_scroll.add_widget(self.meter_results)
        
        # Visual meter display
        self.visual_meter = VisualMeterWidget(size_hint_y=0.3)
        
        meter_layout.add_widget(meter_scroll)
        meter_layout.add_widget(Label(text='Visual Meter:', size_hint_y=None, height=dp(30)))
        meter_layout.add_widget(self.visual_meter)
        meter_tab.add_widget(meter_layout)
        
        # Rhyme Scheme tab
        rhyme_scheme_tab = TabbedPanelItem(text='Rhyme Scheme')
        rhyme_scheme_layout = BoxLayout(orientation='vertical')
        
        self.rhyme_scheme_results = Label(text='Type your poem to see rhyme scheme',
                                         text_size=(None, None), valign='top')
        rhyme_scheme_scroll = ScrollView()
        rhyme_scheme_scroll.add_widget(self.rhyme_scheme_results)
        
        rhyme_scheme_layout.add_widget(rhyme_scheme_scroll)
        rhyme_scheme_tab.add_widget(rhyme_scheme_layout)
        
        # Add all tabs
        analysis_panel.add_widget(dict_tab)
        analysis_panel.add_widget(rhymes_tab)
        analysis_panel.add_widget(phonetics_tab)
        analysis_panel.add_widget(meter_tab)
        analysis_panel.add_widget(rhyme_scheme_tab)
        
        splitter.add_widget(analysis_panel)
        main_layout.add_widget(splitter)
        
        return main_layout
    
    def analyze_poem(self, text):
        """Analyze the current poem text"""
        if not text.strip():
            return
        
        # Update meter analysis
        meter_data = self.analyzer.analyze_meter(text)
        meter_text = f"Meter Analysis:\n\n"
        
        if meter_data['lines']:
            meter_text += f"Lines: {len(meter_data['lines'])}\n"
            meter_text += f"Consistency: {meter_data['consistency']:.1%}\n\n"
            
            for i, line_data in enumerate(meter_data['lines'], 1):
                meter_text += f"Line {i}: {line_data['syllables']} syllables\n"
                meter_text += f"  {line_data['text']}\n"
                meter_text += f"  Pattern: {line_data['stress_pattern']}\n\n"
        
        self.meter_results.text = meter_text
        self.meter_results.text_size = (dp(300), None)
        
        # Update visual meter
        self.visual_meter.set_meter_data(meter_data)
        
        # Update rhyme scheme analysis
        rhyme_data = self.analyzer.analyze_rhyme_scheme(text)
        rhyme_text = f"Rhyme Scheme Analysis:\n\n"
        rhyme_text += f"Scheme: {rhyme_data['scheme']}\n\n"
        
        for i, line in enumerate(rhyme_data['lines']):
            scheme_letter = rhyme_data['scheme'].split()[i] if i < len(rhyme_data['scheme'].split()) else '-'
            rhyme_text += f"{scheme_letter}: {line}\n"
        
        if rhyme_data['groups']:
            rhyme_text += "\nRhyme Groups:\n"
            for letter, words in rhyme_data['groups'].items():
                rhyme_text += f"{letter}: {', '.join(words)}\n"
        
        self.rhyme_scheme_results.text = rhyme_text
        self.rhyme_scheme_results.text_size = (dp(300), None)
    
    def lookup_word(self, word):
        """Look up word definition"""
        if not word.strip():
            return
        
        definitions = self.analyzer.get_word_definition(word)
        result_text = f"Definitions for '{word}':\n\n"
        
        for i, definition in enumerate(definitions, 1):
            result_text += f"{i}. {definition}\n\n"
        
        self.dict_results.text = result_text
        self.dict_results.text_size = (dp(300), None)
    
    def find_rhymes(self, word):
        """Find rhyming words"""
        if not word.strip():
            return
        
        rhymes = self.analyzer.get_rhymes(word)
        if rhymes:
            result_text = f"Rhymes for '{word}':\n\n"
            result_text += ', '.join(rhymes)
        else:
            result_text = f"No rhymes found for '{word}'"
        
        self.rhyme_results.text = result_text
        self.rhyme_results.text_size = (dp(300), None)
    
    def get_phonetics(self, word):
        """Get phonetic representation"""
        if not word.strip():
            return
        
        phonetics = self.analyzer.get_phonetics(word)
        syllables = self.analyzer.count_syllables(word)
        
        result_text = f"Phonetics for '{word}':\n\n"
        result_text += f"Pronunciation: {phonetics}\n"
        result_text += f"Syllables: {syllables}\n"
        
        self.phonetic_results.text = result_text
        self.phonetic_results.text_size = (dp(300), None)
    
    def new_poem(self, instance):
        """Create new poem"""
        self.poem_editor.text = ""
    
    def save_poem(self, instance):
        """Save poem to file"""
        try:
            # Simple file saving - in real app, would use file dialog
            filename = "my_poem.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.poem_editor.text)
            
            popup = Popup(title='Saved',
                         content=Label(text=f'Poem saved as {filename}'),
                         size_hint=(0.6, 0.4))
            popup.open()
        except Exception as e:
            popup = Popup(title='Error',
                         content=Label(text=f'Could not save: {str(e)}'),
                         size_hint=(0.6, 0.4))
            popup.open()
    
    def load_poem(self, instance):
        """Load poem from file"""
        try:
            # Simple file loading - in real app, would use file dialog
            filename = "my_poem.txt"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    self.poem_editor.text = f.read()
            else:
                popup = Popup(title='Not Found',
                             content=Label(text=f'File {filename} not found'),
                             size_hint=(0.6, 0.4))
                popup.open()
        except Exception as e:
            popup = Popup(title='Error',
                         content=Label(text=f'Could not load: {str(e)}'),
                         size_hint=(0.6, 0.4))
            popup.open()


if __name__ == '__main__':
    VersePadApp().run()
