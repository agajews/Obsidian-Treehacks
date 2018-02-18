import tatsu
from argparse import ArgumentParser
from preprocessor import preprocess
from grammar.core import core_grammar
from grammar.fun import process_fun, parse_ops
from grammar.model import PartialBinaryExpr, Block, cata
from grammar.context import Context
from grammar.operators import OperatorGrammar


core_parser = core_grammar.compile()

op_grammar = OperatorGrammar()

op_grammar.add_op('^', 'right', 8)

op_grammar.add_op('*', 'left', 7)
op_grammar.add_op('/', 'left', 7)

op_grammar.add_op('+', 'left', 6)
op_grammar.add_op('-', 'left', 6)

op_grammar.add_op('==', 'chain', 4)
op_grammar.add_op('!=', 'chain', 4)

op_grammar.add_op('<', 'chain', 4)
op_grammar.add_op('>', 'chain', 4)

op_grammar.add_op('<=', 'chain', 4)
op_grammar.add_op('>=', 'chain', 4)

op_grammar.add_op('&&', 'right', 3)
op_grammar.add_op('||', 'right', 3)

op_parser = op_grammar.compile()

class Keyword:
    def __init__(self, header_parser, body_parser, process_fn):
        self.header_parser = header_parser
        self.body_parser = body_parser
        self.process_fn = process_fn

keywords = {'fun': process_fun}

def interpret(text):
    text, line_nums, indent_str = preprocess(text)
    program = core_parser.parse(text, trace=False)
    context = Context(op_parser, keywords)
    for stmt in program:
        if isinstance(stmt, Block):
            context.keywords[stmt.keyword](stmt.header, stmt.body, context, context)
        else:
            print(cata(stmt, lambda ast: parse_ops(ast, context)))


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument('fnm', help='filename to compile')
    args = argparser.parse_args()

    with open(args.fnm, 'r') as f:
        interpret(f.read())
