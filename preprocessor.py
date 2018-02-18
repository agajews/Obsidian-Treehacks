import re
import tatsu
from tatsu.model import ModelBuilderSemantics

comment = r'#.*\n'
open_comment = r'#\['
close_comment = r'\]#'

surround_grammar = '''
@@grammar :: Surround

start = @:{surround|chunk} $ ;

chunk::str = /[^(){}\[\]]+/ ;

surround::Surround = left:'(' contents:{surround|chunk} right:')'
                   | left:'[' contents:{surround|chunk} right:']'
                   | left:'{' contents:{surround|chunk} right:'}'
                   ;
'''

class Surround:
    def __init__(self, ast):
        self.contents = ast['contents']
        self.left = ast['left']
        self.right = ast['right']

    def text(self):
        text = self.left
        for section in self.contents:
            if isinstance(section, Surround):
                text += section.text()
            else:
                text += section
        return text + self.right

surround_model = tatsu.compile(surround_grammar, semantics=ModelBuilderSemantics(types=[Surround]))


def strip_block_comments(text):
    depth = 0
    start = 0
    open_pattern = re.compile(open_comment)
    close_pattern = re.compile(close_comment)
    open_match = open_pattern.search(text)
    close_match = close_pattern.search(text)
    line_nums = list(range(len(text.split('\n'))))
    while open_match is not None or close_match is not None:
        # print('BEGIN')
        # print(text)
        # print('END')
        if open_match is not None and (close_match is None or open_match.start() < close_match.start()):
            # print('Reading open match at {}; at depth {}'.format(open_match.start(), depth))
            match = open_match
            if depth == 0:
                start = open_match.start()
            depth += 1
            open_match = open_pattern.search(text, match.end())
        else:
            # print('Reading close match at {}; at depth {}'.format(close_match.start(), depth))
            match = close_match
            if depth == 0:
                line_pos = text[:match.start()].count('\n')
                line_num = line_nums[line_pos]
                raise Exception('Too many close comments at line {}'.format(line_num + 1))
            elif depth > 1:
                close_match = close_pattern.search(text, match.end())
            else:
                end = match.end()
                num_lines = text[start:end].count('\n')
                start_pos = text[:start].count('\n') + 1
                line_nums = line_nums[:start_pos] + line_nums[start_pos + num_lines:]
                next_start = match.start()
                text = text[:start] + text[end:]
                open_match = open_pattern.search(text)
                close_match = close_pattern.search(text)
            depth -= 1
    if depth > 0:
        line_num = text[:start].count('\n')
        raise Exception('Unmatched block comment; depth at end of file {}; open comment at line {}'.format(depth, line_num + 1))
    return text, line_nums


def strip_line_comments(text):
    return re.sub(r'#[^\n]*\n', '\n', text)


def strip_inner_newlines(text, line_nums):
    ast = surround_model.parse(text, whitespace='')
    stripped = ''
    line_pos = 0
    for section in ast:
        if isinstance(section, Surround):
            section = section.text()
            line_nums = line_nums[:line_pos] + line_nums[line_pos + section.count('\n'):]
            stripped += section.replace('\n', '#[INNERNEWLINE]#')
        else:
            stripped += section
            line_pos += section.count('\n')
    return stripped, line_nums


def insert_outer_newlines(text):
    return text.replace('\n', '#[ENDL]#\n')


def find_indent_str(text, line_nums):
    for line, line_num in zip(text.split('\n'), line_nums):
        if re.search(r'^\s', line) is not None and re.fullmatch(r'\s', line[0]) is not None:

            char = line[0]
            if line[0] not in [' ', '\t']:
                raise Exception('Invalid whitespace at line {}'.format(line_num))

            indent_match = re.match(char + '+', line)
            whitespace_match = re.search(r'\s+', line)

            if not len(indent_match[0]) == len(whitespace_match[0]):
                raise Exception('Mixed indentation at line {}'.format(line_num))
            return char * len(indent_match[0])
    return None
                

def find_indents(text, indent_str, line_nums):
    lines = []
    for line, line_num in zip(text.split('\n'), line_nums):
        if re.search(r'^\s', line) is not None and re.fullmatch(r'\s', line[0]) is not None:
            whitespace_match = re.match(r'\s+', line)
            indent_match = re.fullmatch(indent_str + '+', whitespace_match[0])
            if indent_match is None:
                raise Exception('Invalid indentation at line {}'.format(line_num))
            num_indents = int(len(whitespace_match[0]) / len(indent_str))
            line = (num_indents, indent_match.end(), line)
        else:
            line = (0, 0, line)
        lines.append(line)
    return lines


def insert_dedents(lines):
    indented_lines = []
    indent_level = 0
    for num_indents, line_start, line in lines:
        if num_indents > indent_level:
            line = line[:line_start] + '#[INDENT]#' * (num_indents - indent_level) + line[line_start:]
        elif num_indents < indent_level:
            line = line[:line_start] + '#[DEDENT]#' * (indent_level - num_indents) + line[line_start:]
        indented_lines.append(line)
        indent_level = num_indents
    indented_lines[-1] += '#[DEDENT]#' * indent_level
    return '\n'.join(indented_lines)


def insert_indents(text, line_nums):
    indent_str = find_indent_str(text, line_nums)
    if indent_str is None:
        return text, ''
    lines = find_indents(text, indent_str, line_nums)
    text = insert_dedents(lines)
    return text, indent_str


def replace_newlines(text):
    return text.replace('#[INNERNEWLINE]#', '\n')


def preprocess(text):
    text, line_nums = strip_block_comments(text)
    text = strip_line_comments(text)
    text, noendl_line_nums = strip_inner_newlines(text, line_nums)
    text = insert_outer_newlines(text)
    text, indent_str = insert_indents(text, noendl_line_nums)
    text = replace_newlines(text)
    return text, line_nums, indent_str

