from tatsu.model import ModelBuilderSemantics


def conjugate_surrounder(surrounder):
    if surrounder == '(':
        return ')'
    elif surrounder == '[':
        return ']'
    elif surrounder == '{':
        return '}'


def cata(model, fn):
    if isinstance(model, list):
        return [elem.cata(fn) for elem in model]
    return model.cata(fn)


class ModelNode:
    def cata(self, fn):
        return fn(self)


class Int(ModelNode):
    def __init__(self, string):
        self.literal = string
        self.value = int(string)

    def __repr__(self):
        return 'Int({})'.format(self.value)


class Float(ModelNode):
    def __init__(self, string):
        self.literal = string
        self.value = float(string)

    def __repr__(self):
        return 'Float({})'.format(self.value)


class String(ModelNode):
    def __init__(self, string):
        self.literal = string
        self.string = string[1:-1]

    def to_literal(self):
        return '"{}"'.format(self.string)

    def __repr__(self):
        return 'String("{}")'.format(self.string)


class Symbol(ModelNode):
    def __init__(self, symbol):
        self.literal = '~{}'.format(self.symbol)
        self.symbol = symbol

    def __repr__(self):
        return 'Symbol(~{})'.format(self.symbol)


class Char(ModelNode):
    def __init__(self, char):
        self.literal = char
        self.char = char[1:-1]

    def __repr__(self):
        return "Char('{}')".format(self.char)


class Identifier(ModelNode):
    def __init__(self, name):
        self.literal = name
        self.name = name

    def __repr__(self):
        return 'Ident({})'.format(self.name)


class Op(ModelNode):
    def __init__(self, op):
        self.literal = op
        self.op = op

    def __repr__(self):
        return self.op


class TupleTarget(ModelNode):
    def __init__(self, targets):
        self.targets = targets

    def cata(self, fn):
        return fn(TupleTarget(t.cata(fn) for t in self.targets))

    def __repr__(self):
        return 'Tuple({})'.format(', '.join(str(t) for t in self.targets))


class CollectionTarget(ModelNode):
    def __init__(self, surrounder, contents):
        self.surrounder = surrounder
        self.contents = contents

    def cata(self, fn):
        return fn(CollectionTarget(self.surrounder, self.contents))

    def __repr__(self):
        return 'Collection({}{}{})'.format(self.surrounder, ' '.join(str(c) for c in self.contents), conjugate_surrounder(self.surrounder))


class UnaryExpr(ModelNode):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def cata(self, fn):
        return fn(UnaryExpr(self.op, self.expr.cata(fn)))

    def __repr__(self):
        return 'Unary({}({}))'.format(self.op, self.expr)


class TrailerExpr(ModelNode):
    def __init__(self, expr, surrounder, contents):
        self.expr = expr
        self.surrounder = surrounder
        self.contents = contents

    def cata(self, fn):
        return fn(TrailerExpr(self.expr.cata(fn), self.surrounder, self.contents))

    def __repr__(self):
        return '{}{}{}{}'.format(self.expr, self.surrounder, ' '.join(str(c) for c in self.contents),
                                 conjugate_surrounder(self.surrounder))


class EmptyStmt(ModelNode):
    def __init__(self, ast):
        pass


class Block(ModelNode):
    def __init__(self, keyword, header, body):
        self.keyword = keyword.name
        # print('Block {}'.format(self.keyword))
        # print('Header:')
        # print(header)
        self.header = ' '.join(header)
        # print('Body')
        # print(body)
        body = [' '.join(stmt) if isinstance(stmt, list) else stmt.literal for stmt in body]
        self.body = '#[ENDL]#\n'.join(body)
        self.literal = '{} {} #[ENDL]#\n#[INDENT]# {} #[ENDL]#\n#[DEDENT]#'.format(self.keyword, self.header, self.body)
        # print('Block literal')
        # print(self.literal)

    def cata(self, fn):
        return fn(Block(self.keyword, self.header, self.body))

    def __repr__(self):
        return 'Block({}, header={}, ...)'.format(self.keyword, self.header)


class Assignment(ModelNode):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def cata(self, fn):
        return fn(Assignment(self.name, self.expr.cata(fn)))

    def __repr__(self):
        return 'Assignment({} = {})'.format(self.name, self.expr)


