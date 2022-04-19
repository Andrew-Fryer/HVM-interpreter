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

        self.id = Dup.ctr # this is unique for all Dup objects
        Dup.ctr += 1
    def link_in(self, left, right):
        self.left = left
        self.right = right

class DupState(Enum):
    FRESH = 0
    EXECUTED = 1

# duplicate/fan in nodes
class DupPtr:
    def __init__(self, dup: Dup, id):
        self.d = dup
        self.id = id # this is the id of the ansector/original dup in the source 
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
def dup(child, id=None):
    d = Dup(child)
    if id == None:
        id = d.id # this should only be used when manually building a graph
    l, r = DupLeft(d, id), DupRight(d, id)
    d.link_in(l, r)
    return l, r

# superposition/fan out node
class Sup:
    def __init__(self, left, right, dup_id):
        self.left = left
        self.right = right
        self.id = dup_id
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

class Add:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def __str__(self):
        return "<Add {} {}>".format(str(self.lhs), str(self.rhs))

class Mul:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def __str__(self):
        return "<Mul {} {}>".format(str(self.lhs), str(self.rhs))

class Int:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class Ite:
    def __init__(self, predicate, then_exp, else_exp):
        self.predicate = predicate
        self.then_exp = then_exp
        self.else_exp = else_exp
    def __str__(self):
        return "<Ite {} {} {}>".format(str(self.predicate), str(self.then_exp), str(self.else_exp))

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
                print("\treducing App")
                lam.param.bind(app.arg)
                ast = lam.body
            elif isinstance(lam, Symbol):
                # substitue symbol
                print("\treducing Symbol")
                app.lam = lam.get()
            elif isinstance(lam, DupPtr):
                dup_ptr = lam
                # is this correct? Like, does this violate normal order reduction?
                app.lam, d = self.reduce(dup_ptr)
                # ensure we made progress reducing the child
                assert not d
            elif isinstance(lam, App):
                app_inner = lam
                app.lam, d = self.reduce(app_inner)
                # ensure we made progress reducing the child
                assert not d
            elif isinstance(lam, Sup):
                sup = lam
                arg_a, arg_b = dup(arg, sup.id)
                print("\treducing App Sup")
                ast = Sup(App(sup.left, arg_a), App(sup.right, arg_b), sup.id)
            else:
                assert False
        elif isinstance(ast, Symbol):
            print("\treducing Symbol")
            ast = ast.get()
        elif isinstance(ast, DupPtr):
            dup_ptr = ast
            if dup_ptr.state == DupState.EXECUTED:
                print("\treducing Dup shell")
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
                        print("\treducing Dup Int")
                        left, right = c, c
                    elif isinstance(c, Ite):
                        ite = c
                        print("\treducing Dup Ite")
                        pa, pb = dup(ite.predicate, dup_ptr.id)
                        ta, tb = dup(ite.then_exp, dup_ptr.id)
                        ea, eb = dup(ite.else_exp, dup_ptr.id)
                        left, right = Ite(pa, ta, ea), Ite(pb, tb, eb)
                    elif isinstance(c, Add):
                        add = c
                        print("\treducing Dup Add")
                        la, lb = dup(add.lhs, dup_ptr.id)
                        ra, rb = dup(add.rhs, dup_ptr.id)
                        left, right = Add(la, ra), Add(lb, rb)
                    elif isinstance(c, Mul):
                        mul = c
                        print("\treducing Dup Mul")
                        la, lb = dup(mul.lhs, dup_ptr.id)
                        ra, rb = dup(mul.rhs, dup_ptr.id)
                        left, right = Mul(la, ra), Mul(lb, rb)
                    elif isinstance(c, Sup):
                        sup = c
                        print("\treducing Dup Sup")
                        # print("\n***LEFT: {}***\n***RIGHT: {}***\n".format(str(sup.left), str(sup.right)))
                        # See https://github.com/Kindelia/HVM/blob/master/HOW.md#superposed-duplication
                        '''
                        "If this Dup-Sup represents the end of a duplication process, it must go with the former rule. However, if you're duplicating a term, which itself duplicates something, then this rule must be used."
                        '''
                        # next line is copied from:
                        # https://github.com/Kindelia/HVM/blob/master/src/runtime.c#L622
                        end_of_duping = dup_ptr.id == c.id
                        # end_of_duping = True
                        if end_of_duping:
                            print("\tusing Dup-Sup 1")
                            left, right = sup.left, sup.right
                        else:
                            # Notation from HVM How:
                            # a, b = sup.left, sup.right
                            # xA, yA = dup(a)
                            # xB, yB = dup(b)
                            # x = Sup(xA, xB)
                            # y = Sup(yA, yB)
                            # left, right = x, y
                            print("\tusing Dup-Sup 2")
                            la, lb = dup(sup.left, dup_ptr.id)
                            ra, rb = dup(sup.right, dup_ptr.id)
                            left, right = Sup(la, ra, sup.id), Sup(lb, rb, sup.id)
                    elif isinstance(c, Lam):
                        print("\treducing Dup Lam")
                        lam = c
                        # incrementally clone lambda
                        xa = Symbol()
                        xb = Symbol()
                        lam.param.bind(Sup(xa, xb, dup_ptr.id))
                        a, b = dup(lam.body, dup_ptr.id)
                        left, right = Lam(xa, a), Lam(xb, b)
                    else:
                        assert False
                    dup_node.left.bind(left)
                    dup_node.right.bind(right)
                    assert dup_ptr.state == DupState.EXECUTED
        elif isinstance(ast, Add):
            add = ast
            print("\treducing Add")
            if not isinstance(add.lhs, Int):
                add.lhs, d = self.reduce(add.lhs)
                assert not d
            elif not isinstance(add.rhs, Int):
                add.rhs, d = self.reduce(add.rhs)
                assert not d
            else:
                ast = Int(add.lhs.value + add.rhs.value)
        elif isinstance(ast, Mul):
            mul = ast
            if not isinstance(mul.lhs, Int):
                mul.lhs, d = self.reduce(mul.lhs)
                assert not d
            elif not isinstance(mul.rhs, Int):
                mul.rhs, d = self.reduce(mul.rhs)
                assert not d
            else:
                print("\treducing Mul")
                ast = Int(mul.lhs.value * mul.rhs.value)
        elif isinstance(ast, Ite):
            ite = ast
            if not isinstance(ite.predicate, Int):
                ite.predicate, d = self.reduce(ite.predicate)
                assert not d
            else:
                print("\treducing Ite")
                ast = ite.then_exp if ite.predicate.value != 0 else ite.else_exp
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
    fa, fb = dup(f)
    g = Lam(f, Lam(x, App(fa, App(fb, x))))
    ga, gb = dup(g)
    e = App(ga, gb)
    e = Evaluator().eval(e)
    print()

