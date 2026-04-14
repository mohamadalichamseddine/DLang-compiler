# DLang Compiler

A compiler front-end for DLang, implemented in Python using the SLY library.
The project covers the first three phases of compilation: lexical analysis, syntax analysis, and semantic analysis.

## Structure

| File                     | Description                                                                            |
| ------------------------ | -------------------------------------------------------------------------------------- |
| `DLangLexer.py`          | Lexical analyzer. Tokenizes DLang source code                                          |
| `DLangParser.py`         | Syntax analyzer. Parses the token stream and builds an AST                             |
| `DLangSemanticParser.py` | Semantic analyzer. Type checking, symbol table, declaration and return-type validation |

## Usage

**Lexer** (interactive shell):
```bash
python DLangLexer.py
```

**Parser**:
```bash
python DLangParser.py
```

**Semantic analyzer**:
```bash
python DLangSemanticParser.py <source.dlang>
```

## Clone the repository

To clone this repository along with its dependencies, run:

```bash
git clone --recurse-submodules https://github.com/mohamadalichamseddine/DLang-compiler.git
```

If you have already cloned the repository without submodules, initialize them with:

```bash
git submodule update --init --recursive
```

## Dependencies

This project depends on the SLY (Sly Lex Yacc) library, which is included as a Git submodule.

### About SLY

`SLY` is developed and maintained in its own repository and is used here without modification.
It remains under its original license. See the `sly/` directory for source code and license details.
