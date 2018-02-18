import tatsu
from tatsu.model import ModelBuilderSemantics
from .rules import Name

ident = lambda x: x

class Grammar:
    def __init__(self, rules=None):
        self.rules = {} if rules is None else rules

    def add_rule(self, name, *rules, semantics=ident):
        # print('Adding rules:')
        # print(rules)
        rules = list(rules)
        for i, rule in enumerate(rules):
            if not isinstance(rule, list):
                rule = [rule]
            for j, subrule in enumerate(rule):
                if not isinstance(subrule, tuple):
                    subrule = (None, subrule)
                # name, sub = subrule
                # if isinstance(sub, str):
                #     subrule = (name, Name(sub))
                rule[j] = subrule
            rules[i] = rule
        # print(rules)
        # print('Adding rule to grammar {}'.format(name))
        self.rules[name] = (rules, semantics)

    def add_rules(self, rules):
        self.rules.update(rules)

    def gen_grammar(self):
        grammar = ['@@grammar :: Grammar']
        # print('All rules:')
        # print(self.rules)
        for name, (rule, semantics) in self.rules.items():
            # print('Rule:')
            # print(rule)
            and_rules = []
            for and_rule in rule:
                new_and_rule = []
                # print('And rule:')
                # print(and_rule)
                for (label, sub) in and_rule:
                    if label is not None:
                        new_and_rule.append('{}:{}'.format(label, sub.ebnf()))
                    else:
                        new_and_rule.append(sub.ebnf())
                and_rules.append(new_and_rule)

            rule = ' | '.join(' '.join(and_rule) for and_rule in and_rules)
            # rule = ' | '.join(' '.join(
            #     ('{}:{}'.format(name, sub) if name is not None else sub)
            #     for (name, sub) in subrule)
            #     for subrule in rule)
            # print('Adding rule {}'.format(name))
            grammar.append('{} = {} ;'.format(name, rule))
        return '\n'.join(grammar)

    def semantics(self):
        return {name: semantics for name, (rule, semantics) in self.rules.items()}

    def compile(self):
        grammar = self.gen_grammar()
        # print(grammar)
        return Parser(tatsu.compile(grammar), self.semantics())

    def slice_rule(self, name):
        # print('Slicing rules')
        subrules = set()
        new_subrules = {name}
        # print(self.rules[name])
        while len(new_subrules) > 0:
            curr_name = new_subrules.pop()
            subrules.add(curr_name)
            (subrule, semantics) = self.rules[curr_name]
            # print(subrule)
            for (_, rule) in [s for sub in subrule for s in sub]:
                for subrule_name in rule.subrules():
                    if not subrule_name in subrules:
                        new_subrules.add(subrule_name)
        return {subrule: self.rules[subrule] for subrule in subrules}

    def __getitem__(self, name):
        return Grammar(self.slice_rule(name))

class Parser:
    def __init__(self, parser, semantics):
        self.parser = parser

        class Semantics(ModelBuilderSemantics):
            pass
            # def _default(self, ast):
            #     return semantics[ast.parseinfo.rule](ast)
        self.semantics = Semantics()
        for name, fn in semantics.items():
            # def wrapper(this, *ast):
            #     return fn(*ast)
            setattr(self.semantics, name, fn)

    def parse(self, *args, **kwargs):
        return self.parser.parse(*args, semantics=self.semantics, **kwargs)
