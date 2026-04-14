from sly.src.sly.yacc import Parser
from DLangLexer import DLangLexer


class DLangParser(Parser):

    tokens = DLangLexer.tokens
    debugfile = 'parser.out'

    precedence = (
        ('right', 'ASSIGN'),
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'EQ', 'NE'),
        ('left', 'LT', 'LE', 'GT', 'GE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MOD'),
        ('right', 'NOT', 'UMINUS'),
    )

    def __init__(self):
        super().__init__()
        self.has_syntax_error = False
        self.last_construct = 'Program'

    #############################################
    ####            Helper methods           ####
    #############################################
    def _found(self, construct_name: str):
        self.last_construct = construct_name
        print(f"Found {construct_name}")

    def _reportSyntaxError(self, construct_name: str, token=None):
        self.has_syntax_error = True
        self.last_construct = construct_name
        print(f"Found syntax error at {construct_name}")

    def _guessConstruct(self, token):
        if token is None:
            return self.last_construct

        token_type = token.type
        if token_type in {'INT', 'DOUBLE', 'BOOL', 'STRING'}:
            return 'VariableDecl'
        if token_type == 'NOTHING':
            return 'FunctionDecl'
        if token_type == 'IF':
            return 'IfStmt'
        if token_type == 'WHILE':
            return 'WhileStmt'
        if token_type == 'FOR':
            return 'ForStmt'
        if token_type == 'RETURN':
            return 'ReturnStmt'
        if token_type == 'BREAK':
            return 'BreakStmt'
        if token_type == 'OUTPUT':
            return 'OutputStmt'
        if token_type == 'LBRACE':
            return 'StmtBlock'
        if token_type == 'ID':
            return 'VariableDecl'
        return self.last_construct

    #############################################
    ####       Program and declarations      ####
    #############################################
    @_('decl_list')
    def program(self, p):
        return ('program', p.decl_list)

    @_('decl_list decl')
    def decl_list(self, p):
        return p.decl_list + [p.decl]

    @_('decl')
    def decl_list(self, p):
        return [p.decl]

    @_('variable_decl', 'function_decl')
    def decl(self, p):
        return p[0]

    @_('variable SEMICOL')
    def variable_decl(self, p):
        self._found('VariableDecl')
        return ('variable_decl', p.variable)

    @_('type ID')
    def variable(self, p):
        return ('variable', p.type, p.ID)

    @_('INT', 'DOUBLE', 'BOOL', 'STRING')
    def type(self, p):
        return p[0]

    @_('type ID LPAREN formals RPAREN stmt_block')
    def function_decl(self, p):
        self._found('FunctionDecl')
        return ('function_decl', p.type, p.ID, p.formals, p.stmt_block)

    @_('NOTHING ID LPAREN formals RPAREN stmt_block')
    def function_decl(self, p):
        self._found('FunctionDecl')
        return ('function_decl', 'nothing', p.ID, p.formals, p.stmt_block)

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

    #############################################
    ####   Statement blocks and statements   ####
    #############################################
    @_('LBRACE variable_decl_list stmt_list RBRACE')
    def stmt_block(self, p):
        self._found('StmtBlock')
        return ('stmt_block', p.variable_decl_list, p.stmt_list)

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

    @_('expr_stmt', 'if_stmt', 'while_stmt', 'for_stmt', 'break_stmt', 'return_stmt', 'output_stmt', 'stmt_block')
    def stmt(self, p):
        return p[0]

    @_('expr_opt SEMICOL')
    def expr_stmt(self, p):
        return ('expr_stmt', p.expr_opt)

    @_('IF LPAREN expr RPAREN stmt ELSE stmt')
    def if_stmt(self, p):
        self._found('IfStmt')
        return ('if_stmt', p.expr, p.stmt0, p.stmt1)

    @_('IF LPAREN expr RPAREN stmt')
    def if_stmt(self, p):
        self._found('IfStmt')
        return ('if_stmt', p.expr, p.stmt, None)

    @_('WHILE LPAREN expr RPAREN stmt')
    def while_stmt(self, p):
        self._found('WhileStmt')
        return ('while_stmt', p.expr, p.stmt)

    @_('FOR LPAREN expr_opt SEMICOL expr SEMICOL expr_opt RPAREN stmt')
    def for_stmt(self, p):
        self._found('ForStmt')
        return ('for_stmt', p.expr_opt0, p.expr, p.expr_opt1, p.stmt)

    @_('RETURN expr_opt SEMICOL')
    def return_stmt(self, p):
        self._found('ReturnStmt')
        return ('return_stmt', p.expr_opt)

    @_('BREAK SEMICOL')
    def break_stmt(self, p):
        self._found('BreakStmt')
        return ('break_stmt',)

    @_('OUTPUT LPAREN actuals_nonempty RPAREN SEMICOL')
    def output_stmt(self, p):
        self._found('OutputStmt')
        return ('output_stmt', p.actuals_nonempty)

    #############################################
    ####             Expressions             ####
    #############################################
    @_('expr')
    def expr_opt(self, p):
        return p.expr

    @_('empty')
    def expr_opt(self, p):
        return None

    @_('ID ASSIGN expr')
    def expr(self, p):
        self._found('Assignment')
        return ('assign', p.ID, p.expr)

    @_('ID')
    def expr(self, p):
        return ('id', p.ID)

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
        return ('+', p.expr0, p.expr1)

    @_('expr MINUS expr')
    def expr(self, p):
        return ('-', p.expr0, p.expr1)

    @_('expr TIMES expr')
    def expr(self, p):
        return ('*', p.expr0, p.expr1)

    @_('expr DIVIDE expr')
    def expr(self, p):
        return ('/', p.expr0, p.expr1)

    @_('expr MOD expr')
    def expr(self, p):
        return ('%', p.expr0, p.expr1)

    @_('MINUS expr %prec UMINUS')
    def expr(self, p):
        return ('neg', p.expr)

    @_('expr LT expr')
    def expr(self, p):
        return ('<', p.expr0, p.expr1)

    @_('expr LE expr')
    def expr(self, p):
        return ('<=', p.expr0, p.expr1)

    @_('expr GT expr')
    def expr(self, p):
        return ('>', p.expr0, p.expr1)

    @_('expr GE expr')
    def expr(self, p):
        return ('>=', p.expr0, p.expr1)

    @_('expr EQ expr')
    def expr(self, p):
        return ('==', p.expr0, p.expr1)

    @_('expr NE expr')
    def expr(self, p):
        return ('!=', p.expr0, p.expr1)

    @_('expr AND expr')
    def expr(self, p):
        return ('&&', p.expr0, p.expr1)

    @_('expr OR expr')
    def expr(self, p):
        return ('||', p.expr0, p.expr1)

    @_('NOT expr')
    def expr(self, p):
        return ('!', p.expr)

    @_('INPUTINT LPAREN RPAREN')
    def expr(self, p):
        return ('InputInt',)

    @_('INPUTLINE LPAREN RPAREN')
    def expr(self, p):
        return ('InputLine',)

    @_('ID LPAREN actuals RPAREN')
    def call(self, p):
        self._found('FunctionCall')
        return ('call', p.ID, p.actuals)

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

    @_('INT_CONST')
    def constant(self, p):
        return ('int_const', p.INT_CONST)

    @_('DOUBLE_CONST')
    def constant(self, p):
        return ('double_const', p.DOUBLE_CONST)

    @_('BOOL_CONST')
    def constant(self, p):
        return ('bool_const', p.BOOL_CONST)

    @_('STRING_CONST')
    def constant(self, p):
        return ('string_const', p.STRING_CONST)

    @_('NULL')
    def constant(self, p):
        return ('null', None)

    @_('')
    def empty(self, p):
        return None

    #############################################
    ####           Error Handling            ####
    #############################################
    def error(self, token):
        if not self.has_syntax_error:
            construct = self._guessConstruct(token)
            self._reportSyntaxError(construct, token)
        return None


def applyParsingFromDLangSourceFile(path: str):
    with open(path, 'r', encoding='utf-8') as source_file:
        program = source_file.read()

    dLangLexer = DLangLexer()
    dLangParser = DLangParser()

    lexer_has_error = {'value': False}
    original_print_error = dLangLexer._print_error

    def tracked_print_error(message, token):
        lexer_has_error['value'] = True
        original_print_error(message, token)

    dLangLexer._print_error = tracked_print_error

    producedTokens = dLangLexer.tokenize(program)
    dLangParser.parse(producedTokens)

    if not lexer_has_error['value'] and not dLangParser.has_syntax_error:
        print('Parsing Completed Successfully!')


if __name__ == '__main__':
    filePath = input('Enter DLang source file path: ').strip()

    if not filePath:
        print('No file path provided.')
    else:
        applyParsingFromDLangSourceFile(filePath)