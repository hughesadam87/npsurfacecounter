from collections import namedtuple
from math import sqrt

class memorized_property(object):
    Record = namedtuple("Record", "key value")

    def __init__(self, func, name = None):
        self.func = func
        self. __name__ = name if name else ("_cache_" + func.__name__)

    def __get__(self, instance, klass=None):
        if instance is None:
            return self
        gen = self.func(instance)
        key = next(gen)
        record = instance.__dict__.get(self.__name__, None)
        if not(record and record.key == key):
            record = instance.__dict__[self.__name__] = self.Record(key, next(gen))
        return record.value

class X(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @memorized_property
    def c(self):
        yield (self.a, self.b)
        print("X.c computed")
        yield sqrt(self.a**2 + self.b**2)

if __name__ == "__main__":
    x=X(2, 4)
    print x.a
    print x.b
    print x.c
    print x.c
    x.a=2
    print x.c
    x.a=5
    print x.c