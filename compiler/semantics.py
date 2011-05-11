# Copyright (c) 2011, James Hanlon, All rights reserved
# This software is freely distributable under a derivative of the
# University of Illinois/NCSA Open Source License posted in
# LICENSE.txt and at <http://github.xcore.com/>

import sys

import error
import util
import definitions as defs

import ast
from walker import NodeWalker
import symbol
import signature
from builtin import builtins
from type import Type

elem_types = {
  'elem_sub'     : None,
  'elem_id'      : None,
  'elem_group'   : None,
  'elem_fcall'   : Type('var', 'single'),
  'elem_string'  : Type('var', 'array'),
  'elem_number'  : Type('val', 'single'),
  'elem_boolean' : Type('val', 'single'),
  'elem_char'    : Type('val', 'single'),
  }

class Semantics(NodeWalker):
    """ An AST visitor class to check the semantics of a sire program
    """
    def __init__(self, error):
        self.depth = 0
        self.error = error
        
        # Data structures
        self.sym = symbol.SymbolTable(self, debug=False)
        self.sig = signature.SignatureTable(self, debug=False)
        self.proc_names = []

        # Initialise variables in the 'system' scope
        
        # Add system variables core, chan
        self.sym.begin_scope('system')
        self.sym.insert(defs.SYS_CORE_ARRAY, Type('core', 'array'))
        self.sym.insert(defs.SYS_NUM_CORES_CONST, Type('val', 'single'))

        # Add all mobile builtin functions
        for x in builtins.values():
            self.sym.insert(x.definition.name, x.definition.type)
            self.sig.insert(x.definition.type, x.definition)
            if x.mobile:
                self.proc_names.append(x.definition.name)

    def get_elem_type(self, elem):
        """ Given an element, return its type
        """
        
        # If its an expression group, get_expr_type
        if isinstance(elem, ast.ElemGroup):
            return self.get_expr_type(elem.expr)
        
        # If its a single identifer, look it up (if it exists)
        elif isinstance(elem, ast.ElemId):
            s = self.sym.lookup(elem.name)
            if s: 
                return s.type
            else:
                self.nodecl_error(elem.name, 'single', None)
                return None
        
        # If its a subscripted identifier, lookup and return subscripted type
        elif isinstance(elem, ast.ElemSub):
            s = self.sym.lookup(elem.name)
            if s:
                return s.type.subscriptOf()
            else:
                self.nodecl_error(elem.name, 'array', None)
                return None

        # If it is an array slice
        elif isinstance(elem, ast.ElemSlice):
            s = self.sym.lookup(elem.name)
            if s:
                return s.type
            else:
                self.nodecl_error(elem.name, 'array', None)
                return None

        # Otherwise, return the specified elem type
        else:
            return elem_types[util.camel_to_under(elem.__class__.__name__)]

    def get_expr_type(self, expr):
        """ Given an expression work out its type
        """
        
        #If it's a single value, lookup the type
        if isinstance(expr, ast.ExprSingle):
            return self.get_elem_type(expr.elem)    
        
        # Otherwise it must be a unary or binop, and hence a var
        return Type('var', 'single')

    def check_elem_types(self, elem, types):
        """ Given an elem and a set of types, check if one matches
        """
        t = self.get_elem_type(elem)
        return True if t and any([x==t for x in types]) else False

    # Errors and warnings =================================

    def nodecl_error(self, name, specifier, coord):
        """ No declaration error
        """
        self.error.report_error("{} '{}' not declared"
                .format(specifier, name), coord)

    def badargs_error(self, name, coord):
        """ No definition error 
        """
        self.error.report_error("invalid arguments for procedure '{}' "
                .format(name), coord)

    def redecl_error(self, name, coord):
        """ Re-declaration error 
        """
        self.error.report_error("variable '{}' already declared in scope"
                .format(name), coord)

    def redef_error(self, name, coord):
        """ Re-definition error 
        """
        self.error.report_error("procedure '{}' already declared"
                .format(name), coord)

    def procedure_def_error(self, name, coord):
        """ Re-definition error 
        """
        self.error.report_error("procedure '{}' definition invalid"
                .format(name), coord)

    def unused_warning(self, name, coord):
        """ Unused variable warning
        """
        self.error.report_warning("variable '{}' declared but not used"
                .format(name), coord)

    def type_error(self, msg, name, coord):
        """ Mismatching type error
        """
        self.error.report_error("type error in {} with '{}'".format(msg, name), coord)

    def form_error(self, msg, name, coord):
        """ Mismatching form error
        """
        self.error.report_error("form error in {} with '{}'"
                .format(msg, name), coord)

    # Program ============================================

    def walk_program(self, node):
        self.sym.begin_scope('program')
        self.decls(node.decls)
        self.defs(node.defs)
        self.sym.end_scope()
    
    # Variable declarations ===============================

    def decls(self, node):
        [self.decl(x) for x in node.children()]

    def decl(self, node):
        if not self.sym.insert(node.name, node.type, node.coord):
            self.redecl_error(node.name, node.coord)

    # Procedure definitions ===============================

    def defs(self, node):
        [self.defn(x) for x in node.children()]

    def defn(self, node):
        
        # Rename main to avoid conflicts in linking
        if node.name == 'main':
            node.name = '_'+node.name

        # Add symbol and signature
        if self.sym.insert(node.name, node.type, node.coord):
            if not self.sig.insert(node.type, node):
                self.procedure_def_error(node.name, node.coord)
        else:
            self.redecl_error(node.name, node.coord)

        # Add the procedure name to the list
        self.proc_names.append(node.name)
        self.parent = node.name
    
        # Begin a new scope for decls and stmt components
        self.sym.begin_scope('proc')
        self.formals(node.formals)
        self.decls(node.decls)
        self.stmt(node.stmt)
        self.sym.end_scope()
    
    # Formals =============================================
    
    def formals(self, node):
        [self.param(x) for x in node.children()]

    def param(self, node):
       
        if not self.sym.insert(node.name, node.type, node.coord):
            self.redecl_error(node.name, node.coord)

        # TODO: For alias parameters, check expr is composed of param values
        if node.type.form == 'alias':
            pass
            #if not self.get_expr_type(node.expr).form == 'alias'

    # Statements ==========================================

    def stmt_seq(self, node):
        [self.stmt(x) for x in node.children()]

    def stmt_par(self, node):
        [self.stmt(x) for x in node.children()]

    def stmt_skip(self, node):
        pass

    def stmt_pcall(self, node):
        
        # Check the name is declared
        if not self.sym.check_decl(node.name):
            self.nodecl_error(node.name, 'process', node.coord)
        
        else:
            # Check the arguments are correct
            if not self.sig.check_args('proc', node):
                self.badargs_error(node.name, node.coord)
            
            # And mark the symbol as used
            self.sym.mark_decl(node.name)

        # Children
        [self.expr(x) for x in node.args.expr]

    def stmt_ass(self, node):

        # Check valid type for assignment target
        if not self.check_elem_types(node.left, [
               Type('val', 'single'), 
               Type('var', 'single'), 
               Type('val', 'sub'),
               Type('var', 'sub')]):
            self.type_error('assignment', node.left.name, node.coord)

        # Children
        self.elem(node.left)
        self.expr(node.expr)

    def stmt_alias(self, node):

        if not self.sym.check_form(node.name, ['alias']):
            self.type_error('alias', node.dest, node.coord)
        else:
            node.symbol = self.sym.lookup(node.name)
            self.sym.mark_decl(node.name)
        
        if not self.sym.check_form(node.slice.name, ['var', 'alias', 'array']):
            self.type_error('alias', node.slice.name, node.coord)

        # Children
        self.expr(node.slice)

    def stmt_if(self, node):

        # Children
        self.expr(node.cond)
        self.stmt(node.thenstmt)
        self.stmt(node.elsestmt)

    def stmt_while(self, node):

        # Children
        self.expr(node.cond)
        self.stmt(node.stmt)

    def stmt_for(self, node):
        
        if not self.check_elem_types(node.var, [Type('var', 'single')]):
            self.type_error('for loop index variable', node.var.name, node.coord)

        # Children
        self.elem(node.var)
        self.expr(node.init)
        self.expr(node.bound)
        self.expr(node.step)
        self.stmt(node.stmt)

    def stmt_rep(self, node):
        
        if not self.check_elem_types(node.var, [Type('var', 'single')]):
            self.type_error('repliacator index variable', node.var.name, node.coord)
        
        # Children
        self.elem(node.var)
        self.expr(node.init)
        self.expr(node.count)
        self.elem(node.pcall)

    def stmt_on(self, node):
        if not self.check_elem_types(node.core, [Type('core', 'sub')]):
            self.type_error('on target', node.core, node.coord)

        # Children
        self.elem(node.pcall)

    def stmt_return(self, node):
        
        # Children
        self.expr(node.expr)

    # Expressions =========================================

    # TODO: check ops only act on vars

    def expr_list(self, node):
        [self.expr(x) for x in node.children()]

    def expr_single(self, node):
        #if not self.check_elem_types(node.elem, 
        #        [Type('var', 'single'), Type('var', 'sub')]):
        #    self.type_error('single', node.elem, node.coord)
       
        # Children
        self.elem(node.elem)

    def expr_unary(self, node):
        if not self.check_elem_types(node.elem, [
                Type('var', 'single'), 
                Type('var', 'sub'), 
                Type('val', 'single'),
                ]):
            self.type_error('unary', node.elem, node.coord)

        # Children
        self.elem(node.elem)

    def expr_binop(self, node):
        if not self.check_elem_types(node.elem, [
                Type('val', 'single'),
                Type('var', 'single'), 
                Type('var', 'array'), 
                Type('val', 'sub'), 
                Type('var', 'sub')]):
            self.type_error('binop dest', node.elem, node.coord)
       
        # Children
        self.elem(node.elem)
        self.expr(node.right)
    
    # Elements= ===========================================

    def elem_group(self, node):
        
        # Children
        self.expr(node.expr)

    def elem_id(self, node):
        # Check the symbol has been declared
        if not self.sym.check_decl(node.name):
            self.nodecl_error(node.name, 'variable', node.coord)
        # Mark it as used if it has and link to the symbol
        else:
            node.symbol = self.sym.lookup(node.name)
            self.sym.mark_decl(node.name)
        # Check it has the right form
        #if not self.sym.check_form(node.name, ['single']):
        #    self.form_error('single', node.name, node.coord)

    def elem_sub(self, node):
        # Check the symbol has been declared
        if not self.sym.check_decl(node.name):
            self.nodecl_error(node.name, 'array or alias', node.coord)
        # Mark it as used if it has and link to the symbol
        else:
            node.symbol = self.sym.lookup(node.name)
            self.sym.mark_decl(node.name)
        # Check it has the right form 
        #if not self.sym.check_form(node.name, ['array','alias']):
        #    self.form_error('subscript', node.name, node.coord)
        
        # Children
        self.expr(node.expr)

    def elem_slice(self, node):
        
        # Check the symbol has been declared
        if not self.sym.check_decl(node.name):
            self.nodecl_error(node.name, 'array or alias', node.coord)
        # Mark it as used if it has and link to the symbol
        else:
            node.symbol = self.sym.lookup(node.name)
            self.sym.mark_decl(node.name)
        
        # Children
        self.expr(node.begin)
        self.expr(node.end)

    def elem_pcall(self, node):
        
        # Check the name is declared
        if not self.sym.check_decl(node.name):
            self.nodecl_error(node.name, 'process', node.coord)
        else:
            # Check the arguments are correct
            if not self.sig.check_args('proc', node):
                self.badargs_error(node.name, node.coord)
            # And mark the symbol as used
            self.sym.mark_decl(node.name)
        
        # Children
        self.expr(node.args)

    def elem_fcall(self, node):
        
        # Check the name is declared
        if not self.sym.check_decl(node.name):
            self.nodecl_error(node.name, 'function', node.coord)
        else:
            # Check the arguments are correct
            if not self.sig.check_args('func', node):
                self.badargs_error(node.name, node.coord)
            # And mark the symbol as used
            self.sym.mark_decl(node.name)

        # Children
        self.expr(node.args)

    def elem_number(self, node):
        pass

    def elem_boolean(self, node):
        pass

    def elem_string(self, node):
        pass

    def elem_char(self, node):
        pass

