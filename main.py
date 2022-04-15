class Ast:
    def reduce(self):
        raise NotImplementedError()
    def dup(self):
        raise NotImplementedError()

class Symbol:
    # this is a shell to be used once or not at all
    def __init__(self, name: str=''):
        self.name = name
        self.state = 0 # 0 means new, 1 means bound, 2 means used up
        self.binding = None
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
    def reduce(self):
        assert self.state == 1
        self.state = 2
        return self.binding

class Dup:
    def __init__(self, child):
        self.child = child
    def __str__(self):
        return "<Dup {}>".format(str(self.child))

class Sup:
    def __init__(self, a, b):
        self.a = a
        self.b = b

class Lam:
    def __init__(self, param: Symbol, body):
        self.param = param
        self.body = body
    def __str__(self):
        return "<Lam {} {}>".format(str(self.param), str(self.body))
    def reduce(self):
        self.body = self.body.reduce()
        return self

class App:
    def __init__(self, lam: Lam, arg):
        self.lam = lam
        self.arg = arg
    def __str__(self):
        return "<App {} {}>".format(str(self.lam), str(self.arg))
    def reduce(self):
        # replace instance with parameter
        # Note that the arg must be used 0 or 1 time(s)
        self.lam.param.bind(self.arg)
        self.lam = self.lam.reduce()
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

simple_test()
# complex_test()

print("done")
