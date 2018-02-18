from .rules import *
from .grammar import Grammar
from .model import *

def wrap(left, rest, right, label=None):
    return [(label, Literal(left))] + rest + [Literal(right)]

core_grammar = Grammar()

core_grammar.add_rule('start', [Name('program'), EOF()])
core_grammar.add_rule('program', [Name('stmtlist'), EOF()])

for flag in ['indent', 'dedent', 'endl']:
    core_grammar.add_rule(flag, Literal('#[{}]#'.format(flag.upper())))

simple_atoms = [
    ('identifier', Regex('[_a-zA-Z][_a-zA-Z0-9]*[?!]?'), Identifier),
    ('int', Regex('[0-9]+'), Int),
    ('float', Regex('([0-9]+)|([0-9]+\.[0-9]*)|(\.[0-9]+)'), Float),
    ('char', Regex(r"'([^'\\]|\\.)'"), Char),
    ('string', Regex(r'"([^"\\]|\\.)*"'), String),
]

for name, regex, semantics in simple_atoms:
    core_grammar.add_rule(name, regex, semantics=semantics)

core_grammar.add_rule('symbol', [Literal('~'), ('@', Regex('[a-zA-Z][a-zA-Z0-9]*[?!]?'))],
                      semantics=Symbol)

atoms = [Name(name) for name in [
    'identifier',
    'int',
    'float',
    'char',
    'string',
    'symbol',
]]
core_grammar.add_rule('atom', *atoms)

trailers = [wrap(left, [Cut(), ('contents', Name('chunk'))], right, label='surrounder')
            for left, right in [('(', ')'), ('[', ']'), ('{', '}')]]
core_grammar.add_rule('trailer', *trailers)

core_grammar.add_rule(
    'trailerexpr', [('name', Name('identifier')), ('trailers', PosClosure(Name('trailer')))],
    semantics=trailerexpr)

core_grammar.add_rule('tuple',
    wrap('(', [], ')'),
    wrap('(', [Cut(), ('first', Name('expr')), Literal(','),
               ('contents', Gather(Literal(','), Name('expr')))], ')'),
    semantics=tuple_sem,
)

collections = []
for left, right in [('[', ']'), ('{', '}')]:
    collections.append(wrap(left, [Cut(), ('contents', Name('chunk'))], right, label='surrounder'))
core_grammar.add_rule('collection', *collections, semantics=collection)

core_grammar.add_rule('op', Regex('[-@$%^&*+~<>/:][-@$%^&*+<>/=:]*'), semantics=Op)

core_grammar.add_rule('atomexpr',
    Name('trailerexpr'),
    Name('atom'),
    wrap('(', [('@', Name('expr'))], ')')
)

core_grammar.add_rule('unaryexpr', [('op', Or(Literal('!'), Literal('-')))],
                      ('subexpr', Name('atomexpr')), semantics=unaryexpr)
core_grammar.add_rule('binaryexpr', PosJoin(Name('op'), Name('unaryexpr')), semantics=binaryexpr)
core_grammar.add_rule('expr', Name('binaryexpr'))

# surrounders = [Literal(s) for s in ['(', ')', '[', ']', '{', '}', '"', "'"]]
# core_grammar.add_rule('surrounder', *surrounders)
core_grammar.add_rule('separator', Literal(',',), Literal(';'))

core_grammar.add_rule('lexeme', Name('atom'), Name('op'), Name('separator'), semantics=lexeme)
core_grammar.add_rule('bundle', PosClosure(Name('lexeme')))
core_grammar.add_rule('chunk', PosClosure(Or(Name('surrounded'), Name('bundle'))), semantics=chunk)

surroundeds = []
for left, right in [('(', ')'), ('[', ']'), ('{', '}')]:
    surroundeds.append(wrap(left, [('contents', Name('chunk'))], right, label='surrounder'))
core_grammar.add_rule('surrounded', *surroundeds, semantics=surrounded)

core_grammar.add_rule('chunkstmt', [('chunk', Optional(Name('chunk'))), ('endl', Name('endl'))], semantics=chunkstmt)
core_grammar.add_rule('block', [
    ('keyword', Name('identifier')),
    ('header', Optional(Name('chunk'))),
    Name('endl'), Name('indent'), Cut(),
    ('body', PosClosure(Or(Name('block'), Name('chunkstmt')))),
    Name('dedent'),
], semantics=block)

core_grammar.add_rule('target',
    Name('parenstarget'),
    Name('tupletarget'),
    Name('collectiontarget'))

core_grammar.add_rule('parenstarget', wrap('(', [
    Cut(),
    ('first', Or(Name('parenstarget'), Name('identifier'))),
    Literal(','),
    ('contents', Gather(Literal(','), Or(Name('parenstarget'), Name('identifier')))),
],')'), semantics=parenstarget)

core_grammar.add_rule('tupletarget',
    PosGather(Literal(','), Or(Name('parenstarget'), Name('identifier'))),
    semantics=tupletarget)

core_grammar.add_rule('collectiontarget', Name('collection'), semantics=collectiontarget)

core_grammar.add_rule('assignment', [
    ('target', Name('target')),
    Literal('='), Cut(),
    ('expr', Name('expr')),
    Name('endl'),
], semantics=assignment)

core_grammar.add_rule('emptystmt', Name('endl'), [Literal('pass'), Cut(), Name('endl')],
                      semantics=EmptyStmt)
core_grammar.add_rule('stmt',
    Name('block'),
    Name('assignment'),
    Name('emptystmt'),
    [('@', Name('expr')), Name('endl')])

core_grammar.add_rule('stmtlist', Closure(Name('stmt')), semantics=stmtlist)
