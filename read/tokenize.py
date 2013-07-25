class ReadError(Exception):
    def __init__(self, msg, location, canfix=False):
        self.msg = msg
        self.location = location
        self.canfix = canfix
    def __repr__(self):
        return self.msg

class Token(object):
    def __init__(self, name, value, start, stop, path):
        self.name = name
        self.value = value
        self.start = start
        self.stop  = stop
        self.path = path
    @property
    def location(self):
        return self.start, self.stop, self.path

class Newline(object):
    def __init__(self, parent, start):
        self.indent = 0
        self.parent = parent
        self.start  = start

    def letter(self, i, n):
        if n == '\n':
            self.indent = 0
            return self
        if n == '#':
            return Comment(self.parent, self.start)
        if n.isspace():
            self.indent += 1
            return self
        return self.gen(i).letter(i, n)

    def fin(self, i):
        return self.parent.fin(i)
 
    def gen(self, stop):
        return self.parent.mktoken('newline', self.indent, self.start, stop)

class Comment(object):
    def __init__(self, parent, start):
        self.parent = parent
        self.start = start

    def letter(self, i, n):
        if n == '\n':
            return Newline(self.parent, self.start)
        return self

    def fin(self, i):
        return self.parent.fin(i)

class Number(object):
    def __init__(self, parent, start, first):
        self.data   = first
        self.parent = parent
        self.start  = start

    def letter(self, i, n):
        if n.isalnum() or n == '.':
            self.data += n
            return self
        return self.gen(i).letter(i, n)

    def fin(self, i):
        return self.gen(i).fin(i)

    def gen(self, stop):
        return self.parent.mktoken('number', self.data, self.start, stop)

class Symbol(object):
    def __init__(self, parent, start, first):
        self.data   = first
        self.parent = parent
        self.start  = start
        self.first  = first

    def letter(self, i, n):
        if n.isalnum() or n == '_':
            self.data += n
            return self
        return self.gen(i).letter(i, n)

    def fin(self, i):
        return self.gen(i).fin(i)

    def gen(self, stop):
        return self.parent.mktoken('symbol', self.data, self.start, stop)

class String(object):
    def __init__(self, parent, start, notation):
        self.data = notation
        self.parent = parent
        self.start = start
        self.notation = notation

    def letter(self, i, n):
        self.data += n
        if n == self.notation:
            return self.gen(i+1)
        return self

    def fin(self, stop):
        raise ReadError("unterminated string", (self.start, stop, self.parent.path), canfix=True)

    def gen(self, stop):
        return self.parent.mktoken('string', self.data, self.start, stop)

class Special(object):
    characters = '!%&*+-/<=>:;|'
    def __init__(self, parent, start, first):
        self.data   = first
        self.parent = parent
        self.start  = start

    def letter(self, i, n):
        if n in self.characters:
            self.data += n
            return self
        return self.gen(i).letter(i, n)

    def fin(self, i):
        return self.gen(i).fin(i)

    def gen(self, stop):
        return self.parent.mktoken('symbol', self.data, self.start, stop)

    def __repr__(self):
        return "op%r" % (self.data)

class Any(object):
    def __init__(self, start, path):
        self.data = []
        self.start = start
        self.path = path

    def letter(self, i, n):
        if n == '\n':
            return Newline(self, i)
        if n.isspace():
            return self
        if n == '#':
            return Comment(self, i)
        if n == '(':
            return self.mktoken('lparen', None, i, i+1)
        if n == ')':
            return self.mktoken('rparen', None, i, i+1)
        if n == '[':
            return self.mktoken('lbracket', None, i, i+1)
        if n == ']':
            return self.mktoken('rbracket', None, i, i+1)
        if n == '{':
            return self.mktoken('lbrace', None, i, i+1)
        if n == '}':
            return self.mktoken('rbrace', None, i, i+1)
        if n == ',':
            return self.mktoken('comma', None, i, i+1)
        if n == '@':
            return self.mktoken('home', None, i, i+1)
        if n == '.':
            return self.mktoken('dot', None, i, i+1)
        if n.isdigit():
            return Number(self, i, n)
        if n.isalpha() or n == '_':
            return Symbol(self, i, n)
        if n in Special.characters:
            return Special(self, i, n)
        if n in "'\"":
            return String(self, i, n)
        raise ReadError('unexpected character %r' % n, (i, i+1, self.path))

    def fin(self, i):
        return self.data

    def mktoken(self, name, value, start, stop):
        self.data.append(Token(name, value, start, stop, self.path))
        return self

def string(source, path=''):
    reader = Newline(Any(0, path), 0)
    for i, n in enumerate(source):
        reader = reader.letter(i, n)
    return reader.fin(len(source))

def file(path):
    with open(path) as fd:
        return string(fd.read(), path)
