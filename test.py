import tatsu

test_grammar = '''
@@grammar :: Grammar
start = '#' $ ;
'''
# tatsu.parse(test_grammar, '#', trace=True)
test_parser = tatsu.compile(test_grammar)
print(test_parser.__dict__)
print(type(test_parser))
test_parser.parse('#', trace=True, whitespace='\s')

# from test_parser import GrammarParser
# parser = GrammarParser()
# parser.parse('#', trace=True)
