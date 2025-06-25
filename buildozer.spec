[app]
title = MIDI Piano Roll
package.name = miditools
package.domain = org.midi
version = 1.0
source.dir = .
source.include_exts = py,png,npy,ogg,mid
source.include_dirs = corpus
requirements = 
    python3,
    kivy,
    music21,
    mido,
    matplotlib,
    numpy

android.permissions = 
android.arch = arm64-v8a
p4a.branch = develop

[buildozer]
log_level = 2
