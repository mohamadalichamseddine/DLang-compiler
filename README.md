# DLang Compiler

A compiler implementation for DLang, built in Python.

## Dependencies

This project depends on the SLY (Sly Lex Yacc) library, which is included as a Git submodule.

### Clone the repository

To clone this repository along with its dependencies, run:

```bash
git clone --recurse-submodules https://github.com/mohamadalichamseddine/DLang-compiler.git
```

If you have already cloned the repository without submodules, initialize them with:

```bash
git submodule update --init --recursive
```

### About SLY

`SLY` is developed and maintained in its own repository and is used here without modification.
It remains under its original license. See the `sly/` directory for source code and license details.
