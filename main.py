from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.clock import Clock

import pronouncing
import nltk
import re
import difflib
import random
import os
from collections import defaultdict
from nltk.corpus import wordnet, words, cmudict

nltk.download('words', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('cmudict', quiet=True)

english_words = set(words.words())
cmu_dict = cmudict.dict()

class VersePad(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        Window.clearcolor = get_color_from_hex('#f0f5ff')

        self.fast_event = None
        self.slow_event = None

        toolbar = BoxLayout(size_hint=(1, None), height=dp(40))
        toolbar.add_widget(Button(text='Save', on_press=self.save_poem))
        toolbar.add_widget(Button(text='Load', on_press=self.load_poem))
        toolbar.add_widget(Button(text='Clear', on_press=self.clear_text))
        self.add_widget(toolbar)

        self.text_input = TextInput(
            hint_text="Write your poem here...",
            font_size=dp(22),
            size_hint=(1, 0.7),
            background_color=get_color_from_hex('#ffffff'),
            foreground_color=get_color_from_hex('#333333'),
            multiline=True,
            padding=dp(15)
        )
        self.text_input.bind(text=self.on_text_change)
        self.add_widget(self.text_input)

        self.tabs = TabbedPanel(do_default_tab=False, size_hint=(1, 0.3), tab_width=dp(120))
        self.dict_tab = self.add_tab("Dictionary")
        self.rhyme_tab = self.add_tab("Rhymes")
        self.meter_tab = self.add_tab("Meter")
        self.grammar_tab = self.add_tab("Grammar")
        self.thesaurus_tab = self.add_tab("Thesaurus")
        self.add_widget(self.tabs)

    def add_tab(self, title):
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        label = Label(
            size_hint=(None, None),
            text_size=(None, None),
            markup=True,
            halign='left',
            valign='top',
            font_size=dp(16),
            color=get_color_from_hex('#FFFFFF')
        )
        label.bind(texture_size=lambda instance, size: setattr(instance, 'size', size))
        scroll.add_widget(label)
        tab = TabbedPanelItem(text=title)
        tab.add_widget(scroll)
        self.tabs.add_widget(tab)
        return label

    def on_text_change(self, instance, value):
        if self.fast_event:
            self.fast_event.cancel()
        if self.slow_event:
            self.slow_event.cancel()
        self.fast_event = Clock.schedule_once(lambda dt: self.update_fast_tabs(value), 0.2)
        self.slow_event = Clock.schedule_once(lambda dt: self.update_slow_tabs(value), 1.0)

    def update_fast_tabs(self, text):
        self.update_rhyme(text)
        self.update_meter(text)

    def update_slow_tabs(self, text):
        self.update_dictionary(text)
        self.update_thesaurus(text)
        self.update_grammar(text)

    def get_word_at_cursor(self):
        cursor_index = self.text_input.cursor_index()
        text = self.text_input.text
        left = re.findall(r'\w+$', text[:cursor_index])
        right = re.findall(r'^\w+', text[cursor_index:])
        return (left[0] if left else "") + (right[0] if right else "")

    def update_dictionary(self, text):
        word = self.get_word_at_cursor()
        if not word:
            self.dict_tab.text = "Move cursor over a word to see info"
            return

        output = f"[b][color=3366ff]Dictionary for:[/color] [b]{word}[/b][/b]\n\n"

        if word.lower() in english_words:
            output += "[color=33cc33]✓ correct spelling[/color]\n"
        else:
            sugg = difflib.get_close_matches(word, english_words, n=2)
            if sugg:
                output += f"[color=ff6600]Suggestions: {', '.join(sugg)}[/color]\n"
            else:
                output += "[color=ff0000]Possibly incorrect[/color]\n"

        syns = wordnet.synsets(word.lower())
        if syns:
            output += f"[i]Definition:[/i] {syns[0].definition()}\n"
        phones = pronouncing.phones_for_word(word.lower())
        if phones:
            output += f"[i]Syllables:[/i] {pronouncing.syllable_count(phones[0])}\n"

        self.dict_tab.text = output

    def update_rhyme(self, text):
        word = self.get_word_at_cursor()
        if not word:
            self.rhyme_tab.text = "Move cursor over a word to get rhymes"
            return

        try:
            rhymes = sorted(pronouncing.rhymes(word), key=str.lower)
            near = self.get_near_rhymes(word)
            phrases = self.get_rhyming_phrases(word, text)
            output = f"[b][color=ff3333]Perfect Rhymes for '{word}':[/color][/b] ({len(rhymes)})\n\n"
            output += '\n'.join(rhymes[:100]) or "None found"
            output += f"\n\n[b][color=ff9933]Near Rhymes:[/color][/b] ({len(near)})\n\n"
            output += ', '.join(near[:30]) or "None found"
            output += f"\n\n[b]Phrases:[/b]\n"
            output += '\n'.join(phrases[:5]) or "Try another word"
            self.rhyme_tab.text = output
        except Exception as e:
            self.rhyme_tab.text = f"Rhyme error: {str(e)}"

    def get_near_rhymes(self, word):
        if word.lower() not in cmu_dict:
            return []
        target = cmu_dict[word.lower()][0][-2:]
        return [w for w, p in cmu_dict.items() if w != word.lower() and len(p[0]) > 2 and p[0][-2:] == target]

    def get_rhyming_phrases(self, word, text):
        patterns = [f"{word} and {{}}", f"{{}} {word}", f"{word} {{}}"]
        rhymes = pronouncing.rhymes(word)
        return [p.format(r) for p in patterns for r in random.sample(rhymes, min(3, len(rhymes)))] if rhymes else []

    def update_meter(self, text):
        lines = [l for l in text.splitlines() if l.strip()][-5:]
        output = "[b][color=9933cc]Meter Analysis:[/color][/b]\n\n"
        for idx, line in enumerate(lines, 1):
            words_list = [re.sub(r'[^A-Za-z]', '', w) for w in line.split()]
            pattern = ""
            syllables = []
            total_syllables = 0
            for w in words_list:
                phones = pronouncing.phones_for_word(w)
                if phones:
                    stress = pronouncing.stresses(phones[0])
                    visual = stress.replace('0', '˘').replace('1', '/').replace('2', '\\')
                    pattern += visual + " "
                    total_syllables += pronouncing.syllable_count(phones[0])
                    syllables.append(f"[b]{w}[/b] ({pronouncing.syllable_count(phones[0])})")
                else:
                    syllables.append(f"[b]{w}[/b] (?)")
            output += f"[b]Line {idx}[/b] ({total_syllables} syllables):\n"
            output += ' + '.join(syllables) + "\n"
            output += f"Pattern: {pattern.strip()}\n\n"
        self.meter_tab.text = output if text.strip() else "No text to analyze"

    def update_grammar(self, text):
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        output = "[b][color=ffaa00]Grammar & Style:[/color][/b]\n\n"
        word_count = len(text.split())
        avg_line = word_count / len(lines) if lines else 0
        output += f"Lines: {len(lines)} | Words: {word_count} | Avg: {avg_line:.1f} words/line\n\n"

        issues = []
        word_freq = defaultdict(int)
        all_words = re.findall(r'\b\w+\b', text.lower())
        for word in all_words:
            word_freq[word] += 1

        for i, line in enumerate(lines[:20], 1):
            words = line.split()
            if words and words[0][0].islower():
                issues.append(f"Line {i}: Start with capital")
            if len(words) < 3:
                issues.append(f"Line {i}: Too short")
            elif len(words) > 15:
                issues.append(f"Line {i}: Too long")
            if line[-1] not in '.!?':
                issues.append(f"Line {i}: Missing punctuation")

        repeats = [w for w, count in word_freq.items() if count >= 4 and len(w) > 3]
        if repeats:
            issues.append("Repetitions: " + ", ".join(repeats[:3]))

        self.grammar_tab.text = output + ("\n".join(issues[:20]) if issues else "No issues found")

    def update_thesaurus(self, text):
        word = self.get_word_at_cursor()
        if not word:
            self.thesaurus_tab.text = "Move cursor over a word for synonyms"
            return
        synonyms, antonyms = set(), set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                if lemma.name().lower() != word.lower():
                    synonyms.add(lemma.name().replace("_", " "))
                if lemma.antonyms():
                    antonyms.add(lemma.antonyms()[0].name().replace("_", " "))
        output = f"[b][color=00cc66]Thesaurus for '{word}':[/color][/b]\n\n"
        output += f"[b]Synonyms:[/b] {', '.join(sorted(synonyms)[:15]) or 'None'}\n"
        output += f"\n[b]Antonyms:[/b] {', '.join(sorted(antonyms)[:10]) or 'None'}"
        self.thesaurus_tab.text = output

    def save_poem(self, instance):
        content = self.text_input.text
        if not content.strip():
            return
        box = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(path=os.getcwd(), filters=["*.txt"])
        box.add_widget(chooser)
        btns = BoxLayout(size_hint_y=None, height=dp(40))
        btns.add_widget(Button(text='Cancel', on_press=lambda x: popup.dismiss()))
        btns.add_widget(Button(text='Save', on_press=lambda x: self._save_file(chooser.path, chooser.selection, content, popup)))
        box.add_widget(btns)
        popup = Popup(title='Save Poem', content=box, size_hint=(0.9, 0.9))
        popup.open()

    def _save_file(self, path, selection, content, popup):
        name = selection[0] if selection else "poem.txt"
        full = os.path.join(path, name)
        if not full.endswith('.txt'):
            full += '.txt'
        with open(full, 'w') as f:
            f.write(content)
        popup.dismiss()

    def load_poem(self, instance):
        box = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(path=os.getcwd(), filters=["*.txt"])
        box.add_widget(chooser)
        btns = BoxLayout(size_hint_y=None, height=dp(40))
        btns.add_widget(Button(text='Cancel', on_press=lambda x: popup.dismiss()))
        btns.add_widget(Button(text='Load', on_press=lambda x: self._load_file(chooser.selection, popup)))
        box.add_widget(btns)
        popup = Popup(title='Load Poem', content=box, size_hint=(0.9, 0.9))
        popup.open()

    def _load_file(self, selection, popup):
        try:
            with open(selection[0], 'r') as f:
                self.text_input.text = f.read()
            popup.dismiss()
        except Exception as e:
            self.grammar_tab.text = f"Load error: {str(e)}"

    def clear_text(self, instance):
        self.text_input.text = ""

class VersePadApp(App):
    def build(self):
        self.title = "VersePad Pro"
        return VersePad()

if __name__ == "__main__":
    VersePadApp().run()
