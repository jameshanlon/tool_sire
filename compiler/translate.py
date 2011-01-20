import sys
import ast
import printer
import definitions as defs
from walker import NodeWalker
from type import Type

INDENT = '  '
MAX_TEMPS = 100
BEGIN_BLOCK = '^'
END_BLOCK = '*'

op_conversion = {
    '+'   : '+',
    '-'   : '-',
    '*'   : '*',
    '/'   : '/',
    'rem' : '%',
    'or'  : '||',
    'and' : '&&',
    'xor' : '^',
    '~'   : '!',
    '<<'  : '<<',
    '>>'  : '>>',
    '<'   : '<',
    '>'   : '>',
    '<='  : '<=',
    '>='  : '>=',
    '='   : '==',
    '~='  : '!=',
}

proc_conversion = {
    'printval'   : 'printint',
    'printvalln' : 'printintln',
    'exit'       : '_exit',
}

class Blocker(object):
    """ A class to buffer and output blocks containing declarations and 
        statements
    """

    class BlockBegin(object):
        def __init__(self):
            self.temps = []

    class BlockEnd(object):
        def __init__(self):
            pass

    def __init__(self, translator, buf):
        self.translator = translator
        self.buf = buf
        self.stack = []
        self.temps = []
        self.temp_counter = 0
        self.unused_temps = list(range(MAX_TEMPS))

    def begin(self):
        self.stack.append(self.BlockBegin())
        self.temps.append(BEGIN_BLOCK)

    def end(self):
        self.stack.append(self.BlockEnd())

        # Remove temps not out of scope
        while not self.temps[-1] == BEGIN_BLOCK:
           t = self.temps.pop()
           self.unused_temps.insert(0, t)
        self.temps.pop()

    def get_tmp(self):
        """ Get the next unused temporary variable """
        t = self.unused_temps[0]
        del self.unused_temps[0]
        self.temps.append(t)
        
        # Insert in in the current scope, skipping any nested blocks
        skip = 0
        for x in reversed(self.stack):
            if isinstance(x, self.BlockEnd):
                skip += 1
            if isinstance(x, self.BlockBegin):
                if skip == 0:
                    x.temps.append(t)
                    break
                else:
                    skip -= 1

        return '_t{}'.format(t)

    def insert(self, s):
        """ Insert a statement """
        self.stack.append(s)
   
    def output(self):
        depth = 0
        for x in self.stack:
            if isinstance(x, self.BlockBegin):
                self.out(depth, '{\n')
                depth += 1
                # Output temporaries declaration
                if len(x.temps) > 0: 
                    self.out(depth, 'unsigned '+
                        (', '.join(['_t{}'.format(t) for t in x.temps]))+';\n')
            elif isinstance(x, self.BlockEnd):
                depth -= 1
                self.out(depth, '}\n')
            else:
                self.out(depth, x+'\n')

    def out(self, d, s):
        """ Write an indented line """
        self.buf.write((INDENT*d)+s)
   

