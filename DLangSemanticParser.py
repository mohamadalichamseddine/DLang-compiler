import sys
from sly.src.sly.yacc import Parser
from DLangLexer import DLangLexer


# ==================================
# SYMBOL TABLE
# ==================================

class SymbolTable:

    def __init__(self):
        self.table = []

    def add_name(self, name):
        self.table.append({'name': name})

    def add_type(self, name, typee):
        for entry in self.table:
            if entry['name'] == name:
                entry['type'] = typee
                return

    def add_formals(self, func_name, formal):
        for entry in self.table:
            if entry['name'] == func_name:
                entry.setdefault('formals', []).append(formal)
                return

    def get_formals(self, func_name):
        for entry in self.table:
            if entry['name'] == func_name:
                return entry.get('formals', [])
        return []

    def lookup_name(self, name):
        return any(entry['name'] == name for entry in self.table)

    def get_type(self, symbol):
        for entry in self.table:
            if entry['name'] == symbol:
                return entry.get('type', 'error')
        return 'error'


# ==================================
# SEMANTIC PARSER
# ==================================

class DLangSemanticParser(Parser):

    debugfile = 'semantic_parser.out'
    tokens    = DLangLexer.tokens

    # Precedence (lowest to highest).
    # IFX is a pseudo-token that marks the single-arm if rule so that ELSE
    # (which sits above it) is always preferred via shift — this eliminates
    # the dangling-else shift/reduce conflict.
    precedence = (
        ('nonassoc', 'IFX'),
        ('nonassoc', 'ELSE'),
        ('right',    'ASSIGN'),
        ('left',     'OR'),
        ('left',     'AND'),
        ('left',     'EQ', 'NE'),
        ('left',     'LT', 'LE', 'GT', 'GE'),
        ('left',     'PLUS', 'MINUS'),
        ('left',     'TIMES', 'DIVIDE', 'MOD'),
        ('right',    'NOT', 'UMINUS'),
    )

    def __init__(self):
        self.sym_table             = SymbolTable()
        self.has_semantic_error    = False
        # Return type of the function currently being parsed.
        # Set in func_header (before the body) so return statements can check it.
        self.current_function_type = None

    def semantic_error(self, msg, lineno=None):
        self.has_semantic_error = True
        if lineno:
            print(f"Semantic Error (line {lineno}): {msg}")
        else:
            print(f"Semantic Error: {msg}")

    # ----------------------------------
    # Program and declarations
    # ----------------------------------

    @_('decl_list')
    def program(self, p):
        return p.decl_list

    @_('decl_list decl')
    def decl_list(self, p):
        return p.decl_list + [p.decl]

    @_('decl')
    def decl_list(self, p):
        return [p.decl]

    @_('variable_decl', 'function_decl', 'stmt')
    def decl(self, p):
        return p[0]

    @_('variable SEMICOL')
    def variable_decl(self, p):
        return p.variable

    @_('type ID')
    def variable(self, p):
        if self.sym_table.lookup_name(p.ID):
            self.semantic_error(f"Variable '{p.ID}' already declared", p.lineno)
        else:
            self.sym_table.add_name(p.ID)
            self.sym_table.add_type(p.ID, p.type)
        return (p.type, p.ID)

    @_('INT')
    def type(self, p):
        return 'int'

    @_('DOUBLE')
    def type(self, p):
        return 'double'

    @_('BOOL')
    def type(self, p):
        return 'bool'

    @_('STRING')
    def type(self, p):
        return 'string'

    # Function declaration is split into func_header + stmt_block so that
    # current_function_type is set before the body is parsed, making it
    # available to return statements inside the body.

    @_('type ID LPAREN formals RPAREN')
    def func_header(self, p):
        func_name = p.ID
        func_type = p.type
        if self.sym_table.lookup_name(func_name):
            self.semantic_error(f"Function '{func_name}' already declared", p.lineno)
        else:
            self.sym_table.add_name(func_name)
            self.sym_table.add_type(func_name, func_type)
            for (f_type, f_name) in p.formals:
                self.sym_table.add_formals(func_name, (f_type, f_name))
        self.current_function_type = func_type
        return (func_name, func_type, p.formals)

    @_('NOTHING ID LPAREN formals RPAREN')
    def func_header(self, p):
        func_name = p.ID
        if self.sym_table.lookup_name(func_name):
            self.semantic_error(f"Function '{func_name}' already declared", p.lineno)
        else:
            self.sym_table.add_name(func_name)
            self.sym_table.add_type(func_name, 'nothing')
            for (f_type, f_name) in p.formals:
                self.sym_table.add_formals(func_name, (f_type, f_name))
        self.current_function_type = 'nothing'
        return (func_name, 'nothing', p.formals)

    @_('func_header stmt_block')
    def function_decl(self, p):
        self.current_function_type = None
        return 'nothing'

    @_('formal_list')
    def formals(self, p):
        return p.formal_list

    @_('empty')
    def formals(self, p):
        return []

    @_('variable')
    def formal_list(self, p):
        return [p.variable]

    @_('formal_list COMMA variable')
    def formal_list(self, p):
        return p.formal_list + [p.variable]

    # ----------------------------------
    # Statement blocks and statements
    # ----------------------------------

    @_('LBRACE variable_decl_list stmt_list RBRACE')
    def stmt_block(self, p):
        return 'nothing'

    @_('variable_decl_list variable_decl')
    def variable_decl_list(self, p):
        return p.variable_decl_list + [p.variable_decl]

    @_('empty')
    def variable_decl_list(self, p):
        return []

    @_('stmt_list stmt')
    def stmt_list(self, p):
        return p.stmt_list + [p.stmt]

    @_('empty')
    def stmt_list(self, p):
        return []

    @_('expr_stmt', 'if_stmt', 'while_stmt', 'for_stmt',
       'break_stmt', 'return_stmt', 'output_stmt', 'stmt_block')
    def stmt(self, p):
        return p[0]

    @_('expr_opt SEMICOL')
    def expr_stmt(self, p):
        return p.expr_opt

    @_('IF LPAREN expr RPAREN stmt ELSE stmt')
    def if_stmt(self, p):
        if p.expr not in ('bool', 'error'):
            self.semantic_error(
                f"If condition must be of type 'bool', got '{p.expr}'", p.lineno)
        return 'nothing'

    @_('IF LPAREN expr RPAREN stmt %prec IFX')
    def if_stmt(self, p):
        if p.expr not in ('bool', 'error'):
            self.semantic_error(
                f"If condition must be of type 'bool', got '{p.expr}'", p.lineno)
        return 'nothing'

    @_('WHILE LPAREN expr RPAREN stmt')
    def while_stmt(self, p):
        if p.expr not in ('bool', 'error'):
            self.semantic_error(
                f"While condition must be of type 'bool', got '{p.expr}'", p.lineno)
        return 'nothing'

    @_('FOR LPAREN expr_opt SEMICOL expr SEMICOL expr_opt RPAREN stmt')
    def for_stmt(self, p):
        return 'nothing'

    @_('RETURN expr_opt SEMICOL')
    def return_stmt(self, p):
        lineno    = p.lineno
        expr_type = p.expr_opt   # None for bare 'return;'
        func_type = self.current_function_type

        if expr_type is None:
            if func_type is not None and func_type != 'nothing':
                self.semantic_error(
                    f"Return with no value in function with return type '{func_type}'",
                    lineno)
        else:
            if func_type == 'nothing':
                self.semantic_error("Return value in 'nothing' function", lineno)
            elif (expr_type != 'error'
                  and func_type is not None
                  and func_type != 'error'
                  and expr_type != func_type):
                self.semantic_error(
                    f"Return type mismatch: expected '{func_type}', got '{expr_type}'",
                    lineno)

        return expr_type if expr_type is not None else 'nothing'

    @_('BREAK SEMICOL')
    def break_stmt(self, p):
        return 'nothing'

    @_('OUTPUT LPAREN actuals_nonempty RPAREN SEMICOL')
    def output_stmt(self, p):
        return 'nothing'

    # ----------------------------------
    # Expressions
    # ----------------------------------

    @_('expr')
    def expr_opt(self, p):
        return p.expr

    @_('empty')
    def expr_opt(self, p):
        return None

    @_('ID ASSIGN expr')
    def expr(self, p):
        var_name = p.ID
        rhs_type = p.expr

        if not self.sym_table.lookup_name(var_name):
            self.semantic_error(f"Variable '{var_name}' not declared", p.lineno)
            return 'error'

        lhs_type = self.sym_table.get_type(var_name)

        # Skip type check if either side already has an error to avoid cascading
        if rhs_type != 'error' and lhs_type != 'error':
            if lhs_type != rhs_type:
                self.semantic_error(
                    f"Type mismatch in assignment: cannot assign '{rhs_type}' "
                    f"to '{var_name}' (type '{lhs_type}')", p.lineno)
                return 'error'
        return lhs_type

    @_('ID')
    def expr(self, p):
        if not self.sym_table.lookup_name(p.ID):
            self.semantic_error(f"Variable '{p.ID}' not declared", p.lineno)
            return 'error'
        return self.sym_table.get_type(p.ID)

    @_('constant')
    def expr(self, p):
        return p.constant

    @_('call')
    def expr(self, p):
        return p.call

    @_('LPAREN expr RPAREN')
    def expr(self, p):
        return p.expr

    @_('expr PLUS expr')
    def expr(self, p):
        # '+' also handles string concatenation
        left, right = p.expr0, p.expr1
        if left == 'error' or right == 'error':
            return 'error'
        if left == right and left in ('int', 'double', 'string'):
            return left
        self.semantic_error(
            f"Type mismatch in '+': cannot add '{left}' and '{right}'", p.lineno)
        return 'error'

    @_('expr MINUS expr')
    def expr(self, p):
        left, right = p.expr0, p.expr1
        if left == 'error' or right == 'error':
            return 'error'
        if left == right and left in ('int', 'double'):
            return left
        self.semantic_error(
            f"Type mismatch in '-': cannot subtract '{left}' and '{right}'", p.lineno)
        return 'error'

    @_('expr TIMES expr')
    def expr(self, p):
        left, right = p.expr0, p.expr1
        if left == 'error' or right == 'error':
            return 'error'
        if left == right and left in ('int', 'double'):
            return left
        self.semantic_error(
            f"Type mismatch in '*': cannot multiply '{left}' and '{right}'", p.lineno)
        return 'error'

    @_('expr DIVIDE expr')
    def expr(self, p):
        left, right = p.expr0, p.expr1
        if left == 'error' or right == 'error':
            return 'error'
        if left == right and left in ('int', 'double'):
            return left
        self.semantic_error(
            f"Type mismatch in '/': cannot divide '{left}' and '{right}'", p.lineno)
        return 'error'

    @_('expr MOD expr')
    def expr(self, p):
        left, right = p.expr0, p.expr1
        if left == 'error' or right == 'error':
            return 'error'
        if left == 'int' and right == 'int':
            return 'int'
        self.semantic_error(
            f"Type mismatch in '%': modulo requires 'int' operands, "
            f"got '{left}' and '{right}'", p.lineno)
        return 'error'

    @_('MINUS expr %prec UMINUS')
    def expr(self, p):
        t = p.expr
        if t == 'error':
            return 'error'
        if t in ('int', 'double'):
            return t
        self.semantic_error(f"Unary minus requires numeric operand, got '{t}'", p.lineno)
        return 'error'

    @_('expr LT expr')
    def expr(self, p):
        return self._check_ordering(p, '<')

    @_('expr LE expr')
    def expr(self, p):
        return self._check_ordering(p, '<=')

    @_('expr GT expr')
    def expr(self, p):
        return self._check_ordering(p, '>')

    @_('expr GE expr')
    def expr(self, p):
        return self._check_ordering(p, '>=')

    @_('expr EQ expr')
    def expr(self, p):
        return self._check_equality(p, '==')

    @_('expr NE expr')
    def expr(self, p):
        return self._check_equality(p, '!=')

    def _check_ordering(self, p, op):
        left, right = p.expr0, p.expr1
        if left == 'error' or right == 'error':
            return 'bool'
        if left == right and left in ('int', 'double'):
            return 'bool'
        self.semantic_error(
            f"Type mismatch in '{op}': requires numeric operands of same type, "
            f"got '{left}' and '{right}'", p.lineno)
        return 'bool'

    def _check_equality(self, p, op):
        left, right = p.expr0, p.expr1
        if left == 'error' or right == 'error':
            return 'bool'
        if left == right or 'null' in (left, right):
            return 'bool'
        self.semantic_error(
            f"Type mismatch in '{op}': cannot compare '{left}' and '{right}'", p.lineno)
        return 'bool'

    @_('expr AND expr')
    def expr(self, p):
        return self._check_logical(p, '&&')

    @_('expr OR expr')
    def expr(self, p):
        return self._check_logical(p, '||')

    def _check_logical(self, p, op):
        left, right = p.expr0, p.expr1
        if left == 'error' or right == 'error':
            return 'bool'
        if left == 'bool' and right == 'bool':
            return 'bool'
        self.semantic_error(
            f"Logical operator '{op}' requires 'bool' operands, "
            f"got '{left}' and '{right}'", p.lineno)
        return 'bool'

    @_('NOT expr')
    def expr(self, p):
        t = p.expr
        if t != 'error' and t != 'bool':
            self.semantic_error(f"'!' requires 'bool' operand, got '{t}'", p.lineno)
        return 'bool'

    @_('INPUTINT LPAREN RPAREN')
    def expr(self, p):
        return 'int'

    @_('INPUTLINE LPAREN RPAREN')
    def expr(self, p):
        return 'string'

    # ----------------------------------
    # Function calls
    # ----------------------------------

    @_('ID LPAREN actuals RPAREN')
    def call(self, p):
        func_name = p.ID
        actuals   = p.actuals

        if not self.sym_table.lookup_name(func_name):
            self.semantic_error(f"Function '{func_name}' not declared", p.lineno)
            return 'error'

        formals = self.sym_table.get_formals(func_name)

        if len(actuals) != len(formals):
            self.semantic_error(
                f"Argument count mismatch in call to '{func_name}': "
                f"expected {len(formals)}, got {len(actuals)}", p.lineno)
            return self.sym_table.get_type(func_name)

        for i, (actual_type, (formal_type, _)) in enumerate(zip(actuals, formals)):
            if actual_type != 'error' and actual_type != formal_type:
                self.semantic_error(
                    f"Type mismatch in call to '{func_name}': "
                    f"argument {i + 1} expected '{formal_type}', got '{actual_type}'",
                    p.lineno)

        return self.sym_table.get_type(func_name)

    @_('actuals_nonempty')
    def actuals(self, p):
        return p.actuals_nonempty

    @_('empty')
    def actuals(self, p):
        return []

    @_('expr')
    def actuals_nonempty(self, p):
        return [p.expr]

    @_('actuals_nonempty COMMA expr')
    def actuals_nonempty(self, p):
        return p.actuals_nonempty + [p.expr]

    # ----------------------------------
    # Constants
    # ----------------------------------

    @_('INT_CONST')
    def constant(self, p):
        return 'int'

    @_('DOUBLE_CONST')
    def constant(self, p):
        return 'double'

    @_('BOOL_CONST')
    def constant(self, p):
        return 'bool'

    @_('STRING_CONST')
    def constant(self, p):
        return 'string'

    @_('NULL')
    def constant(self, p):
        return 'null'

    @_('')
    def empty(self, p):
        return None

    def error(self, token):
        if token:
            print(f"Syntax error at '{token.value}' (line {token.lineno})")
        else:
            print("Syntax error at end of input")


# ==================================
# MAIN
# ==================================

def run_semantic_analysis(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()

    lexer  = DLangLexer()
    parser = DLangSemanticParser()

    parser.parse(lexer.tokenize(source))

    if not parser.has_semantic_error:
        print("No Semantic Error!")

    print("Symbol Table Content")
    print(parser.sym_table.table)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        run_semantic_analysis(sys.argv[1])
    else:
        path = input('Enter DLang source file path: ').strip()
        if path:
            run_semantic_analysis(path)
        else:
            print('No file path provided.')
