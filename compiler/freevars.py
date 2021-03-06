# Copyright (c) 2011, James Hanlon, All rights reserved
# This software is freely distributable under a derivative of the
# University of Illinois/NCSA Open Source License posted in
# LICENSE.txt and at <http://github.xcore.com/>

from walker import NodeWalker
from typedefs import T_SCOPE_PROGRAM
import ast

class FreeVars(NodeWalker):
  """
  Calculate the set of free variables within a statement. This can be:
   - All definitions and uses.
   - All definitions.
   - All uses and definitions of array types only.

  Ignore values.
  """
  def __init__(self):
    pass

  def compute(self, node):
    return self.stmt(node)

  def remove_bound(self, c, decls):
    decl_elems = set()
    for x in decls:
      decl_elems.add(ast.ElemId(x.name))
    return c - decl_elems
  
  # Statements ==========================================

  # New scope

  def stmt_seq(self, node):
    c = set()
    [c.update(self.stmt(x)) for x in node.stmt]
    c = self.remove_bound(c, node.decls)
    return c

  def stmt_par(self, node):
    c = set()
    [c.update(self.stmt(x)) for x in node.stmt]
    c = self.remove_bound(c, node.decls)
    return c

  def stmt_server(self, node):
    c = self.stmt(node.server)
    c |= self.stmt(node.client)
    c = self.remove_bound(c, node.decls)
    return c

  # No new scope

  def stmt_skip(self, node):
    return set()

  def stmt_ass(self, node):
    c = self.elem(node.left)
    c |= self.expr(node.expr)
    return c

  def stmt_in(self, node):
    c = self.elem(node.left)
    c |= self.expr(node.expr)
    return c

  def stmt_out(self, node):
    c = self.elem(node.left)
    c |= self.expr(node.expr)
    return c

  def stmt_in_tag(self, node):
    c = self.elem(node.left)
    c |= self.expr(node.expr)
    return c

  def stmt_out_tag(self, node):
    c = self.elem(node.left)
    c |= self.expr(node.expr)
    return c

  def stmt_alias(self, node):
    c = self.elem(node.left)
    c |= self.elem(node.slice)
    return c

  def stmt_pcall(self, node):
    c = set()
    [c.update(self.expr(x)) for x in node.args]
    return c

  def stmt_if(self, node):
    c = self.expr(node.cond)
    c |= self.stmt(node.thenstmt)
    c |= self.stmt(node.elsestmt)
    return c

  def stmt_while(self, node):
    c = self.expr(node.cond)
    c |= self.stmt(node.stmt)
    return c

  def stmt_for(self, node):
    c = self.elem(node.index)
    c |= self.stmt(node.stmt)
    return c

  def stmt_rep(self, node):
    c = set()
    [c.update(self.elem(x)) for x in node.indices]
    c |= self.stmt(node.stmt)
    return c

  def stmt_connect(self, node):
    c = self.elem(node.left)
    if node.expr:
      c |= self.expr(node.expr)
    return c

  def stmt_on(self, node):
    c = self.expr(node.expr)
    c |= self.stmt(node.stmt)
    return c

  def stmt_assert(self, node):
    return self.expr(node.expr)
  
  def stmt_return(self, node):
    return self.expr(node.expr)
  
  # Expressions =========================================

  def expr_single(self, node):
    return self.elem(node.elem)

  def expr_unary(self, node):
    return self.elem(node.elem)

  def expr_binop(self, node):
    c = self.elem(node.elem)
    c |= self.expr(node.right)
    return c
  
  # Elements= ===========================================

  # Identifier
  def elem_id(self, node):
    # Only use it if it's not a value symbol.
    if node.symbol!=None and node.symbol.scope!=T_SCOPE_PROGRAM:
      return set([node])
    else:
      return set()

  # Array subscript
  def elem_sub(self, node):
    c = self.expr(node.expr)
    return c | set([node])

  # Array slice
  def elem_slice(self, node):
    c = self.expr(node.base)
    c |= self.expr(node.count)
    return c | set([node])

  # Index
  def elem_index_range(self, node):
    c = self.expr(node.base)
    c |= self.expr(node.count)
    return c | set([node])

  def elem_group(self, node):
    return self.expr(node.expr)

  def elem_fcall(self, node):
    c = set()
    [c.update(self.expr(x)) for x in node.args]
    return c

  def elem_number(self, node):
    return set()

  def elem_boolean(self, node):
    return set()

  def elem_string(self, node):
    return set()

  def elem_char(self, node):
    return set()


