# Copyright (c) 2011, James Hanlon, All rights reserved
## This software is freely distributable under a derivative of the
## University of Illinois/NCSA Open Source License posted in
## LICENSE.txt and at <http://github.xcore.com/>

import sys
import copy
import collections
from itertools import product

import ast
from walker import NodeWalker
from typedefs import *
from subelem import SubElem
from evalexpr import EvalExpr

from printer import Printer

class LabelChans(NodeWalker):
  """
  A template recursive descent AST NodeWalker.
  """
  def __init__(self):
    pass

  def expand_channel(self, i, stmt, elem):
    """
    Expand the use of a channel subscript over a set of iterators.
    """
    #print(Printer().expr(elem.expr))
    #print(Printer().expr(stmt.location))
    ranges = [range(x.base_value, x.base_value+x.count_value) for x in i]
    for x in product(*ranges):
      index_expr = copy.deepcopy(elem.expr)
      locat_expr = copy.deepcopy(stmt.location)
      for (y, z) in zip(i, x):
        index_expr.accept(SubElem(ast.ElemId(y.name), ast.ElemNumber(z)))
        locat_expr.accept(SubElem(ast.ElemId(y.name), ast.ElemNumber(z)))
      #print(Printer().expr(locat_expr))
      index_value = EvalExpr().expr(index_expr)
      locat_value = EvalExpr().expr(locat_expr)
      print('  {}[{}] at {}'.format(elem.name, index_value, locat_value))

  # Program ============================================

  def walk_program(self, node):
    #[self.decl(x) for x in node.decls]
    [self.defn(x) for x in node.defs]
  
  # Procedure definitions ===============================

  def defn(self, node):
    #[self.decl(x) for x in node.decls]
    self.stmt(node.stmt, [])
  
  # Statements ==========================================

  # Statements containing uses of channels

  def stmt_in(self, node, i):
    print('? channel {}:'.format(node.left.name))
    if isinstance(node.left, ast.ElemSub):
      self.expand_channel(i, node, node.left)
    elif isinstance(node.left, ast.ElemId):
      assert 0

  def stmt_out(self, node, i):
    print('! channel {}:'.format(node.left.name))
    if isinstance(node.left, ast.ElemSub):
      self.expand_channel(i, node, node.left)
    elif isinstance(node.left, ast.ElemId):
      assert 0

  def stmt_pcall(self, node, i):
    for x in node.args:
      if (isinstance(x, ast.ExprSingle) 
          and isinstance(x.elem, ast.ElemSub)
          and x.elem.symbol.type == T_CHAN_ARRAY):
        print('arg channel {}:'.format(x.elem.name))
        self.expand_channel(i, node, x.elem)
    
  # Statements containing processes

  def stmt_rep(self, node, i):
    self.stmt(node.stmt, i + node.indicies)
  
  def stmt_seq(self, node, i):
    [self.stmt(x, i) for x in node.stmt]

  def stmt_par(self, node, i):
    [self.stmt(x, i) for x in node.stmt]

  def stmt_if(self, node, i):
    self.stmt(node.thenstmt, i)
    self.stmt(node.elsestmt, i)

  def stmt_while(self, node, i):
    self.stmt(node.stmt, i)

  def stmt_for(self, node, i):
    self.stmt(node.stmt, i)

  # Statements not containing processes or channels uses

  def stmt_ass(self, node, i):
    pass

  def stmt_alias(self, node, i):
    pass

  def stmt_skip(self, node, i):
    pass

  def stmt_return(self, node, i):
    pass

  # Prohibited statements

  def stmt_on(self, node, i):
    assert 0

  def stmt_connect(self, node, i):
    assert 0