def my_test_evaluator():
    x0 = Symbol("x0")
    x1 = Symbol("x1")
    x2 = Symbol("x2")
    f0 = Lam(x0, x0)
    f0a, f0b = dup(f0)
    f1 = Lam(x1, App(f0a, App(f0b, x1)))
    f1a, f1b = dup(f1)
    f2 = Lam(x2, App(f1a, App(f1b, x2)))
    e = App(f2, Int(0))
    e = Evaluator().eval(e)
    print()

def test_k_combinator():
    x = Symbol("a")
    i = Lam(x, x)
    ia, ib = dup(i)
    x = Symbol("x")
    y = Symbol("y")
    k = Lam(x, Lam(y, x))
    e = App(App(k, App(ia, Int(0))), App(ib, Int(1)))
    e = Evaluator().eval(e)
    print()

def test_dups_different():
    x = Symbol("a")
    i = Lam(x, x)
    ia, ib = dup(i)
    e = Mul(App(ia, Int(500)), App(ib, Int(7)))
    e = Evaluator().eval(e)
    print()

def use_y_combinator():
    x1 = Symbol()
    x1a, x1b = dup(x1)
    x2 = Symbol()
    x2a, x2b = dup(x2)
    f = Symbol()
    fa, fb = dup(f)
    y = Lam(f, App(
        Lam(x1, App(fa, App(x1a, x1b))),
        Lam(x2, App(fb, App(x2a, x2b)))
    ))

    f = Symbol()
    n = Symbol()
    na, n_ = dup(n)
    # nb, nc = dup(n_)
    # I think it is okay to use n_ twice because it will only be used once because of the semantics of Ite
    fun = Lam(n, Lam(f, Ite(na, App(f, Add(n_, 1)), n_)))

    e = App(y, App(fun, Int(-1)))

    e = Evaluator().eval(e)
    print()

def factorial():
    x1 = Symbol()
    x1a, x1b = dup(x1)
    x2 = Symbol()
    x2a, x2b = dup(x2)
    f = Symbol()
    fa, fb = dup(f)
    y = Lam(f, App(
        Lam(x1, App(fa, App(x1a, x1b))),
        Lam(x2, App(fb, App(x2a, x2b)))
    ))

    # I'm copying this from here:
    # https://levelup.gitconnected.com/implementing-recursion-with-the-y-combinator-in-any-language-9e83fa369ca
    # this has the answer in the 1st comment:
    # https://www.youtube.com/watch?v=9T8A89jgeTI
    f = Symbol()
    x = Symbol()
    xa, x_ = dup(x)
    xb, xc = dup(x_)
    fac = Lam(f, Lam(x, Ite(xa, Mul(xb, App(f, Add(xc, Int(-1)))), Int(1))))

    e = App(App(y, fac), Int(3))
    e = Evaluator().eval(e)
    print()

def infinite_recursion_test():
    x1 = Symbol()
    x1a, x1b = dup(x1)
    x2 = Symbol()
    x2a, x2b = dup(x2)
    e = App(Lam(x1, App(x1a, x1b)), Lam(x2, App(x2a, x2b)))
    e = Evaluator().eval(e)
    print()


# simple_test_evaluator()
# medium_test_evaluator()
# complex_test_evaluator()
# trick_test_evaluator()
# my_test_evaluator()
# test_k_combinator()
# test_dups_different()

# use_y_combinator()
factorial()
# infinite_recursion_test()

print("done")
