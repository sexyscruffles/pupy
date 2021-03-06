# -*- coding: utf-8 -*-

import ast
import marshal
import logging

try:
    from .PupyLogger import getLogger
    logger = getLogger('compiler')
except ValueError:
    # If PupyCompile imported directly (build_library_zip.py)
    logger = logging.getLogger('compiler')

class Compiler(ast.NodeTransformer):
    def __init__(self, data, path=False, main=False):
        source = data
        if path:
            with open(data) as src:
                source = src.read()

        self._main = main

        ast.NodeTransformer.__init__(self)
        self._source_ast = ast.parse(source)

    def compile(self, filename, obfuscate=False, raw=False):
        body = marshal.dumps(compile(self.visit(self._source_ast), filename, 'exec'))
        if obfuscate:
            l = len(body)
            offset = 0 if raw else 8

            output = bytearray(l + 8)
            for i,x in enumerate(body):
                output[i+offset] = (ord(x)^((2**((65535-i)%65535))%251))

            if raw:
                for i in xrange(8):
                    output[i] = 0

            return output

        elif raw:
            return body

        else:
            return '\0'*8 + body

    def visit_If(self, node):
        if hasattr(node.test, 'id') and node.test.id == '__debug__':
            return node.orelse
        if not self._main and type(node.test) == ast.Compare and type(node.test.left) == ast.Name \
          and node.test.left.id == '__name__':
          for comparator in node.test.comparators:
              if type(comparator) == ast.Str and comparator.s == '__main__':
                  return node.orelse
        elif hasattr(node.test, 'operand') and type(node.test.op) == ast.Not \
          and type(node.test.operand) == ast.Name and node.test.operand.id == '__debug__':
            return node.body

        return node

    def visit_Expr(self, node):
        if type(node.value) == ast.Call and type(node.value.func) == ast.Attribute and \
          type(node.value.func.value) == ast.Name and \
          node.value.func.value.id == 'logging' and node.value.func.attr == 'debug':
          return None
        elif (type(node.value) == ast.Str):
            node.value.s = ""

        return node

def pupycompile(data, filename='', path=False, obfuscate=False, raw=False, debug=False, main=False):
    if not debug:
        logger.info(data if path else filename)
        data = Compiler(data, path, main).compile(filename, obfuscate, raw)
    else:
        source = data
        if path:
            with open(data) as sfile:
                source = sfile.read()

        logger.info('debug: {}'.format(data if path else filename))
        data = marshal.dumps(compile(source, filename, 'exec'))

    return data
