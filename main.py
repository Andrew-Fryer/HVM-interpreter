from enum import Enum

class SymbolState(Enum):
    NEW = 0
    BOUND = 1
    USED = 2

# Remember that lambdas don't have scopes
# Attempting to get a value out of a new (or used) Symbol is an error,
# I believe that evaluation order should prevent us from attempting to get values out of new symbols
class Symbol:
    # this is a shell to be used once or not at all
    # presently, this is only used for lambda parameters
    ctr = 0
    space = ['']
    def __init__(self, name: str=''):
        while name in Symbol.space:
            name = 'x_' + str(Symbol.ctr)
            Symbol.ctr += 1
        Symbol.space.append(name)
        self.name = name
        self.state = SymbolState.NEW
        self.binding = None
    def __str__(self):
        if self.state == SymbolState.NEW:
            return self.name
        if self.state == SymbolState.BOUND:
            return "{}=[{}]".format(self.name, str(self.binding))
            # return str(self.binding) # causes infinite recursion
        # assert False # should not be holing on to Symbols that are used up
        return self.name
    def bind(self, value):
        assert self.state == SymbolState.NEW
        self.binding = value
        self.state = SymbolState.BOUND
    def get(self):
        # normal order reduction behaves lazily
        assert self.state == SymbolState.BOUND
        self.state = SymbolState.USED
        return self.binding

# internal duplication node used to signify that there are 2 refs to this ast node
class Dup:
    ctr = 0
    def __init__(self, child):
        self.child = child
        self.left = None
        self.right = None
        self.cache = None

        self.id = Dup.ctr
        Dup.ctr += 1
    def link_in(self, left, right):
        self.left = left
        self.right = right

class DupState(Enum):
    FRESH = 0
    EXECUTED = 1

class DupPtr:
    def __init__(self, dup: Dup):
        self.d = dup
        self.state = DupState.FRESH
        self.binding = None
    def bind(self, value):
        assert self.state == DupState.FRESH
        self.binding = value
        self.state = DupState.EXECUTED
    def __str__(self):
        return str(self.d)
class DupLeft(DupPtr):
    def __str__(self):
        if self.state == DupState.EXECUTED:
            return "<DupLeft {}>".format(str(self.binding))
        return "<Dup_{} {}>".format(str(self.d.id), str(self.d.child))
class DupRight(DupPtr):
    def __str__(self):
        if self.state == DupState.EXECUTED:
            return "<DupRight {}>".format(str(self.binding))
        return "<Dup_{}>".format(str(self.d.id))

# helper for building ASTs in tests
def dup(child):
    d = Dup(child)
    l, r = DupLeft(d), DupRight(d)
    d.link_in(l, r)
    return l, r

class Sup:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __str__(self):
        return "{" + str(self.left) + ", " + str(self.right) + "}"

class Lam:
    def __init__(self, param: Symbol, body):
        self.param = param
        self.body = body
    def __str__(self):
        return "<Lam {} {}>".format(str(self.param), str(self.body))

class App:
    def __init__(self, lam: Lam, arg):
        self.lam = lam
        self.arg = arg
    def __str__(self):
        return "<App {} {}>".format(str(self.lam), str(self.arg))

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

class Evaluator:
    def __init__(self):
        pass
    def eval(self, ast):
        done = False
        while not done:
            print(ast)
            ast, done = self.reduce(ast)
        return ast
    def reduce(self, ast):
        done = False
        if isinstance(ast, App):
            app = ast
            # try to perform application
            lam, arg = app.lam, app.arg
            if isinstance(lam, Lam):
                # perform application
                lam.param.bind(app.arg)
                ast = lam.body
            if isinstance(lam, Symbol):
                # substitue symbol
                app.lam = lam.get()
            elif isinstance(lam, DupPtr):
                dup_ptr = lam
                # is this correct? Like, does this violate normal order reduction?
                app.lam, d = self.reduce(dup_ptr)
                # ensure we made progress reducing the child
                assert not d
        elif isinstance(ast, Symbol):
            ast = ast.get()
        elif isinstance(ast, DupPtr):
            dup_ptr = ast
            if dup_ptr.state == DupState.EXECUTED:
                ast = dup_ptr.binding
            else:
                # the dup has not been executed
                dup_node = dup_ptr.d
                c = dup_node.child
                d = True
                if isinstance(c, App)\
                    or isinstance(c, Symbol)\
                        or isinstance(c, DupPtr):
                    dup_node.child, d = self.reduce(c)
                    # ensure we made progress reducing the child
                    assert not d
                else:
                    # perform duplication
                    # this feels like a visitor class
                    left, right = None, None
                    if isinstance(c, Int):
                        left, right = c, c
                    elif isinstance(c, Sup):
                        sup = c
                        # TODO: implement decision betwen Dup-Sup rules
                        # See https://github.com/Kindelia/HVM/blob/master/HOW.md#superposed-duplication
                        '''
                        If this Dup-Sup represents the end of a duplication process, it must go with the former rule. However, if you're duplicating a term, which itself duplicates something, then this rule must be used.
                        '''
                        end_of_duping = True
                        if end_of_duping:
                            left, right = sup.left, sup.right
                        else:
                            # Notation from HVM How:
                            # a, b = sup.left, sup.right
                            # xA, yA = dup(a)
                            # xB, yB = dup(b)
                            # x = Sup(xA, xB)
                            # y = Sup(yA, yB)
                            # left, right = x, y
                            la, lb = dup(sup.left)
                            ra, rb = dup(sup.right)
                            left, right = Sup(la, ra), Sup(lb, rb)
                    elif isinstance(c, Lam):
                        lam = c
                        # incrementally clone lambda
                        xa = Symbol()
                        xb = Symbol()
                        lam.param.bind(Sup(xa, xb))
                        a, b = dup(lam.body)
                        left, right = Lam(xa, a), Lam(xb, b)
                    else:
                        assert False
                    dup_node.left.bind(left)
                    dup_node.right.bind(right)
                    assert dup_ptr.state == DupState.EXECUTED
        elif isinstance(ast, Lam):
            done = True
        elif isinstance(ast, Int):
            done = True
        elif isinstance(ast, Sup):
            assert False
        else:
            assert False
        return ast, done

def simple_test_evaluator():
    x = Symbol("x")
    f = Lam(x, x)
    e = App(f, Int(0))
    e = Evaluator().eval(e)
    print()

def test_from_hvm_how_doc():
    x = Symbol("x")
    y = Symbol("y")
    a, b = dup(Lam)
    # TODO

def medium_test_evaluator():
    x = Symbol("x")
    f = Lam(x, x)
    fa, fb = dup(f)
    e = App(fa, App(fb, Int(0)))
    e = Evaluator().eval(e)
    print()

def complex_test_evaluator():
    x = Symbol("x")
    f = Lam(x, x)
    fa, fb = dup(f)
    x1 = Symbol("x1")
    f1 = Lam(x1, App(fa, App(fb, x1)))
    f1a, f1b = dup(f1)
    e = App(f1a, App(f1b, Int(0)))
    e = Evaluator().eval(e)
    print()

def trick_test_evaluator():
    # from HVM How page:
    # let g = λf(λx(f (f x)))
    # (g g)
    x = Symbol("x")
    f = Symbol("f")
    g = Lam(f, Lam(x, App(f, App(f, x))))
    e = App(g, g)
    e = Evaluator().eval(e)
    print()

simple_test_evaluator()
medium_test_evaluator()
complex_test_evaluator()
# trick_test_evaluator()

print("done")
