# Copyright (c) 2011, James Hanlon, All rights reserved
# This software is freely distributable under a derivative of the
# University of Illinois/NCSA Open Source License posted in
# LICENSE.txt and at <http://github.xcore.com/>

from walker import NodeWalker
from cmpexpr import CmpExpr
from symbol import Symbol
from typedefs import *
import ast

from printer import Printer

class RenameChans(NodeWalker):
  """
  Rename channel variables with their new channel end and remove all channel
  declarations.
  """
  def __init__(self):
    pass

  def rename_chan(self, elem, chans):
    """
    Rename a channel (elem) using the set of channel elements (ChanElemSet)
    which will contain the name of the channel end allocated to this instance. 
    """
    if isinstance(elem, ast.ElemId) and elem.symbol.type == T_CHAN_SINGLE:
      for x in chans:
        if elem.name == x.name:
          s = Symbol(x.chanend, T_CHANEND_SINGLE, T_SCOPE_PROC)
          e = ast.ElemId(x.chanend)
          e.symbol = s
          return ast.ExprSingle(e)

    elif isinstance(elem, ast.ElemSub) and elem.symbol.type == T_CHAN_ARRAY:
      for x in chans:
        if elem.name == x.name and CmpExpr().expr(elem.expr, x.expr):
          s = Symbol(x.chanend, T_CHANEND_SINGLE, T_SCOPE_PROC)
          e = ast.ElemId(x.chanend)
          e.symbol = s
          return ast.ExprSingle(e)
    else:
      assert 0

  def remove_chan_decls(self, decls):
    """
    Remove any single or array channel declarations from a list.
    """
    new_decls = []
    for x in decls:
      if not (x.type == T_CHAN_SINGLE or x.type == T_CHAN_ARRAY):
        new_decls.append(x)
    return new_decls

  # Program ============================================

  def walk_program(self, node):
    [self.defn(x) for x in node.defs]
  
  # Procedure definitions ===============================

  def defn(self, node):
    node.decls = self.remove_chan_decls(node.decls)
    self.stmt(node.stmt, node.chans)
  
  # Statements ==========================================

  # Statements with channel 'boundaries'

  def stmt_rep(self, node, chans):
    self.stmt(node.stmt, node.chans)
    
  def stmt_par(self, node, chans):
    [self.stmt(x, y) for (x, y) in zip(node.stmt, node.chans)]

  def stmt_seq(self, node, chans):
    [self.stmt(x, chans) for x in node.stmt]

  # Statements containing uses of channels

  def stmt_in(self, node, chans):
    c = node.left
    t = c.symbol.type
    if ((isinstance(c, ast.ElemId) and t == T_CHAN_SINGLE)
        or (isinstance(c, ast.ElemSub) and t == T_CHAN_ARRAY)):
      node.left = self.rename_chan(c, chans)

  def stmt_out(self, node, chans):
    c = node.left
    t = c.symbol.type
    if ((isinstance(c, ast.ElemId) and t == T_CHAN_SINGLE)
        or (isinstance(c, ast.ElemSub) and t == T_CHAN_ARRAY)):
      node.left = self.rename_chan(c, chans)

  def stmt_pcall(self, node, chans):
    for (i, x) in enumerate(node.args):
      if isinstance(x, ast.ExprSingle):

        if (isinstance(x.elem, ast.ElemId)
            and x.elem.symbol.type == T_CHAN_SINGLE):
          node.args[i] = self.rename_chan(x.elem, chans)

        elif (isinstance(x.elem, ast.ElemSub)
            and x.elem.symbol.type == T_CHAN_ARRAY):
          node.args[i] = self.rename_chan(x.elem, chans)
  
  # Other statements containing statements

  def stmt_if(self, node, chans):
    self.stmt(node.thenstmt, chans)
    self.stmt(node.elsestmt, chans)

  def stmt_while(self, node, chans):
    self.stmt(node.stmt, chans)

  def stmt_for(self, node, chans):
    self.stmt(node.stmt, chans)

  def stmt_on(self, node, chans):
    self.stmt(node.stmt, chans)

  # Statements we can ignore

  def stmt_alias(self, node, chans):
    pass

  def stmt_connect(self, node, chans):
    pass

  def stmt_return(self, node, chans):
    pass

  def stmt_ass(self, node, chans):
    pass

  def stmt_skip(self, node, chans):
    pass
