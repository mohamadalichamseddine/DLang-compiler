from sly.src.sly.lex import Lexer
import os

class DLangLexer(Lexer):

    #############################################
    ####      Define set of token names      ####
    #############################################

    tokens = {
        # Identifiers / literals
        'ID', 'INT_CONST', 'DOUBLE_CONST', 'STRING_CONST', 'BOOL_CONST',

        # Reserved Keywords
        'NOTHING', 'INT', 'DOUBLE', 'BOOL', 'STRING', 'CLASS', 'INTERFACE',
        'NULL', 'THIS', 'EXTENDS', 'IMPLEMENTS', 'FOR', 'WHILE', 'IF', 'ELSE',
        'RETURN', 'BREAK', 'NEW',
        'ARRAYINSTANCE', 'OUTPUT', 'INPUTINT', 'INPUTLINE',

        # Operators and Punctuation
        # Operators:
        'LE', 'GE', 'EQ', 'NE', 'AND', 'OR',
        'LT', 'GT', 'ASSIGN', 'NOT',
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
        
        # Punctuation:
        'SEMICOL', 'COMMA', 'DOT',
        'LBRACK', 'RBRACK', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    }


    #############################################
    ####        Match Actions - Errors       ####
    #############################################

    # Invalid identifier: starts with a digit, then has chars
    # Examples: 1abc, 123_name, 9A
    @_(r'\d+[A-Za-z_][A-Za-z0-9_]*')
    def bad_identifier(self, token):
        self._print_error(f"Invalid identifier {token.value!r}: identifiers cannot start with a digit",
            token)  # skip token (no return)


    #############################################
    ####     Ignored Lexemes and comments    ####
    #############################################
    # We ignore:
    #   - whitespace characters
    #   - tabs
    #   - carriage returns
    #   - newlines
    #   - comments (single-line and block)

    ignore = ' \t\r'  # spaces, tabs, carriage returns ignored

    @_(r'\n+')
    def ignore_newline(self, token):
        self.lineno += token.value.count('\n')

    # Single-line comment ( // to end of line):
    # [^\n] = matches all characters except new line
    ignore_singleline_comment = r'//[^\n]*'

    # Block comment (/* ... */):
    # [\s\S] = any character including newlines. We can use a dot (.) but it might not include the new line.
    # *? = non-greedy match (as few as possible, to stop at the first occurrence of */)
    @_(r'/\*[\s\S]*?\*/')
    def ignore_block_comment(self, token):
        self.lineno += token.value.count('\n')

    # Unterminated block comment: starts with /* but never closes with */
    @_(r'/\*[\s\S]*$')
    # [\s\S] = match any character including newlines.
    # $ = end of input (end of file in this case)
    def bad_block_comment(self, token):
        self._print_error("Unterminated block comment", token)
        self.lineno += token.value.count('\n')


    #############################################
    #### Regular expression rules for tokens ####
    #############################################

    ID = r'[A-Za-z_][A-Za-z0-9_]*'
    DOUBLE_CONST = r'\d+\.\d*(?:E[+-]?\d+)?'
    INT_CONST = r'\d+'
    STRING_CONST = r'"[^"\n]*"'

    # Operators and punctuation
    LE = r'<='
    GE = r'>='
    EQ = r'=='
    NE = r'!='
    AND = r'&&'
    OR = r'\|\|'
    LT = r'<'
    GT = r'>'
    ASSIGN = r'='
    NOT = r'!'
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    MOD = r'%'
    SEMICOL = r';'
    COMMA = r','
    DOT = r'\.'
    LBRACK = r'\['
    RBRACK = r'\]'
    LPAREN = r'\('
    RPAREN = r'\)'
    LBRACE = r'\{'
    RBRACE = r'\}'

    # Map reserved keywords to their token types
    ID['nothing']       = NOTHING
    ID['int']           = INT
    ID['double']        = DOUBLE
    ID['bool']          = BOOL
    ID['string']        = STRING
    ID['class']         = CLASS
    ID['interface']     = INTERFACE
    ID['null']          = NULL
    ID['this']          = THIS
    ID['extends']       = EXTENDS
    ID['implements']    = IMPLEMENTS
    ID['for']           = FOR
    ID['while']         = WHILE
    ID['if']            = IF
    ID['else']          = ELSE
    ID['return']        = RETURN
    ID['break']         = BREAK
    ID['new']           = NEW
    ID['ArrayInstance'] = ARRAYINSTANCE
    ID['Output']        = OUTPUT
    ID['InputInt']      = INPUTINT
    ID['InputLine']     = INPUTLINE
    ID['True']          = BOOL_CONST
    ID['False']         = BOOL_CONST


    #############################################
    ####          More Match Actions         ####
    #############################################

    # Unterminated string detection (missing closing quote on same line).
    @_(r'"[^"\n]*(\n|$)')
    # This will match strings that start with a quote but do not have a closing quote before the end of the line or input.
    # " = match a double quote character
    # [^"\n]* = match any characters except quotes or newlines
    # \n|$ = match either a newline OR end of input
    def bad_string(self, token):
        # Report and recover by skipping it.
        self._print_error("Unterminated string literal", token)
        if token.value.endswith('\n'):
            self.lineno += 1

    def INT_CONST(self, token):
        token.value = int(token.value)
        return token

    def DOUBLE_CONST(self, token):
        token.value = float(token.value)
        return token
    
    def STRING_CONST(self, token):
        token.value = token.value[1:-1]
        return token
    
    def ID(self, token):
        # Enforcing max length for real identifiers
        if token.type == 'ID' and len(token.value) > 50:
            self._print_error(f"Identifier too long (>50): {token.value!r}", token)
            return None  # skip this token and continue lexing
        return token


    #############################################
    ####           Error Handling            ####
    #############################################

    # This error method is called when no token rule matches at the current position
    def error(self, token):
        # Handle the error: report it (with a print), skip the character, and continue lexing
        self._print_error(f"Illegal character {token.value[0]!r}", token)
        self.index += 1  # skip the characer

    def _find_column(self, index: int) -> int:
        # Return the column number (starting at 1) for a character position in the input
        last_newline_index = self.text.rfind('\n', 0, index)
        return index - last_newline_index

    def _print_error(self, message: str, token):
        line = token.lineno
        col = self._find_column(token.index)
        print(f"[LEXICAL ERROR] - line {line}, col {col}: {message}")


