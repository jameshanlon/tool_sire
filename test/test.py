# Copyright (c) 2011, James Hanlon, All rights reserved
# This software is freely distributable under a derivative of the
# University of Illinois/NCSA Open Source License posted in
# LICENSE.txt and at <http://github.xcore.com/>

from util import read_file

class Test(object):
  """ 
  A generic test object with a list (of system sizes) for specific tests.
  """
  def __init__(self, name, cores=[1], cmp_flags=[]):
    self.name = name
    self.cores = cores

