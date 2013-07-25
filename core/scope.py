class Scope(object):
    def __init__(self, objects, parent):
        self.objects = objects
        self.parent = parent

    def lookup(self, name):
        if name in self.objects:
            return self.objects[name]
        if self.parent is not None:
            return self.parent.lookup(name)

    def assign(self, name, value):
        if name in self.objects:
            self.objects[name] = value
            return True
        if self.parent is not None:
            return self.parent.store(name, value)

    def declare(self, name, value):
        self.objects[name] = value

    def extend(self, objects):
        self.objects.update(objects)