#############################################
####         Interactive prompt          ####
#############################################

def run_lexer_on_file(lexer, path: str) -> bool:
    path = path.strip().strip('"')

    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}\n")
        return False

    with open(path, "r", encoding="utf-8") as f:
        program = f.read()

    print(f"---------  Generated tokens from file: {path}  ---------")
    for tok in lexer.tokenize(program):
        col = lexer._find_column(tok.index)
        print(f"{tok.type:<14} value={tok.value!r:<15} Line={tok.lineno:<3} Col={col}")
    print("--------------------------------------------------------\n")
    return True


def interactive_prompt_run():
    print(r"""
    ============================================================
        Welcome to my DLang Lexer - Interactive shell prompt
    ============================================================

    How to use:
    - Type a line of DLang code and press ENTER to tokenize it.
    - Type :file <path> to tokenize a DLang program stored in a text file.
    - Type :q and press ENTER to quit.

    ============================================================
    """.strip("\n"))

    lexer = DLangLexer()

    while True:
        try:
            line = input("dlang> ")
        except EOFError:
            print()
            break

        stripped = line.strip()

        if stripped == ":q":
            break

        if stripped.startswith(":file "):
            path = stripped[len(":file "):]
            run_lexer_on_file(lexer, path)
            continue

        print("-----------------  Generated tokens -----------------")
        for tok in lexer.tokenize(line):
            col = lexer._find_column(tok.index)
            print(f"{tok.type:<14} value={tok.value!r:<15} Line={tok.lineno:<3} Col={col}")
        print("-----------------------------------------------------\n")

    print("Exiting...")


if __name__ == "__main__":
    interactive_prompt_run()

