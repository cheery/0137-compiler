from error import CrunchError

class Environ(object):
    def __init__(self, variables, macros, options):
        self.variables = variables
        self.macros = macros
        self.options = options

    def crunch(self, node):
        macro = self.macros.lookup('%'+node.name)
        if callable(macro):
            return macro(self, node)
        raise CrunchError("no macro found for %%%s %r" % (node.name, node.value), node)

