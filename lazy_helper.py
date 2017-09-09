import sys
import marshal

# global dict holding marshal data, keyed by func name
LAZY_DATA = '__lazy_data'

def set_class(name):
    # Give the module 'name' the __getattr__ hook needed to load
    # functions as they are accessed.
    #print(f'lazy setup {name}')
    mod = sys.modules[name]
    class Lazy(type(sys)):
        def __getattr__(self, func):
            #print(f'wake func {func}')
            data = self.__dict__[LAZY_DATA].get(func)
            if data is not None:
                code = marshal.loads(data)
                exec(code, vars(self))
                return self.__dict__[func]
            raise AttributeError()
    sys.modules[name].__class__ = Lazy
