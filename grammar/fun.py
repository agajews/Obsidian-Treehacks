from .core import core_grammar, wrap
from .rules import *
from .grammar import Grammar
from .context import Context
from .model import Block, PartialBinaryExpr, cata


body_grammar = Grammar()
body_grammar.add_rule('start', [Name('stmtlist'), EOF()])
body_grammar.add_rules(core_grammar.slice_rule('stmtlist'))

body_parser = body_grammar.compile()

header_grammar = Grammar()
header_grammar.add_rules(core_grammar.slice_rule('identifier'))
header_grammar.add_rule('start', [Name('signature'), EOF()])
header_grammar.add_rule('signature', [('name', Name('identifier')), ('params', Name('params'))])
header_grammar.add_rule('params', wrap('(', [Gather(Literal(','), Name('identifier'))], ')'))

header_parser = header_grammar.compile()


def parse_ops(ast, context):
    if isinstance(ast, PartialBinaryExpr):
        return context.op_parser.parse(ast.exprs)
    return ast


def process_fun(header, body, ext_context, global_context):
    header = header_parser.parse(header)
    body = body_parser.parse(body, trace=False)

    name = header.name

    context = Context(ext_context.op_parser, ext_context.keywords)
    
    print('FUNCTION {}'.format(name))
    for stmt in body:
        if isinstance(stmt, Block):
            context.keywords[stmt.keyword](stmt.header, stmt.body, context, global_context)
        else:
            print(cata(stmt, lambda ast: parse_ops(ast, context)))
    print('END FUNCTION {}'.format(name))
