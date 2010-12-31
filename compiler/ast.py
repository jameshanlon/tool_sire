#-----------------------------------------------------------------
# ** ATTENTION **
# This code was automatically generated from the file:
# ast.cfg 
#
# Do not modify it directly. Modify the configuration file and
# run the generator again.
#-----------------------------------------------------------------

import sys

class Node(object):
    """ Abstract base class for AST nodes.
    """
    def children(self):
        """ A sequence of all children that are Nodes
        """
        pass

    def accept(self, visitor):
        """ Accept a visitor
        """
        pass


class NodeVisitor(object):
    """ Generic Node visitor base class to be subclassed
    """
    pass

class Program(Node):
    def __init__(self, decls, defs, coord=None):
        self.decls = decls
        self.defs = defs
        self.coord = coord

    def children(self):
        c = []
        if self.decls is not None: c.append(self.decls)
        if self.defs is not None: c.append(self.defs)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_program(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'Program('
        s += ')'
        return s

class Decls(Node):
    def __init__(self, decl, coord=None):
        self.decl = decl
        self.coord = coord

    def children(self):
        c = []
        if self.decl is not None: c.extend(self.decl)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_decls(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'Decls('
        s += ')'
        return s

class DeclSingle(Node):
    def __init__(self, name, type, form, expr, coord=None):
        self.name = name
        self.type = type
        self.form = form
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_decl_single(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'DeclSingle('
        s += ', '.join('%s' % v for v in [self.type, self.form])
        s += ')'
        return s

class DeclArray(Node):
    def __init__(self, name, type, form, expr, coord=None):
        self.name = name
        self.type = type
        self.form = form
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_decl_array(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'DeclArray('
        s += ', '.join('%s' % v for v in [self.type, self.form])
        s += ')'
        return s

class DeclVal(Node):
    def __init__(self, name, type, form, expr, coord=None):
        self.name = name
        self.type = type
        self.form = form
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_decl_val(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'DeclVal('
        s += ', '.join('%s' % v for v in [self.type, self.form])
        s += ')'
        return s

class DeclPort(Node):
    def __init__(self, name, type, form, expr, coord=None):
        self.name = name
        self.type = type
        self.form = form
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_decl_port(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'DeclPort('
        s += ', '.join('%s' % v for v in [self.type, self.form])
        s += ')'
        return s

class Defs(Node):
    def __init__(self, decl, coord=None):
        self.decl = decl
        self.coord = coord

    def children(self):
        c = []
        if self.decl is not None: c.extend(self.decl)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_defs(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'Defs('
        s += ')'
        return s

class DefProc(Node):
    def __init__(self, name, formals, vardecls, stmt, coord=None):
        self.name = name
        self.formals = formals
        self.vardecls = vardecls
        self.stmt = stmt
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.formals is not None: c.append(self.formals)
        if self.vardecls is not None: c.append(self.vardecls)
        if self.stmt is not None: c.append(self.stmt)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_def_proc(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'DefProc('
        s += ')'
        return s

class DefFunc(Node):
    def __init__(self, name, formals, vardecls, stmt, coord=None):
        self.name = name
        self.formals = formals
        self.vardecls = vardecls
        self.stmt = stmt
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.formals is not None: c.append(self.formals)
        if self.vardecls is not None: c.append(self.vardecls)
        if self.stmt is not None: c.append(self.stmt)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_def_func(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'DefFunc('
        s += ')'
        return s

class Formals(Node):
    def __init__(self, params, coord=None):
        self.params = params
        self.coord = coord

    def children(self):
        c = []
        if self.params is not None: c.extend(self.params)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_formals(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'Formals('
        s += ')'
        return s

class ParamVar(Node):
    def __init__(self, name, type, form, coord=None):
        self.name = name
        self.type = type
        self.form = form
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_param_var(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ParamVar('
        s += ', '.join('%s' % v for v in [self.name, self.type, self.form])
        s += ')'
        return s

class ParamAlias(Node):
    def __init__(self, name, type, form, coord=None):
        self.name = name
        self.type = type
        self.form = form
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_param_alias(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ParamAlias('
        s += ', '.join('%s' % v for v in [self.name, self.type, self.form])
        s += ')'
        return s

class ParamVal(Node):
    def __init__(self, name, type, form, coord=None):
        self.name = name
        self.type = type
        self.form = form
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_param_val(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ParamVal('
        s += ', '.join('%s' % v for v in [self.name, self.type, self.form])
        s += ')'
        return s

class ParamChanend(Node):
    def __init__(self, name, type, form, coord=None):
        self.name = name
        self.type = type
        self.form = form
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_param_chanend(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ParamChanend('
        s += ', '.join('%s' % v for v in [self.name, self.type, self.form])
        s += ')'
        return s

class StmtSeq(Node):
    def __init__(self, stmt, coord=None):
        self.stmt = stmt
        self.coord = coord

    def children(self):
        c = []
        if self.stmt is not None: c.extend(self.stmt)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_seq(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtSeq('
        s += ')'
        return s

class StmtPar(Node):
    def __init__(self, stmt, coord=None):
        self.stmt = stmt
        self.coord = coord

    def children(self):
        c = []
        if self.stmt is not None: c.extend(self.stmt)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_par(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtPar('
        s += ')'
        return s

class StmtSkip(Node):
    def __init__(self, coord=None):
        self.coord = coord

    def children(self):
        return ()

    def accept(self, visitor):
        tag = visitor.visit_stmt_skip(self)
        visitor.down(tag)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtSkip('
        s += ')'
        return s

class StmtPcall(Node):
    def __init__(self, name, args, coord=None):
        self.name = name
        self.args = args
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.args is not None: c.append(self.args)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_pcall(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtPcall('
        s += ')'
        return s

class StmtAss(Node):
    def __init__(self, left, expr, coord=None):
        self.left = left
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.left is not None: c.append(self.left)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_ass(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtAss('
        s += ')'
        return s

class StmtIn(Node):
    def __init__(self, left, expr, coord=None):
        self.left = left
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.left is not None: c.append(self.left)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_in(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtIn('
        s += ')'
        return s

class StmtOut(Node):
    def __init__(self, left, expr, coord=None):
        self.left = left
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.left is not None: c.append(self.left)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_out(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtOut('
        s += ')'
        return s

class StmtIf(Node):
    def __init__(self, cond, thenstmt, elsestmt, coord=None):
        self.cond = cond
        self.thenstmt = thenstmt
        self.elsestmt = elsestmt
        self.coord = coord

    def children(self):
        c = []
        if self.cond is not None: c.append(self.cond)
        if self.thenstmt is not None: c.append(self.thenstmt)
        if self.elsestmt is not None: c.append(self.elsestmt)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_if(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtIf('
        s += ')'
        return s

class StmtWhile(Node):
    def __init__(self, cond, stmt, coord=None):
        self.cond = cond
        self.stmt = stmt
        self.coord = coord

    def children(self):
        c = []
        if self.cond is not None: c.append(self.cond)
        if self.stmt is not None: c.append(self.stmt)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_while(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtWhile('
        s += ')'
        return s

class StmtFor(Node):
    def __init__(self, var, init, bound, stmt, coord=None):
        self.var = var
        self.init = init
        self.bound = bound
        self.stmt = stmt
        self.coord = coord

    def children(self):
        c = []
        if self.var is not None: c.append(self.var)
        if self.init is not None: c.append(self.init)
        if self.bound is not None: c.append(self.bound)
        if self.stmt is not None: c.append(self.stmt)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_for(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtFor('
        s += ')'
        return s

class StmtOn(Node):
    def __init__(self, core, pcall, coord=None):
        self.core = core
        self.pcall = pcall
        self.coord = coord

    def children(self):
        c = []
        if self.core is not None: c.append(self.core)
        if self.pcall is not None: c.append(self.pcall)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_on(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtOn('
        s += ')'
        return s

class StmtConnect(Node):
    def __init__(self, left, core, dest, coord=None):
        self.left = left
        self.core = core
        self.dest = dest
        self.coord = coord

    def children(self):
        c = []
        if self.left is not None: c.append(self.left)
        if self.core is not None: c.append(self.core)
        if self.dest is not None: c.append(self.dest)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_connect(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtConnect('
        s += ')'
        return s

class StmtAliases(Node):
    def __init__(self, left, name, expr, coord=None):
        self.left = left
        self.name = name
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.left is not None: c.append(self.left)
        if self.name is not None: c.append(self.name)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_aliases(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtAliases('
        s += ')'
        return s

class StmtReturn(Node):
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_stmt_return(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'StmtReturn('
        s += ')'
        return s

class ExprList(Node):
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.expr is not None: c.extend(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_expr_list(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ExprList('
        s += ')'
        return s

class ExprSingle(Node):
    def __init__(self, elem, coord=None):
        self.elem = elem
        self.coord = coord

    def children(self):
        c = []
        if self.elem is not None: c.append(self.elem)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_expr_single(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ExprSingle('
        s += ')'
        return s

class ExprUnary(Node):
    def __init__(self, op, elem, coord=None):
        self.op = op
        self.elem = elem
        self.coord = coord

    def children(self):
        c = []
        if self.elem is not None: c.append(self.elem)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_expr_unary(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ExprUnary('
        s += ', '.join('%s' % v for v in [self.op])
        s += ')'
        return s

class ExprBinop(Node):
    def __init__(self, op, elem, right, coord=None):
        self.op = op
        self.elem = elem
        self.right = right
        self.coord = coord

    def children(self):
        c = []
        if self.elem is not None: c.append(self.elem)
        if self.right is not None: c.append(self.right)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_expr_binop(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ExprBinop('
        s += ', '.join('%s' % v for v in [self.op])
        s += ')'
        return s

class ElemGroup(Node):
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_elem_group(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ElemGroup('
        s += ')'
        return s

class ElemSub(Node):
    def __init__(self, name, expr, coord=None):
        self.name = name
        self.expr = expr
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.expr is not None: c.append(self.expr)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_elem_sub(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ElemSub('
        s += ')'
        return s

class ElemFcall(Node):
    def __init__(self, name, args, coord=None):
        self.name = name
        self.args = args
        self.coord = coord

    def children(self):
        c = []
        if self.name is not None: c.append(self.name)
        if self.args is not None: c.append(self.args)
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_elem_fcall(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ElemFcall('
        s += ')'
        return s

class ElemNumber(Node):
    def __init__(self, value, coord=None):
        self.value = value
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_elem_number(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ElemNumber('
        s += ', '.join('%s' % v for v in [self.value])
        s += ')'
        return s

class ElemBoolean(Node):
    def __init__(self, value, coord=None):
        self.value = value
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_elem_boolean(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ElemBoolean('
        s += ', '.join('%s' % v for v in [self.value])
        s += ')'
        return s

class ElemString(Node):
    def __init__(self, value, coord=None):
        self.value = value
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_elem_string(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ElemString('
        s += ', '.join('%s' % v for v in [self.value])
        s += ')'
        return s

class ElemChar(Node):
    def __init__(self, value, coord=None):
        self.value = value
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_elem_char(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ElemChar('
        s += ', '.join('%s' % v for v in [self.value])
        s += ')'
        return s

class ElemId(Node):
    def __init__(self, value, coord=None):
        self.value = value
        self.coord = coord

    def children(self):
        c = []
        return tuple(c)

    def accept(self, visitor):
        tag = visitor.visit_elem_id(self)
        visitor.down(tag)
        for c in self.children():
            c.accept(visitor)
        visitor.up(tag)

    def __repr__(self):
        s =  'ElemId('
        s += ', '.join('%s' % v for v in [self.value])
        s += ')'
        return s

