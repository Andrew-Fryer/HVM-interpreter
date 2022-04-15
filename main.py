class Ast:
    def reduce(self):
        raise NotImplementedError()
    def dup(self):
        raise NotImplementedError()

class Dup:
    def __init__(self, child):
        self.child = child
    def __str__(self):
        return "<Dup {}>".format(str(self.child))

class Lam:
    def __init__(self, param: Var, body):
        self.param = param
        self.body = body
    def __str__(self):
        return "<Lam {} {}>".format(str(self.param), str(self.body))

# I think we want a different class for parameter and for instance...
class Var:
    def __init__(self, name: str):
        self.name = name
        self.binding = None
    def __str__(self):
        return self.name
    def bind(self, value):
        self.binding = value
    # def reduce(self) # does this ever get called?
    def dup(self):
        return Var(self.name + '_0'), Var(self.name + '_1')

class App:
    def __init__(self, lam: Lam, arg):
        self.lam = lam
        self.arg = arg
    def __str__(self):
        return "<App {} {}>".format(str(self.lam), str(self.arg))
    def reduce(self):
        # replace instance with parameter
        # Note that the arg must be used 0 or 1 time(s)
        self.lam.param.bind(arg)
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
        pass
    def dup(self):
        return self, self # okay because Int is immutable

x = Var("x")
f = Lam(x, x)
f_dup = Dup(f)
x1 = Var("x1")
f1 = Lam(x1, App(f_dup, App(f_dup, x1)))
f1_dup = Dup(f1)
e = App(f1_dup, App(f1_dup, Int(0)))

print(e)

print("done")
