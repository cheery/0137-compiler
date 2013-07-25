import sys

HEADER = '\033[95m'
OKBLUE = '\033[94m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def getlines(path):
    with open(path) as fd:
        return fd.readlines()

def dump_lines(start, stop, lines, C):
    k1 = 0
    for no, line in enumerate(lines, 1):
        k0 = k1
        k1 += len(line)
        show = False
        if k0 <= stop < k1:
            cut = stop - k0
            line = line[:cut] + ENDC + line[cut:]
            show = True
        else:
            line = line + ENDC
        if k0 <= start < k1:
            cut = start - k0
            line = line[:cut] + C + line[cut:]
            show = True
        else:
            line = C + line
        if start < k0 and k1 <= stop:
            show = True
        if show:
            yield no, line

def write_error(fd, msg, location):
    fd.write(msg + '\n')
    if location is not None:
        start, stop, path = location
        for no, line in dump_lines(start, stop, getlines(path), FAIL):
            fd.write((HEADER+" %3i"+ENDC+"  %s") % (no, line))
    fd.flush()

    

def read_error(location, msg):
    if location is None:
        sys.stderr.write('read  %s\n' % msg)
    else:
        (start, stop, path) = location
        lines = getlines(path)
        sys.stderr.write('read  %s\n' % msg)
        sys.stderr.write('file  %s\n' % path)
        for no, line in dump_lines(start, stop, lines, FAIL):
            sys.stderr.write((HEADER+" %3i"+ENDC+"  %s") % (no, line))
        sys.stderr.flush()

def recurse(tokens):
    for token in tokens:
        yield token
        if isinstance(token.value, list):
            for subtoken in recurse(token.value):
                yield subtoken

def token_dump(tokens):
    lastpath = ''
    lines = []
    for token in recurse(tokens):
        path = token.location[2]
        if path != lastpath:
            sys.stdout.write('file            %s\n' % path)
            lines = getlines(path)
        start, stop, lastpath = token.location
        tn = token.name
        for no, line in dump_lines(start, stop, lines, OKBLUE):
            sys.stdout.write((HEADER+" %3i"+ENDC+"  %8s  %s") % (no, tn, line))
            tn = ''
    sys.stdout.flush()


#import tokenize
#try:
#    tokens = tokenize.file('bad')
#    token_dump(tokens)
#except tokenize.ReadError, e:
#    read_error(e.location, e.msg)