class Tuple(ModelNode):
    def __init__(self, contents):
        self.contents = contents

    def cata(self, fn):
        return fn(Tuple(c.cata(fn) for c in self.contents))

    def __repr__(self):
        return 'Tuple({})'.format(', '.join(str(c) for c in self.contents))


class Collection(ModelNode):
    def __init__(self, surrounder, contents):
        self.surrounder = surrounder
        self.contents = contents

    def cata(self, fn):
        return fn(Collection(self.surrounder, self.contents))

    def __repr__(self):
        return 'Collection({}{}{})'.format(self.surrounder, ' '.join(str(c) for c in self.contents), conjugate_surrounder(self.surrounder))


class PartialBinaryExpr(ModelNode):
    def __init__(self, exprs):
        self.exprs = exprs

    def cata(self, fn):
        return fn(PartialBinaryExpr(e.cata(fn) if i % 2 == 0 else e for i, e in enumerate(self.exprs)))

    def __repr__(self):
        return 'PartialBinary({})'.format(' '.join(str(e) for e in self.exprs))


def unaryexpr(ast):
    if ast.subexpr is not None:
        return ast.subexpr
    return UnaryExpr(ast.op, ast.expr)


def chunk(ast):
    chunk = []
    for elem in ast:
        if isinstance(elem, list):
            chunk += elem
        else:
            chunk += [elem.left] + elem.contents + [elem.right]
    # print('Chunk')
    # print(chunk)
    return chunk


def chunkstmt(ast):
    if ast.chunk is not None:
        return ast.chunk + [ast.endl]
    return [ast.endl]


def lexeme(ast):
    if isinstance(ast, ModelNode):
        return ast.literal
    return ast


def trailerexpr(ast):
    expr = ast.name
    for trailer in ast.trailers:
        expr = TrailerExpr(expr, trailer.surrounder, trailer.contents)
    return expr


def surrounded(ast):
    return [ast.surrounder] + ast.contents + [conjugate_surrounder(ast.surrounder)]


def stmtlist(ast):
    return [stmt for stmt in ast if not isinstance(stmt, EmptyStmt)]


def binaryexpr(ast):
    if len(ast) == 1:
        return ast[0]
    return PartialBinaryExpr(ast)


def block(ast):
    return Block(ast.keyword, ast.header, ast.body)


def assignment(ast):
    return Assignment(ast.target, ast.expr)


def tuple_sem(ast):
    return Tuple([] if ast.contents is None else [ast.first] + ast.contents)


def parenstarget(ast):
    return TupleTarget([ast.first] + ast.contents)


def tupletarget(ast):
    if len(ast) == 1:
        return ast[0]
    return TupleTarget(ast)


def collectiontarget(ast):
    return CollectionTarget(ast.surrounder, ast.contents)

def collection(ast):
    return Collection(ast.surrounder, ast.contents)


class Semantics(ModelBuilderSemantics):
    def __init__(self):
        super().__init__(types=[
            Int, String, Char, Op,
            Identifier,
            EmptyStmt,
        ])

    def unaryexpr(self, ast):
        if ast.subexpr is not None:
            return ast.subexpr
        return UnaryExpr(ast.op, ast.expr)

    def chunk(self, ast):
        chunk = []
        for elem in ast:
            if isinstance(elem, list):
                chunk += elem
            else:
                chunk += [elem.left] + elem.contents + [elem.right]
        return chunk

    def trailerexpr(self, ast):
        expr = ast.name
        for trailer in ast.trailers:
            expr = TrailerExpr(expr, trailer.surrounder, trailer.contents)
        return expr

    def stmtlist(self, ast):
        return [stmt for stmt in ast if not isinstance(stmt, EmptyStmt)]

    def binaryexpr(self, ast):
        if len(ast) == 1:
            return ast[0]
        return PartialBinaryExpr(ast)

    def block(self, ast):
        return Block(ast.keyword, ast.header, ast.body)

    def assignment(self, ast):
        return Assignment(ast.target, ast.expr)

    def tuple(self, ast):
        return Tuple([] if ast.contents is None else [ast.first] + ast.contents)

    def parenstarget(self, ast):
        return TupleTarget([ast.first] + ast.contents)

    def tupletarget(self, ast):
        if len(ast) == 1:
            return ast[0]
        return TupleTarget(ast)

    def collectiontarget(self, ast):
        return CollectionTarget(ast.surrounder, ast.contents)

    def collection(self, ast):
        return Collection(ast.surrounder, ast.contents)
