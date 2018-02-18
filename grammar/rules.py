class Rule:
    def subrules(self):
        return []


class Name(Rule):
    def __init__(self, name):
        self.name = name

    def subrules(self):
        return [self.name]

    def ebnf(self):
        return self.name


class Regex(Rule):
    def __init__(self, regex):
        self.regex = regex

    def ebnf(self):
        return '/{}/'.format(self.regex.replace('/', '\/'))


class Literal(Rule):
    def __init__(self, literal):
        self.literal = literal

    def ebnf(self):
        return "'{}'".format(self.literal.replace("'", r"\'"))


class Cut(Rule):
    def ebnf(self):
        return '~'


class EOF(Rule):
    def ebnf(self):
        return '$'


class Closure(Rule):
    def __init__(self, rule):
        self.rule = rule

    def subrules(self):
        return self.rule.subrules()

    def ebnf(self):
        return '{{{}}}'.format(self.rule.ebnf())


class PosClosure(Rule):
    def __init__(self, rule):
        self.rule = rule

    def subrules(self):
        return self.rule.subrules()

    def ebnf(self):
        return '{{{}}}+'.format(self.rule.ebnf())


class Join(Rule):
    def __init__(self, sep, rule):
        self.sep = sep
        self.rule = rule

    def subrules(self):
        return self.sep.subrules() + self.rule.subrules()

    def ebnf(self):
        return '({})%{{{}}}'.format(self.sep.ebnf(), self.rule.ebnf())


class PosJoin(Rule):
    def __init__(self, sep, rule):
        self.sep = sep
        self.rule = rule

    def subrules(self):
        return self.sep.subrules() + self.rule.subrules()

    def ebnf(self):
        return '({})%{{{}}}+'.format(self.sep.ebnf(), self.rule.ebnf())


class LeftJoin(Rule):
    def __init__(self, sep, rule):
        self.sep = sep
        self.rule = rule

    def subrules(self):
        return self.sep.subrules() + self.rule.subrules()

    def ebnf(self):
        return '({})<{{{}}}+'.format(self.sep.ebnf(), self.rule.ebnf())


class RightJoin(Rule):
    def __init__(self, sep, rule):
        self.sep = sep
        self.rule = rule

    def subrules(self):
        return self.sep.subrules() + self.rule.subrules()

    def ebnf(self):
        return '({})>{{{}}}+'.format(self.sep.ebnf(), self.rule.ebnf())


class Gather(Rule):
    def __init__(self, sep, rule):
        self.sep = sep
        self.rule = rule

    def subrules(self):
        return self.sep.subrules() + self.rule.subrules()

    def ebnf(self):
        return '({}).{{{}}}'.format(self.sep.ebnf(), self.rule.ebnf())


class PosGather(Rule):
    def __init__(self, sep, rule):
        self.sep = sep
        self.rule = rule

    def subrules(self):
        return self.sep.subrules() + self.rule.subrules()

    def ebnf(self):
        return '({}).{{{}}}+'.format(self.sep.ebnf(), self.rule.ebnf())


class Lookahead(Rule):
    def __init__(self, rule):
        self.rule = rule

    def subrules(self):
        return self.rule.subrules()

    def ebnf(self):
        return '&{}'.format(self.rule.ebnf())


class Optional(Rule):
    def __init__(self, rule):
        self.rule = rule

    def subrules(self):
        return self.rule.subrules()

    def ebnf(self):
        return '[{}]'.format(self.rule.ebnf())


class Or(Rule):
    def __init__(self, *rules):
        self.rules = rules

    def subrules(self):
        return [subrule for rule in self.rules for subrule in rule.subrules()]

    def ebnf(self):
        return ' | '.join(r.ebnf() for r in self.rules)


class And(Rule):
    def __init__(self, *rules):
        self.rules = rules

    def subrules(self):
        return [subrule for rule in self.rules for subrule in rule.subrules()]

    def ebnf(self):
        return ' '.join(r.ebnf() for r in self.rules)
