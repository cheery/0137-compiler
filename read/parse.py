import tokenize
ReadError = tokenize.ReadError

class Node(object):
    def __init__(self, name, value, location):
        self.name = name
        self.value = value
        self.location = location

class Precedence(object):
    lbp = 0
    @staticmethod
    def nud(parser, token):
        if token is None:
            raise ReadError("premature end", None, True)
        raise ReadError("not a prefix %r" % labelof(token), token.location)
    @staticmethod
    def led(parser, left, token):
        raise ReadError("not an operator %r" % labelof(token), token.location)


operators = set()
precedence  = {}

def labelof(token):
    if token is None:
        return None
    if token.name == 'symbol' and token.value in operators:
        return token.value
    return token.name

def sym(token):
    label = labelof(token)
    if label in precedence:
        return precedence[label]
    else:
        return Precedence()

def declare(label):
    if label in precedence:
        res = precedence[label]
    else:
        res = precedence[label] = Precedence()
    return res

def infix(name, bp, rp=0):
    def infix_led(parser, left, token):
        right = expression( parser, bp - rp )
        callee = declare('symbol').nud(parser, token)
        return Node('invoke', [callee, left, right], token.location)
    declare(name).led = infix_led
    declare(name).lbp = bp
    operators.add(name)
infixr = lambda name, bp: infix(name, bp, 1)

def prefix(name):
    def prefix_nud(parser, token):
        right = expression( parser, 70 )
        callee = declare('symbol').nud(parser, token)
        return Node('invoke', [callee, right], token.location)
    declare(name).nud = prefix_nud

declare('number').nud = lambda y, token: Node('number', token.value, token.location)
declare('symbol').nud = lambda y, token: Node('symbol', token.value, token.location)
declare('string').nud = lambda y, token: Node('string', token.value, token.location)

infixr('and', 30)
infixr('or',  30)
infixr('xor', 30)
infix('==', 35)
infix('!=', 35)
infix('<=', 35)
infix('>',  35)
infix('>=', 35)
infix(':', 38)
infix('&', 40)
infix('^', 40)
infix('|', 40)
infix('<<', 45)
infix('>>', 45)
infix('++', 50)
infix('+', 50)
infix('-', 50)
infix('*', 60)
infix('/', 60)
infix('%', 60)
prefix('+')
prefix('-')
prefix('!')

def dot_led(parser, left, token):
    if labelof(parser.nxt) == 'symbol':
        member = declare('symbol').nud(parser, parser.advance())
        return Node('member', [left, member], token.location)
    return Node('invoke', [left], token.location)
declare('dot').led = dot_led
declare('dot').lbp = 1000

def lparen_nud(parser, token):
    invocation = sequence_head(parser, -1, True)
    parser.advance('rparen')
    return invocation
declare('lparen').nud = lparen_nud

def lbracket_nud(parser, token):
    invocation = sequence_head(parser, -1, False)
    parser.advance('rbracket')
    invocation.name = 'list'
    return invocation
declare('lbracket').nud = lbracket_nud

def lbrace_nud(parser, token):
    invocation = sequence_head(parser, -1, False)
    parser.advance('rbrace')
    invocation.name = 'def'
    parser.thief = invocation.value
    return invocation
declare('lbrace').nud = lbrace_nud

def thief_led(parser, left, token):
    parser.thief = [left]
    return Node('invoke', parser.thief, token.location)
operators.add(';')
declare(';').led = thief_led
declare(';').lbp = 1000

assignators = ('=', ':=', '!=', '+=', '-=', '*=', '/=')
operators.update(assignators)

terminators = (None, 'rparen', 'rbracket', 'rbrace')

def sequence(parser, indent, unbox):
    res = exprs = []
    if parser.thief is not None:
        exprs = parser.thief
        parser.thief = None
    while labelof(parser.nxt) == 'newline' and parser.nxt.value == indent:
        current = parser.advance('newline')
        last = sequence_head(parser, current.value, unbox)
        if isinstance(last, list) and len(last) == 0:
            continue
        exprs.append(last)
    return res

def sequence_head(parser, indent, unbox):
    res = []
    start = parser.start
#    if parser.nxt is not None and parser.nxt.name == 'symbol':
#        res.append( declare('symbol').nud(parser, parser.advance()) )
#    if parser.nxt is not None and parser.nxt.name == 'dot':
#        parser.advance()
#        unbox = False
    while labelof(parser.nxt) not in terminators:
        if labelof(parser.nxt) == 'newline':
            if parser.nxt.value <= indent:
                break
            res.extend( sequence(parser, parser.nxt.value, True) )
        elif labelof(parser.nxt) == 'comma':
            res = res[0] if len(res) == 1 else Node('invoke', res, (start, parser.stop, parser.path))
            comma = parser.advance('comma')
            res = [res]
        elif labelof(parser.nxt) in assignators:
            res = res[0] if len(res) == 1 else Node('invoke', res, (start, parser.stop, parser.path))
            assign = declare('symbol').nud(parser, parser.advance() )
            right = sequence_head(parser, indent, True)
            res = [assign, res, right]
        else:
            res.append( expression( parser, 0 ) )
    return res[0] if unbox and len(res) == 1 else Node('invoke', res, (start, parser.stop, parser.path))

def expression(parser, rbp):
    if labelof(parser.nxt) == 'newline':
        parser.advance()
    current = parser.advance()
    left = sym(current).nud(parser, current)
    while rbp < sym(parser.nxt).lbp:
        current = parser.advance()
        left = sym(current).led(parser, left, current)
    return left

def getnext(stream):
    try:
        return stream.next()
    except StopIteration, i:
        return None

class Parser(object):
    def __init__(self, tokens, path):
        self.stream = iter(tokens)
        self.nxt = getnext(self.stream)
        self.start = 0
        self.stop  = 0
        self.path  = path
        self.thief = None

    def advance(self, expect=None):
        last = self.nxt
        if expect and labelof(last) != expect:
            raise ReadError('expected %r, got %r' % (expect, last), last.location)
        self.nxt = getnext(self.stream)
        if last is not None:
            self.stop = last.stop
        if self.nxt is None:
            self.start = self.stop
        else:
            self.start = self.nxt.start
        return last

def tokens(tokens, path=''):
    parser = Parser(tokens, path)
    root = sequence( parser, 0, True )
    if parser.nxt is None:
        return root
    else:
        raise ReadError('parsing prematurely terminated to %r' % labelof(parser.nxt), parser.nxt.location)

def string(source, path=''):
    return tokens(tokenize.string(source, path), path)

def file(path):
    return tokens(tokenize.file(path), path)
