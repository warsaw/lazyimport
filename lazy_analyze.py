import sys
import ast
import importlib.util


def safe_assign(value):
    safe = {ast.Num, ast.NameConstant, ast.Str}
    return type(value) in safe


class Transformer:
    def __init__(self, fn):
        self.is_lazy = True
        self.force_lazy = False
        self.lazy_funcs = 0
        self.lazy_classes = 0
        self.imports = []
        self.fn = fn

    def eager(self, stmt):
        self.is_lazy = False
        print(f'{self.fn}:{stmt.lineno}: non-lazy {stmt.__class__.__name__}')

    def analyze(self, node):
        for stmt in node.body:
            if isinstance(stmt, ast.ImportFrom):
                self.imports.append(stmt.module)
            elif isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    self.imports.append(alias.name)
            elif isinstance(stmt, ast.Assign):
                targets = stmt.targets
                if len(targets) == 1:
                    target = targets[0]
                    if (isinstance(target, ast.Assign) and
                            target.id == '__lazy__'):
                        self.force_lazy = True
                    else:
                        self.eager(stmt)
                        return
                else:
                    if not safe_assign(stmt.value):
                        print('assign', stmt.value)
                        self.is_lazy = False
            elif isinstance(stmt, ast.FunctionDef):
                self.lazy_funcs += 1
            elif isinstance(stmt, ast.ClassDef):
                self.lazy_classes += 1
            elif isinstance(stmt, ast.Expr):
                # Docstrings.
                if isinstance(stmt.value, ast.Str):
                    pass
                else:
                    self.eager(stmt)
                    return
            else:
                self.eager(stmt)
                return
        return


def parse(buf, filename='<string>'):
    if isinstance(buf, bytes):
        buf = importlib.util.decode_source(buf)
    try:
        node = ast.parse(buf, filename)
    except SyntaxError as e:
        # set the filename attribute
        raise SyntaxError(str(e), (filename, e.lineno, e.offset, e.text))
    return node


def analyze(node, fn):
    t = Transformer(fn)
    t.analyze(node)
    return t


def main():
    total = lazy = eager = 0
    for fn in sys.argv[1:]:
        if 'test_' in fn:
            continue
        with open(fn) as fp:
            total += 1
            try:
                buf = fp.read()
            except UnicodeDecodeError:
                continue
            try:
                node = parse(buf)
            except SyntaxError:
                continue
            a = analyze(node, fn)
            if a.is_lazy:
                lazy += 1
                ## print('%s lazy = %s, funcs = %d classes = %d' % (
                ##     fn, a.is_lazy, a.lazy_funcs, a.lazy_classes))
                ## for name in a.imports:
                ##     print('  import', name)
            else:
                eager += 1
    print(f'{lazy / total * 100:.1f}% - total: {total}')


if __name__ == '__main__':
    main()
