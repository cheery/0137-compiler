import read, util, sys
from llvm import *
from llvm.core import *
from llvm.ee import *
from core import Scope, Environ, CrunchError

from core import cffi

class NumberLiteral(object):
    def __init__(self, value):
        self.value = value

    def codegen(self, builder):
        return Constant.int(Type.int(), self.value)

def mac_number(env, node):
    if node.value.startswith('0x'):
        return NumberLiteral(int(node.value, 16))
    return NumberLiteral(int(node.value))

def mac_symbol(env, node):
    obj = env.variables.lookup(node.value)
    if obj is None:
        raise CrunchError("no such symbol", node)
    return obj

def mac_invoke(env, node):
    expr = node.value
    if expr[0].name == 'symbol':
        macro = env.macros.lookup(expr[0].value)
        if callable(macro):
            return macro(env, node)
    values = map(env.crunch, expr)
    callee = values[0]
    arguments = values[1:]
    if callable(callee):
        return callee(node, arguments)
    raise CrunchError("not sure how to call %r" % callee, node)

def mac_let(env, node):
    lhs = node.value[1]
    rhs = node.value[2]
    if lhs.name != 'symbol':
        raise CrunchError("only symbols supported on leftside", lhs)
    block = env.crunch(rhs)
    env.variables.declare(lhs.value, block)
    return block

system = Environ(Scope({}, None), Scope({}, None), {})

cffi.register(system)

system.macros.declare('%symbol', mac_symbol)
system.macros.declare('%invoke', mac_invoke)
system.macros.declare('%number', mac_number)
system.macros.declare('=', mac_let)

path = 'examples/simple'

try:
    source = read.file(path)
except read.ReadError, e:
    util.read_error(e.location, e.msg)
    sys.exit(1)

system.options['module'] = module = Module.new(path)

try:
    program = []
    for expr in source:
        block = system.crunch(expr)
        if block is not None:
            program.append( block )

except CrunchError, e:
    util.write_error(sys.stdout, e.msg, e.node.location)
    sys.exit(1)

ty_func = Type.function(Type.int(), [])
f_main = module.add_function(ty_func, "main")

entry = f_main.append_basic_block("entry")
builder = Builder.new(entry)

for block in program:
    block.codegen(builder)

builder.ret(Constant.int(Type.int(), 0))


for filename in system.options['clink']:
    load_library_permanently(filename)

ee = ExecutionEngine.new(module)
 
retval = ee.run_function(f_main, [])
print "returned", retval.as_int()

# create environ
# populate environ
#  - clink "GL"
#  - cinclude "GL/gl.h"
#      glClearColor
#      glSomeOtherStuff
# lulz :)
# attach environ to the programs.

# process everything first in this scope
# then process second layer of lambdas

# construct type inference system
# create C ffi


#class Native(object):
#    def __init__(self, 

## def pass0_compile(expr, env):
##     pass
## 
## def pass0(source):
##     out = []
##     env = Environ(Scope({}, None), Scope({}, None))
## 
##     for expr in source:
##         out.append( pass0_compile(expr, env) )
## 
##     return out
## 
## path = 'examples/simple'
## 
## source = read.file(path)
## 
## program = pass0(source)
## 
## 
## 
## print program
## 
## ty_bool = Type.int(1)
## ty_int = Type.int()
## ty_void = Type.void()
## 
## exit_type = Type.function(ty_void, [ty_int])
## 
## #print_i_sig = Type.function(ty_int, [ty_int])
## runtime = Module.from_assembly(open('runtime.s'))
## 
## sample = Module.new(path)
## sample.link_in(runtime)
## 
## c_exit = Function.new(sample, exit_type, 'exit')
## print c_exit
## 
## print_i = sample.get_type_named('print_i')
## print print_i
## 
## print_i = sample.get_function_named('print_i')
## 
## ty_func = Type.function(ty_int, [])
## f_main = sample.add_function(ty_func, "main")
## entry = f_main.append_basic_block("entry")
## 
## builder = Builder.new(entry)
## 
## builder.call(print_i, [Constant.int(ty_int, 10)])
## 
## builder.call(c_exit, [Constant.int(ty_int, 1)])
## 
## builder.ret(Constant.int(ty_int, 1))
## 
## 
## 
## ee = ExecutionEngine.new(sample)
## 
## retval = ee.run_function(f_main, [])
## print "returned", retval.as_int()
