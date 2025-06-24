class Stream:
    def __init__(self):
        self.elements = []
    def append(self, obj):
        self.elements.append(obj)
    @property
    def notes(self):
        return [e for e in self.elements if hasattr(e, 'quarterLength')]
    def flatten(self):
        return self
    def write(self, fmt, fp=None):
        print(f"Mock write: {fmt} -> {fp}")