class Translate(NodeWalker):
    """ A walker class to pretty-print the AST in the langauge syntax 
    """
    
    def __init__(self, semantics, buf):
        super(Translate, self).__init__()
        self.sem = semantics
        self.buf = buf
        self.indent = [INDENT]
        self.blocker = Blocker(self, buf)
        self.printer = printer.Printer(buf)

    def out(self, s):
        """ Write an indented line """
        self.blocker.insert(s)

    def asm(self, template, outop=None, inops=None, clobber=None):
        """ Write an inline assembly statement """
        self.out('asm("{}"{}{}{}{}{}{});'.format(
            template,
            ' : ' if outop or inops or clobber else '',
            '"=r"('+outop+')' if outop else '', 
            ' : ' if inops or clobber  else '', 
            ', '.join(['"r"('+x+')' for x in inops]) if inops else '',
            ' : '   if clobber else '',
            clobber if clobber else ''
            ))

    def ppt(self, method, node):
        """ Display a pretty-printed AST node in a comment """
        self.out('/*\n')
        #getattr(self.printer, method)(node, 0)
        self.out('\n')
        self.out('*/\n')

    def stmt_block(self, stmt):
        """ Decide whether the statement needs a block """
        if not (isinstance(stmt, ast.StmtSeq) 
                or isinstance(stmt, ast.StmtPar)):
            self.blocker.begin()
            self.stmt(stmt)
            self.blocker.end()
        else:
            self.stmt(stmt)
        
    def procedure_name(self, name):
        """ If a procedure name has a conversion, return it """
        # Check for conversion (TODO: neaten this)
        if name in proc_conversion:
            return proc_conversion[name] 
        else:
            return name

    def arguments(self, arg_list):
        """ Build the list of arguments. If there is an array reference 
            proper, it must be loaded manually.
        """
        args = []
        for x in arg_list.children():
            # For single array arguments, load the address given by this
            # variable manually to circumvent an XC type error.
            arg = None
            if isinstance(x, ast.ExprSingle):
                if isinstance(x.elem, ast.ElemId):
                    if x.elem.symbol.type.form == 'array':
                        tmp = self.blocker.get_tmp()
                        self.asm('mov %0, %1', outop=tmp,
                                inops=[x.elem.name])
                        arg = tmp
            args.append(arg if arg else self.expr(x))
        return ', '.join(args)

    def header(self):
        self.out('#include <xs1.h>')
        self.out('#include <print.h>')
        self.out('#include <syscall.h>')
  
    def definitions(self):
        self.out('#define TRUE 1')
        self.out('#define FALSE 0')

    # Program ============================================

    def walk_program(self, node):
        self.header()
        self.out('')
        self.definitions()
        self.out('')
        self.decls(node.decls)
        self.out('')
        self.defs(node.defs, 0)
        self.blocker.output()
    
    # Variable declarations ===============================

    def decls(self, node):
        for x in node.children():
            self.out(self.decl(x))

    def decl(self, node):
        s = '{}'.format(node.name)

        # Forms
        if node.type.form == 'array':
            s += '[{}]'.format(self.expr(node.expr))
        elif node.type.form == 'alias':
            return 'unsigned '+s+';'
        
        # Specifiers
        if node.type.specifier == 'var':
            s = 'int {}'.format(s)+';'
        elif node.type.specifier == 'val':
            s = '#define {} {}'.format(s, self.expr(node.expr))
        elif node.type.specifier == 'port':
            s = 'const unsigned {} = {};'.format(s, self.expr(node.expr))
        else:
            s = '{} {}'.format(node.type.specifier, s)
        
        return s

    # Procedure declarations ==============================

    def defs(self, node, d):
        for p in node.children():
            self.defn(p, d)

    def defn(self, node, d):
        self.out('#pragma unsafe arrays')
        s = ''
        #if node.type.specifier == 'proc':   s += 'int'
        #elif node.type.specifier == 'func': s += 'int'
        if node.name == '_main':
            s += 'void'
        else:
            s += 'int'
        s += ' {}({})'.format(
                self.procedure_name(node.name), 
                self.formals(node.formals))
        self.out(s)
        self.blocker.begin()
        self.decls(node.decls)
        self.stmt_block(node.stmt)
        self.blocker.end()
        self.out('')
    
    # Formals =============================================
    
    def formals(self, node):
        return ', '.join([self.param(x) for x in node.children()])

    def param(self, node):
        s = '{}'.format(node.name)

        # Forms
        if node.type.form == 'alias':
            return 'unsigned '+s

        # Specifiers
        if node.type == Type('var', 'single'):
            s = '&' + s
        elif node.type.specifier == 'var' or node.type.specifier == 'val':
            s = 'int ' + s
        elif node.type.specifier == 'chanend':
            s = 'unsigned '+s

        return s

    # Statements ==========================================

    def stmt_seq(self, node):
        self.blocker.begin()
        for x in node.children(): 
            self.stmt(x)
        self.blocker.end()

    def stmt_par(self, node):
        #self.buf.write(self.indt(d-1)+'par {\n')
        #for x in node.children():
        #    self.stmt(x)
        #    self.buf.write('\n')
        #self.buf.write(self.indt(d-1)+'}')
        pass

    def stmt_skip(self, node):
        pass

    def stmt_pcall(self, node):
        self.out('{}({});'.format(
            self.procedure_name(node.name), self.arguments(node.args)))

    def stmt_ass(self, node):
    
        # If the target is an alias, then generate a store after
        if node.left.symbol.type.form == 'alias':
            tmp = self.blocker.get_tmp()
            self.out('{} = {};'.format(tmp, self.expr(node.expr)))
            self.asm('stw %0, %1[%2]', 
                    inops=[tmp, node.left.name, self.expr(node.left.expr)])
        
        # Otherwise, proceede normally
        else:
            self.out('{} = {};'.format(
                self.elem(node.left), self.expr(node.expr)))

    def stmt_in(self, node):
        self.out('{} ? {};'.format(
            self.elem(node.left), self.expr(node.expr)))

    def stmt_out(self, node):
        self.out('{} ! {};'.format(
            self.elem(node.left), self.expr(node.expr)))

    def stmt_if(self, node):
        self.out('if ({})'.format(self.expr(node.cond)))
        self.stmt_block(node.thenstmt)
        if not isinstance(node.elsestmt, ast.StmtSkip):
            self.out('else')
            self.stmt_block(node.elsestmt)

    def stmt_while(self, node):
        self.out('while ({})'.format(self.expr(node.cond)))
        self.stmt_block(node.stmt)
    
    def stmt_for(self, node):
        self.out('for ({0} = {1}; {0} <= {2}; {0}++)'.format(
            self.elem(node.var),
            self.expr(node.init), self.expr(node.bound)))
        self.stmt_block(node.stmt)

    def stmt_on(self, node):
        self.out('on {}: '.format(self.elem(node.core)))
        self.stmt(node.pcall)
        self.out(';')

    def stmt_connect(self, node):
        self.out('connect {} to {} : {};'.format(
            self.elem(node.left), self.elem(node.core), self.elem(node.dest)))

    def stmt_aliases(self, node):
        self.asm('add %0, %1, %2', 
                outop=node.dest, 
                inops=[node.name, '({})*{}'.format(
                    self.elem(node.expr), defs.BYTES_PER_WORD)])

    def stmt_return(self, node):
        self.out('return {};'.format(self.expr(node.expr)))

    # Expressions =========================================

    def expr_list(self, node):
        return ', '.join([self.expr(x) for x in node.children()])
    
    def expr_single(self, node):

        # If the elem is an alias subscript, generate a load
        if isinstance(node.elem, ast.ElemSub):
            if node.elem.symbol.type.form == 'alias':
                tmp = self.blocker.get_tmp()
                self.asm('ldw %0, %1[%2]', outop=tmp,
                        inops=[node.elem.name, self.expr(node.elem.expr)])
                return tmp

        # Otherwise, just return
        return self.elem(node.elem)

    def expr_unary(self, node):
        
        # If the elem is an alias subscript, generate a load
        if isinstance(node.elem, ast.ElemSub):
            if node.elem.symbol.type.form == 'alias':
                tmp = self.blocker.get_tmp()
                self.asm('ldw %0, %1[%2]', outop=tmp,
                        inops=[node.elem.name, self.expr(node.elem.expr)])
                return '({}{})'.format(node.op, tmp)
        
        # Otherwise, just return
        else:
            return '({}{})'.format(node.op, self.elem(node.elem))

    def expr_binop(self, node):
        
        # If the elem is an alias subscript, generate a load
        if isinstance(node.elem, ast.ElemSub):
            if node.elem.symbol.type.form == 'alias':
                tmp = self.blocker.get_tmp()
                self.asm('ldw %0, %1[%2]', outop=tmp,
                        inops=[node.elem.name, self.expr(node.elem.expr)])
                return '{} {} {}'.format(tmp,
                        op_conversion[node.op], self.expr(node.right))
        
        # Otherwise, just return
        return '{} {} {}'.format(self.elem(node.elem), 
                op_conversion[node.op], self.expr(node.right))
    
    # Elements= ===========================================

    def elem_group(self, node):
        return '({})'.format(self.expr(node.expr))

    def elem_sub(self, node):
        return '{}[{}]'.format(node.name, self.expr(node.expr))
        #if node.symbol.type.form == 'array':
        #    return '{}[{}]'.format(node.name, self.expr(node.expr))
        #elif node.symbol.type.form == 'alias':
        #    return None

    def elem_fcall(self, node):
        return '{}({})'.format(node.name, self.arguments(node.args))

    def elem_number(self, node):
        return '{}'.format(node.value)

    def elem_boolean(self, node):
        return '{}'.format(node.value.upper())

    def elem_string(self, node):
        return '{}'.format(node.value)

    def elem_char(self, node):
        return '{}'.format(node.value)

    def elem_id(self, node):
        return node.name

