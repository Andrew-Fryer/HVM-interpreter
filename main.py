class Ast:
    def reduce(self):
        raise NotImplementedError()
    def dup(self):
        raise NotImplementedError()

# lambdas don't have scopes
class Symbol:
    # this is a shell to be used once or not at all
    def __init__(self, name: str='', trigger=None):
        self.name = name
        self.state = 0 # 0 means new, 1 means bound, 2 means used up
        self.binding = None
        self.trigger = trigger
    def __str__(self):
        if self.state == 0:
            return self.name
        if self.state == 1:
            return self.binding
        assert False # should not be holing on to Symbols that are used up
    def bind(self, value):
        assert self.state == 0
        self.binding = value
        self.state = 1
    def get(self):
        # normal order reduction behaves lazily, but I had to add this hack to allow symbols of dups to trigger the dup to do the duplication
        if self.state == 0 and self.trigger != None:
            self.trigger()
        assert self.state == 1
        self.state = 2
        return self.binding

class Dup:
    def __init__(self, child):
        self.child = child
        self.a = Symbol(trigger=lambda: self.execute())
        self.b = Symbol(trigger=lambda: self.execute())
    def syms(self):
        return self.a, self.b
    def __str__(self):
        return "<Dup {}>".format(str(self.child))
    def execute(self):
        a, b = self.child.dup()
        self.a.bind(a)
        self.b.bind(b)
        # ...and this dup node is used up now

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
        if isinstance(self.body, Symbol):
            self.body = self.body.get()
        self.body = self.body.reduce()
        return self
    def dup(self):
        xa = Symbol()
        xb = Symbol()
        self.param.bind(Sup(xa, xb))
        if isinstance(self.body, Symbol):
            self.body = self.body.get()
        a, b = self.body.dup()
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
        if isinstance(self.lam, Symbol):
            self.lam = self.lam.get()
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

def medium_test():
    x = Symbol("x")
    f = Lam(x, x)
    fa, fb = Dup(f).syms()
    e = App(fa, App(fb, Int(0)))
    print(e)
    e = e.reduce()
    print(e)
    print()

def complex_test():
    x = Symbol("x")
    f = Lam(x, x)
    f_dup = Dup(f)
    x1 = Symbol("x1")
    f1 = Lam(x1, App(f_dup, App(f_dup, x1)))
    f1_dup = Dup(f1)
    e = App(f1_dup, App(f1_dup, Int(0)))
    print(e)
    e = e.reduce()
    print(e)
    print()

# simple_test()
medium_test()
# complex_test()

print("done")
