from enum import Enum

class Ast:
    def reduce(self):
        raise NotImplementedError()
    def dup(self):
        raise NotImplementedError()

class SymbolState(Enum):
    NEW = 0
    BOUND = 1
    USED = 2

# Remember that lambdas don't have scopes
# Attempting to get a value out of a new (or used) Symbol is an error,
# I believe that evaluation order should prevent us from attempting to get values out of new symbols
class Symbol:
    # this is a shell to be used once or not at all
    def __init__(self, name: str=''):
        self.name = name
        self.state = SymbolState.NEW
        self.binding = None
    def __str__(self):
        if self.state == SymbolState.NEW:
            return self.name
        if self.state == SymbolState.BOUND:
            return self.binding
        assert False # should not be holing on to Symbols that are used up
    def bind(self, value):
        assert self.state == SymbolState.NEW
        self.binding = value
        self.state = SymbolState.BOUND
    def get(self):
        # normal order reduction behaves lazily
        assert self.state == SymbolState.BOUND
        self.state = SymbolState.USED
        return self.binding

# class DupDir(Enum):
#     LEFT = 0
#     RIGHT = 1

# internal duplication node
class Dup:
    def __init__(self, child):
        self.child = child
        self.cache = None
    def __str__(self):
        return "<Dup {}>".format(str(self.child))
    def execute(self):
        if self.cache == None:
            self.cache = self.child.dup()
        a, b = self.cache
        return a, b

class DupPtr:
    def __init__(self, dup: Dup):
        self.dup = dup
    def __str__(self):
        return str(self.dup)
    def execute(self): # I think this is reduce...
        raise NotImplementedError()
class DupLeft(DupPtr):
    def execute(self):
        a, b = self.dup.execute()
        return a
class DupRight(DupPtr):
    def execute(self):
        a, b = self.dup.execute()
        return b

def dup(child):
    d = Dup(child)
    return DupLeft(d), DupRight(d)

def resolve(ast_node):
    if isinstance(ast_node, Symbol):
        return resolve(ast_node.get())
    if isinstance(ast_node, DupPtr):
        return resolve(ast_node.execute())
    return ast_node

class Sup:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def dup(self):
        # TODO: implement other dup-sup and decision betwen them
        return self.a, self.b

class Lam:
    def __init__(self, param: Symbol, body):
        self.param = param
        self.body = body
    def __str__(self):
        return "<Lam {} {}>".format(str(self.param), str(self.body))
    def reduce(self):
        self.body = resolve(self.body)
        self.body = self.body.reduce()
        return self
    def dup(self):
        xa = Symbol()
        xb = Symbol()
        self.param.bind(Sup(xa, xb))
        self.body = resolve(self.body)
        a, b = dup(self.body)
        return Lam(xa, a), Lam(xb, b)

class App:
    def __init__(self, lam: Lam, arg):
        self.lam = lam
        self.arg = arg
    def __str__(self):
        return "<App {} {}>".format(str(self.lam), str(self.arg))
    def reduce(self):
        # replace instance with parameter
        # Note that the arg must be used 0 or 1 time(s)
        self.lam = resolve(self.lam)
        self.lam.param.bind(self.arg)
        self.lam = self.lam.reduce() # or should we call reduce on body here?
        return self.lam.body
    # def dup()

# class Add:
#     def __init__(self, lhs, rhs):
#         self.lhs = lhs
#         self.rhs = rhs
#     def __str__(self):
#         return "<Add {} {}>".format(str(self.lhs), str(self.rhs))

# class Mul:
#     def __init__(self, lhs, rhs):
#         self.lhs = lhs
#         self.rhs = rhs
#     def __str__(self):
#         return "<Mul {} {}>".format(str(self.lhs), str(self.rhs))

class Int:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)
    def reduce(self):
        return self
    def dup(self):
        return self, self # okay because Int is immutable

def simple_test():
    x = Symbol("x")
    f = Lam(x, x)
    e = App(f, Int(0))
    print(e)
    e = e.reduce()
    print(e)
    print()

def test_from_hvm_how_doc():
    x = Symbol("x")
    y = Symbol("y")
    a, b = Dup(Lam)

def medium_test():
    x = Symbol("x")
    f = Lam(x, x)
    fa, fb = dup(f)
    e = App(fa, App(fb, Int(0)))
    print(e)
    e = e.reduce()
    print(e)
    print()

def complex_test():
    x = Symbol("x")
    f = Lam(x, x)
    fa, fb = Dup(f).syms()
    x1 = Symbol("x1")
    f1 = Lam(x1, App(fa, App(fb, x1)))
    f1a, f1b = Dup(f1).syms()
    e = App(f1a, App(f1b, Int(0)))
    print(e)
    e = e.reduce()
    print(e)
    print()

# simple_test()
medium_test()
# complex_test()

print("done")
