from error import CrunchError
import os

from clang.cindex import *
from llvm.core import Type, Function

ctypes = {
    'Int': Type.int(),
    'UInt': Type.int(),
    'Pointer': Type.pointer(Type.int(8)),
    'Void': Type.void()
}


class NativeCall(object):
    def __init__(self, node, wrapper, args):
        self.node = node
        self.wrapper = wrapper
        self.args = args

    def codegen(self, builder):
        argv = [arg.codegen(builder) for arg in self.args]
        return builder.call(self.wrapper.fn, argv)

class NativeWrapper(object):
    def __init__(self, env, node, restype, argtypes):
        self.env = env
        self.node = node
        self.restype = ctypes[restype]
        self.argtypes = [ctypes[t] for t in argtypes]
        self.fntype = Type.function(self.restype, self.argtypes)
        self.fn = Function.new(env.options['module'], self.fntype, node.value)

    def __call__(self, node, args):
        if len(args) != len(self.argtypes):
            raise CrunchError("expected %i arguments" % len(args), node)
        return NativeCall(node, self, args)

index = Index.create()

include_paths = [
    '/usr/local/include',
    '/usr/include'
]
def find_file(dirs, name):
    for directory in dirs:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            return path

def as_string(node):
    if node.name != 'string':
        raise CrunchError("not a string", node)
    return node.value[1:-1]

def as_symbol(node):
    if node.name != 'symbol':
        raise CrunchError("not a symbol", node)
    return node.value

def find_decl(node, name):
    if node.kind.is_declaration() and node.spelling == name:
        return node
    for child in node.get_children():
        decl = find_decl(child, name)
        if decl is not None:
            return decl

def make_wrapper(env, node, type):
    if type.kind == TypeKind.FUNCTIONPROTO:
        restype = type.get_result().get_canonical().kind.spelling
        argtypes = []
        for argtype in type.argument_types():
            argtype = argtype.get_canonical()
            argtypes.append(argtype.kind.spelling)
        return NativeWrapper(env, node, restype, argtypes)
    else:
        raise CrunchError("odd item %r" % type.kind, node)

def mac_include(env, node):
    header = as_string(node.value[1])
    names = node.value[2:]
    #names = map(as_symbol, node.value[2:])
    path = find_file(include_paths, header)
    tu = index.parse(path)

    for name in names:
        decl = find_decl(tu.cursor, name.value)
        if decl is None:
            raise CrunchError("not found", name)
        wrap = make_wrapper(env, name, decl.type)
        env.variables.declare(name.value, wrap)

arch = "x86_64-linux-gnu"

link_paths = [
    '/usr/local/lib', '/usr/lib', '/lib',
    '/usr/local/lib/%s' % arch,
    '/usr/lib/%s' % arch,
    '/lib/%s' % arch,
]

def mac_link(env, node):
    lib = as_string(node.value[1])
    path = find_file(link_paths, lib)
    if path is None:
        raise CrunchError("not found", node.value[1])
    env.options['clink'].append(path)

def register(environ):
    environ.options['clink'] = []
    environ.macros.extend(dict(
        cinclude = mac_include,
        clink = mac_link,
    ))
