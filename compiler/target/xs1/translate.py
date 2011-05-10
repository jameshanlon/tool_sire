# Copyright (c) 2011, James Hanlon, All rights reserved
# This software is freely distributable under a derivative of the
# University of Illinois/NCSA Open Source License posted in
# LICENSE.txt and at <http://github.xcore.com/>

import sys

import definitions as defs
import config
import ast
from util import read_file
from walker import NodeWalker
from type import Type
from blocker import Blocker
from blocker import INDENT

op_conversion = {
    '+'   : '+',
    '-'   : '-',
    '*'   : '*',
    '/'   : '/',
    'rem' : '%',
    'or'  : '||',
    'and' : '&&',
    'xor' : '^',
    '&'   : '&',
    'lor' : '|',
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

builtin_conversion = {
  # Printing
  'printchar'   : '_PRINTCHAR',
  'printcharln' : '_PRINTCHARLN',
  'printval'    : '_PRINTVAL',
  'printvalln'  : '_PRINTVALLN',
  'printhex'    : '_PRINTHEX',
  'printhexln'  : '_PRINTHEXLN',
  'printstr'    : '_PRINTSTR',
  'printstrln'  : '_PRINTSTRLN',
  'println'     : '_PRINTLN',
  # Fixed point
  'mul8_24'     : '_MUL_8_24',
  'div8_24'     : '_DIV_8_24',
}

class TranslateXS1(NodeWalker):
    """ A walker class to pretty-print the AST in the langauge syntax 
    """
    def __init__(self, semantics, children, buf):
        super(TranslateXS1, self).__init__()
        self.sem = semantics
        self.child = children
        self.buf = buf
        self.indent = [INDENT]
        self.blocker = Blocker(self, buf)
        self.label_counter = 0
        self.parent = None

    def out(self, s):
        """ Write an indented line
        """
        self.blocker.insert(s)

    def asm(self, template, outop=None, inops=None, clobber=None):
        """ Write an inline assembly statement
        """
        self.out('asm("{}"{}{}{}{}{}{});'.format(
            #template.replace('\n', ' ; '),
            template,
            ':' if outop or inops or clobber else '',
            '"=r"('+outop+')' if outop else '', 
            ':' if inops or clobber  else '', 
            ', '.join(['"r"('+x+')' for x in inops]) if inops else '',
            ':'   if clobber else '',
            ', '.join(['"'+x+'"' for x in clobber]) if clobber else ''
            ))

    def comment(self, s):
        """ Write a comment
        """
        self.out('// '+s)

    def stmt_block(self, stmt):
        """ Decide whether the statement needs a block
        """
        if not (isinstance(stmt, ast.StmtSeq) 
                or isinstance(stmt, ast.StmtPar)):
            self.blocker.begin()
            self.stmt(stmt)
            self.blocker.end()
        else:
            self.stmt(stmt)
        
    def procedure_name(self, name):
        """ If a procedure name has a conversion, return it
        """
        return builtin_conversion[name] if name in builtin_conversion else name

    def arguments(self, arg_list):
        """ Build the list of arguments for a procedure call. If there is an
            array reference proper, either directly or as a slice, it must be
            loaded manually with an assembly inline which forces the compiler to
            reveal the address.
        """
        args = []

        for x in arg_list.children():
            arg = None

            if isinstance(x, ast.ExprSingle):
            
                if isinstance(x.elem, ast.ElemId):
                    if x.elem.symbol.type.form == 'array':
                        tmp = self.blocker.get_tmp()
                        self.asm('mov %0, %1', outop=tmp,
                                inops=[x.elem.name])
                        arg = tmp
                
                elif isinstance(x.elem, ast.ElemSlice):
                    if x.elem.symbol.type.form == 'array':
                        tmp = self.blocker.get_tmp()
                        self.asm('add %0, %1, %2', outop=tmp,
                                inops=[x.elem.name, '({})*{}'.format(
                                self.expr(x.elem.begin),
                                defs.BYTES_PER_WORD)])
                        arg = tmp

            args.append(self.expr(x) if not arg else arg)

        return ', '.join(args)

    def get_label(self):
        """ Get the next unique label
        """
        l = '_L{}'.format(self.label_counter)
        self.label_counter += 1
        return l

    def header(self):
        self.out('#include <xs1.h>')
        self.out('#include <print.h>')
        self.out('#include <syscall.h>')
        self.out('#include "device.h"')
        self.out('#include "runtime/xs1/globals.h"')
        self.out('#include "runtime/xs1/util.h"')
        self.out('#include "runtime/xs1/guest.h"')
        self.out('#include "system/definitions.h"')
        self.out('#include "system/xs1/definitions.h"')
        self.out('')
  
    def builtins(self):
        """ Insert builtin code. We include builtin code directly here so that
            it can be transformed in the build process to be made 'mobile'. This
            is in contrast with the MPI implementation where there is only a
            single binary.
        """
        s = read_file(config.XS1_SYSTEM_PATH+'/builtins.xc')
        self.out(s)
    
    # Program ============================================

    def walk_program(self, node):

        # Walk the entire program
        self.header()
        self.builtins()
        self.decls(node.decls)
        self.defs(node.defs, 0)

        # Output the buffered blocks
        self.blocker.output()
    
    # Variable declarations ===============================

    def decls(self, node):
        for x in node.children():
            self.out(self.decl(x))
        if len(node.children()) > 0:
            self.out('')

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
        s += 'void' if node.name == '_main' else 'int'
        s += ' {}({})'.format(
                self.procedure_name(node.name),
                self.formals(node.formals))
        self.parent = node.name
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
        if (node.type.specifier == 'var' 
                or node.type.specifier == 'val'):
            s = 'int ' + s
        if node.type.specifier == 'chanend':
            s = 'unsigned '+s

        return s

    # Statements ==========================================

    def stmt_seq(self, node):
        self.blocker.begin()
        for x in node.children(): 
            self.stmt(x)
        self.blocker.end()

    def thread_set(self):
        """ Generate the initialisation for a slave thread, in the body of a for
            loop with _i indexing the thread number
        """

        # Get a synchronised thread
        self.out('unsigned _t;')
        self.out('unsigned _spnew;')
        self.asm('getst %0, res[%1]', outop='_t', inops=['_sync'])

        # Setup pc = &setupthread (from jump table)
        self.asm('ldw r11, cp[{}] ; init t[%0]:pc, r11'
                .format(defs.JUMPI_INIT_THREAD), 
                inops=['_t'], clobber=['r11'])

        # Move sp away: sp -= THREAD_STACK_SPACE and save it
        self.out('_spnew = _sp - (((_t>>8)&0xFF) * THREAD_STACK_SPACE);')
        self.asm('init t[%0]:sp, %1', inops=['_t', '_spnew'])

        # Setup dp, cp
        self.asm('ldaw r11, dp[0x0] ; init t[%0]:dp, r11', 
                 inops=['_t'], clobber=['r11'])
        self.asm('ldaw r11, cp[0x0] ; init t[%0]:cp, r11', 
                 inops=['_t'], clobber=['r11'])

        # Copy register values
        self.comment('Copy thread registers')
        for i in range(12):
            self.asm('set t[%0]:r{0}, r{0}'.format(i), inops=['_t'])
        
        self.comment('Copy thread stack')
        self.out('for(int _j=0; _j<_frametab[{}]; _j++)'.format(
            defs.JUMP_INDEX_OFFSET + self.sem.proc_names.index(self.parent)))
        self.blocker.begin()
        self.asm('ldw r11, %0[%1] ; stw r11, %2[%1]',
                inops=['_spbase', '_j', '_spnew'], clobber=['r11']) 
        self.blocker.end()

        # Copy thread id to the array
        self.out('_threads[_i] = _t;')

    def stmt_par(self, node):
        """ Generate a parallel block
        """
        self.blocker.begin()
        num_slaves = len(node.children()) - 1
        exit_label = self.get_label()

        self.comment('Parallel block')

        # Declare sync variable and array to store thread identifiers
        self.out('unsigned _sync;')
        self.out('unsigned _spbase;')
        self.out('unsigned _threads[{}];'.format(num_slaves))

        # Get a label for each thread
        thread_labels = [self.get_label() for i in range(num_slaves + 1)]

        self.comment('Get a sync, sp base, _spLock and claim num threads')
        
        # Get a thread synchroniser
        #self.out('_sync = GETR_SYNC();')
        self.asm('getr %0, " S(XS1_RES_TYPE_SYNC) "', outop='_sync');
       
        # Load the address of sp
        self.asm('ldaw %0, sp[0x0]', outop='_spbase')

        # Claim thread count
        self.asm('in r11, res[%0]', inops=['_numThreadsLock'], clobber=['r11'])
        self.out('_numThreads = _numThreads - {};'.format(num_slaves))
        self.asm('out res[%0], r11', inops=['_numThreadsLock'], clobber=['r11'])

        # Setup each slave thread
        self.comment('Initialise slave threads')
        self.out('for(int _i=0; _i<{}; _i++)'.format(num_slaves))
        self.blocker.begin()
        self.thread_set()
        self.blocker.end()
       
        # Set lr = &instruction label
        self.comment('Initialise slave link registers')
        for (i, x) in enumerate(node.children()):
            if not i == 0:
                self.asm('ldap r11, '+thread_labels[i]+' ; init t[%0]:lr, r11',
                    inops=['_threads[{}]'.format(i-1)], clobber=['r11'])

        # Master synchronise
        self.comment('Master synchronise')
        self.asm('msync res[%0]', inops=['_sync'])

        # Output each thread's instructions followed by a slave synchronise or
        # for the master, a master join and branch out of the block.
        for (i, x) in enumerate(node.children()):
            self.comment('Thread {}'.format(i))
            self.asm(thread_labels[i]+':')
            self.stmt(x)
            if i == 0:
                self.asm('mjoin res[%0]', inops=['_sync'])
                self.asm('bu '+exit_label)
            else:
                self.asm('ssync')

        # Ouput exit label 
        self.comment('Exit, free _sync, restore _sp and _numThreads')
        self.asm(exit_label+':')
        
        # Free synchroniser resource
        self.asm('freer res[%0]', inops=['_sync'])

        # Release thread count
        self.asm('in r11, res[%0]', inops=['_numThreadsLock'], clobber=['r11'])
        self.out('_numThreads = _numThreads + {};'.format(num_slaves))
        self.asm('out res[%0], r11', inops=['_numThreadsLock'], clobber=['r11'])

        self.blocker.end()

    def stmt_skip(self, node):
        pass

    def stmt_pcall(self, node):
        #if self.parent == node.name:
        #    self.out('#pragma stackcalls 10')
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
        self.out('for ({0} = {1}; {0} <= {2}; {0} += {3})'.format(
            self.elem(node.var), self.expr(node.init), 
            self.expr(node.bound), self.expr(node.step)))
        self.stmt_block(node.stmt)

    def stmt_on(self, node):
        """ Generate an on statement 
        """
        proc_name = node.pcall.name
        num_args = len(node.pcall.args.expr) if node.pcall.args.expr else 0 
        num_procs = len(self.child.children[proc_name]) + 1
        
        # Calculate closure size 
        closure_size = 2 + num_procs;
        for (i, x) in enumerate(node.pcall.args.expr):
            t = self.sem.sig.lookup_param_type(proc_name, i)
            if t.form == 'alias': closure_size = closure_size + 3
            elif t.form == 'single': closure_size = closure_size + 2 

        self.comment('On')
        
        self.blocker.begin()
        self.out('unsigned _closure[{}];'.format(closure_size))
        n = 0

        # Header: (#args, #procs)
        self.comment('Header: (#args, #procs)')
        self.out('_closure[{}] = {};'.format(n, num_args)) ; n+=1
        self.out('_closure[{}] = {};'.format(n, num_procs)) ; n+=1

        # Arguments: 
        #   Array: (0, length, address)
        #   Var:   (1, address)
        #   Val:   (2, value)
        if node.pcall.args.expr:
            for (i, x) in enumerate(node.pcall.args.expr):
                t = self.sem.sig.lookup_param_type(proc_name, i)

                # If the parameter type is an array reference
                if t.form == 'alias':

                    # Output the length of the array
                    q = self.sem.sig.lookup_array_qualifier(proc_name, i)
                    self.comment('alias')
                    self.out('_closure[{}] = t_arg_ALIAS;'.format(n)) ; n+=1
                    self.out('_closure[{}] = {};'.format(n,
                        self.expr(node.pcall.args.expr[q]))) ; n+=1
                   
                    # If the elem is a proper array, load the address
                    if x.elem.symbol.type.form == 'array':
                        tmp = self.blocker.get_tmp()
                        self.asm('mov %0, %1', outop=tmp, inops=[x.elem.name])
                        self.out('_closure[{}] = {};'.format(n, tmp)) ; n+=1
                    # Otherwise, just assign
                    if x.elem.symbol.type.form == 'alias':
                        self.out('_closure[{}] = {};'.format(n, self.expr(x))) ; n+=1
                
                # Otherwise, a var or val single
                elif t.form == 'single':

                    if t.specifier == 'var':
                        self.comment('var')
                        self.out('_closure[{}] = t_arg_VAR;'.format(n)) ; n+=1
                        tmp = self.blocker.get_tmp()
                        self.asm('mov %0, %1', outop=tmp,
                                inops=['('+x.elem.name+', unsigned[])'])
                        self.out('_closure[{}] = {};'.format(n, tmp)) ; n+=1
                    elif t.specifier == 'val':
                        self.comment('val')
                        self.out('_closure[{}] = t_arg_VAL;'.format(n)) ; n+=1
                        self.out('_closure[{}] = {};'.format(n, self.expr(x))) ; n+=1

        # Procedures: (jumpindex)*
        self.comment('Proc: parent '+proc_name)
        self.out('_closure[{}] = {};'.format(n, defs.JUMP_INDEX_OFFSET
                +self.sem.proc_names.index(proc_name))) ; n+=1
        for x in self.child.children[proc_name]:
            self.comment('Proc: child '+x)
            self.out('_closure[{}] = {};'.format(n, defs.JUMP_INDEX_OFFSET
                    +self.sem.proc_names.index(x))) ; n+=1

        # Call runtime TODO: length argument?
        self.out('{}({}, _closure);'.format(defs.LABEL_MIGRATE, 
            self.expr(node.core.expr)))

        self.blocker.end()

    def stmt_alias(self, node):
        """ Generate an alias statement. If the slice target is an array we must
            use some inline assembly to get xcc to load the address for us.
            Otherwise, we can just perform arithmetic on the pointer.
        """
        if node.symbol.type.form == 'array':
            self.asm('add %0, %1, %2', outop=node.name, 
                    inops=[node.slice.name, '({})*{}'.format(
                        self.expr(node.slice.begin), defs.BYTES_PER_WORD)])
        elif node.symbol.type.form == 'alias':
            self.out('{} = {} + ({})*{};'.format(node.name, node.slice.name, 
                self.expr(node.slice.begin), defs.BYTES_PER_WORD))

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

        # Otherwise, just return the regular syntax
        return self.elem(node.elem)

    def expr_unary(self, node):
        
        # If the elem is an alias subscript, generate a load
        if isinstance(node.elem, ast.ElemSub):
            if node.elem.symbol.type.form == 'alias':
                tmp = self.blocker.get_tmp()
                self.asm('ldw %0, %1[%2]', outop=tmp,
                        inops=[node.elem.name, self.expr(node.elem.expr)])
                return '({}{})'.format(node.op, tmp)
        
        # Otherwise, just return the regular syntax
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
        
        # Otherwise, just return the regular syntax
        return '{} {} {}'.format(self.elem(node.elem), 
                op_conversion[node.op], self.expr(node.right))
    
    # Elements= ===========================================

    def elem_group(self, node):
        return '({})'.format(self.expr(node.expr))

    def elem_sub(self, node):
        return '{}[{}]'.format(node.name, self.expr(node.expr))

    def elem_slice(self, node):
        # If source is an array take the address, if alias just the value
        address = ''+node.name
        if node.symbol.type.form == 'array':
            address = '(unsigned, '+address+')'
        return '({} + ({})*{})'.format(address, self.expr(node.begin),
               defs.BYTES_PER_WORD)

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

