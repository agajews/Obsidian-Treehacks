import tatsu
from tatsu.model import ModelBuilderSemantics


def parse_ops(ast, context):
    op_parser = context.op_grammar.compile()
    if isinstance(ast, PartialBinaryExpr):
        return op_parser.parse(ast.exprs)
    return ast



class Operator:
    def __init__(self, op, associativity='left', precedence=5):
        self.op = op
        self.associativity = associativity
        self.precedence = precedence


class BinaryExpr:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return 'Binary({} {} {})'.format(self.left, self.op, self.right)


class ChainExpr:
    def __init__(self, elems):
        self.elems = elems

    def __repr__(self):
        return 'Chain({})'.format(' '.join(str(e) for e in self.elems))


class OperatorGrammar:
    def __init__(self):
        self.operators = {}

    def add_op(self, op, associativity, precedence):
        if precedence not in self.operators:
            self.operators[precedence] = {'left': [], 'right': [], 'chain': []}
        assert associativity in ['left', 'right', 'chain']
        self.operators[precedence][associativity].append(op)

    def gen_grammar(self):
        operators = [self.operators[precedence] for precedence in sorted(self.operators.keys())]
        # print(operators)
        grammar = [
            '@@grammar :: Operator',
            'start = expr $ ;',
            'atom = /[0-9]+/ ;',
            'opexpr{} = atom ;'.format(len(operators)),
        ]
        for precedence, ops in reversed(list(enumerate(operators))):
            lops = ops['left']
            rops = ops['right']
            cops = ops['chain']
            op_expr = []
            if len(lops) > 0:
                grammar.append('lop{} = {} ;'.format(precedence, ' | '.join("'{}'".format(l) for l in lops)))
                op_expr.append('(lop{})<{{opexpr{}}}+'.format(precedence, precedence + 1))
            if len(rops) > 0:
                grammar.append('rop{} = {} ;'.format(precedence, ' | '.join("'{}'".format(r) for r in rops)))
                op_expr.append('(rop{})>{{opexpr{}}}+'.format(precedence, precedence + 1))
            if len(cops) > 0:
                grammar.append('cop{} = {} ;'.format(precedence, ' | '.join("'{}'".format(c) for c in cops)))
                op_expr.append('(cop{})%{{opexpr{}}}+'.format(precedence, precedence + 1))
            grammar.append('opexpr{} = {} | opexpr{} ;'.format(precedence, ' | '.join(op_expr), precedence + 1))
        grammar.append('expr = opexpr0 ;')
        # print('\n'.join(grammar))
        return '\n'.join(grammar)

    def compile(self):
        return OperatorParser(tatsu.compile(self.gen_grammar()))


def simplify_expr(ast):
    # print(ast)
    if isinstance(ast, tuple):
        op, left, right = ast
        return BinaryExpr(op, simplify_expr(left), simplify_expr(right))
    elif isinstance(ast, list):
        if len(ast) == 1:
            return simplify_expr(ast[0])
        return ChainExpr(ast)
    return ast


class OperatorParser:
    def __init__(self, parser):
        self.parser = parser

    def parse(self, elems):
        elems = list(elems)
        is_op = False
        text = list(elems)
        exprs = []
        for i in range(len(text)):
            if i % 2 == 0:
                text[i] = '{}'.format(int(i / 2))
                exprs.append(elems[i])
            else:
                text[i] = text[i].op

        class Semantics(ModelBuilderSemantics):
            def atom(self, idx):
                return exprs[int(idx)]

            def expr(self, ast):
                return simplify_expr(ast)

        text = ' '.join(text)
        # print(text)
        # print('Exprs:')
        # print(exprs)
        return self.parser.parse(text, semantics=Semantics())
        
