# Copyright (c) 2011, James Hanlon, All rights reserved
# This software is freely distributable under a derivative of the
# University of Illinois/NCSA Open Source License posted in
# LICENSE.txt and at <http://github.xcore.com/>

import sys
import os

INSTALL_PATH_ENV = 'SIRE_INSTALL_PATH'

def init():
    """ Initialise configuration variables.
    """
    global INSTALL_PATH
    INSTALL_PATH = os.environ[INSTALL_PATH_ENV]

    if INSTALL_PATH:
        init_paths()
    else:
        raise Exception("no '"+INSTALL_PATH_env+"' enviromnent variable")

def init_paths():
    """ Initialise various paths.
    """
    globals()['INCLUDE_PATH'] = INSTALL_PATH+'/include'
    globals()['XS1_DEVICE_PATH']  = INSTALL_PATH+'/target/xs1/devices'
    globals()['XS1_RUNTIME_PATH'] = INSTALL_PATH+'/src/runtime/target/xs1'
    globals()['MPI_RUNTIME_PATH'] = INSTALL_PATH+'/src/runtime/target/mpi'
    