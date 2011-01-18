import sys
import os
import io
import util
import glob
import subprocess
from math import floor

RUNTIME_DIR    = 'runtime'
INCLUDE_DIR    = 'include'
CONFIGS_DIR    = 'configs'
NUMCORES_HDR   = 'numcores.h'
PROGRAM        = 'program'
PROGRAM_SRC    = 'program.xc'
PROGRAM_ASM    = 'program.S'
PROGRAM_OBJ    = 'program.o'
MASTER_JUMPTAB = 'masterjumptab'
MASTER_SIZETAB = 'mastersizetab'
MASTER_XE      = 'master.xe'
SLAVE_XE       = 'slave.xe'

XCC            = 'xcc'
XAS            = 'xas'
XOBJDUMP       = 'xobjdump'
COMPILE_FLAGS  = ['-S', '-O2']
ASSEMBLE_FLAGS = ['-c', '-O2']
LINK_FLAGS     = ['-nostartfiles', '-Xmapper', '--nochaninit']

CORES_PER_NODE = 4

RUNTIME_FILES = ['guest.xc', 'host.S', 'host.xc', 'master.S', 'master.xc', 
'slave.S', 'slavejumptab.S', 'system.S', 'system.xc', 'util.xc']

JUMP_TABLE = 'jumpTable'
SIZE_TABLE = 'sizeTable'
NUM_RUNTIME_ENTRIES = 3
JUMP_TABLE_SIZE = 10
BYTES_PER_WORD = 4

# TODO: read all these from definitions fil
# TODO: fix top and bottom function labels

LBL_MIGRATE     = 'migrate'
LBL_INIT_THREAD = 'initThread'
LBL_CONNECT     = 'connect'

class Build(object):
    """ A class to compile, assemble and link the program source with the
        runtime into an executable multi-core binary.
    """
    def __init__(self, numcores, semantics, verbose=False):
        self.numcores = numcores
        self.sem = semantics
        self.verbose = verbose

    def run(self, program_buf, outfile):
        """ Run the full build
        """
        e = False

        # Output the master jump and size tables
        jumptab_buf = io.StringIO()
        sizetab_buf = io.StringIO()
        self.build_jumptab(jumptab_buf)
        self.build_sizetab(sizetab_buf)
        
        self.create_headers()
        if not e: e = self.compile_buf(PROGRAM, program_buf)
        if not e: 
            program_buf.close()
            program_buf = io.StringIO()
            self.insert_labels(PROGRAM_ASM, program_buf)
        if not e: e = self.assemble_buf(PROGRAM, 'S', program_buf)
        if not e: e = self.assemble_buf(MASTER_JUMPTAB, 'S', jumptab_buf)
        if not e: e = self.assemble_buf(MASTER_SIZETAB, 'S', sizetab_buf)
        if not e: e = self.assemble_runtime()
        if not e: e = self.link_master()
        if not e: e = self.link_slave()
        if not e: e = self.replace_slaves()
        self.cleanup(outfile)

    def compile(self, buf, outfile):
        """ Compile the program only
        """
        self.compile_buf(PROGRAM, buf)
        buf.close()
        buf = io.StringIO()
        self.insert_labels(PROGRAM_ASM, buf)
        util.write_file(PROGRAM_ASM, buf.getvalue())
        os.rename(PROGRAM_ASM, outfile)

    def create_headers(self):
        self.verbose_msg('Creating header '+NUMCORES_HDR)
        util.write_file(INCLUDE_DIR+'/'+NUMCORES_HDR, 
                '#define NUM_CORES {}'.format(self.numcores));

    def compile_buf(self, name, buf, cleanup=True):
        """ Compile a buffer containing an XC program
        """
        srcfile = name + '.xc'
        outfile = name + '.S'
        self.verbose_msg('Compiling '+srcfile+' -> '+outfile)
        util.write_file(srcfile, buf.getvalue())
        e = util.call([XCC, srcfile, '-o', outfile] + COMPILE_FLAGS)
        if cleanup:
            os.remove(srcfile)
        return e

    def assemble_buf(self, name, ext, buf, cleanup=True):
        """ Assemble a buffer containing an XC or assembly program
        """
        srcfile = name + '.' + ext
        outfile = name + '.o'
        self.verbose_msg('Assembling '+srcfile+' -> '+outfile)
        util.write_file(srcfile, buf.getvalue())
        if ext == 'xc':
            e = util.call([XCC, srcfile, '-o', outfile] + ASSEMBLE_FLAGS)
        elif ext == 'S':
            e = util.call([XAS, srcfile, '-o', outfile])
        if cleanup: 
            os.remove(srcfile)
        return e

    def target(self):
        return '{}/XMP-{}.xn'.format(CONFIGS_DIR, self.numcores)

    def assemble_runtime(self):
        self.verbose_msg('Compiling runtime:')
        e = False
        for x in RUNTIME_FILES:
            objfile = x+'.o'
            self.verbose_msg('  '+x+' -> '+objfile)
            e = util.call([XCC, self.target(), RUNTIME_DIR+'/'+x, '-o', objfile] 
                    + ASSEMBLE_FLAGS)
        return e

    def link_master(self):
        self.verbose_msg('Linking master -> '+MASTER_XE)
        e = util.call([XCC, self.target(), 
            '-first '+MASTER_JUMPTAB+'.o', MASTER_SIZETAB+'.o',
            'system.S.o', 'system.xc.o',
            'guest.xc.o', 'host.xc.o', 'host.S.o',
            'master.xc.o', 'master.S.o', 
            'program.o',
            'util.xc.o', '-o', MASTER_XE] + LINK_FLAGS)
        return e

    def link_slave(self):
        self.verbose_msg('Linking slave -> '+SLAVE_XE)
        e = util.call([XCC, self.target(), 
            '-first slavejumptab.o',
            'system.S.o', 'system.xc.o',
            'guest.xc.o', 'host.xc.o', 'host.S.o',
            'slave.S.o',
            'util.xc.o', '-o', SLAVE_XE] + LINK_FLAGS)
        return e

    def replace_slaves(self):
        self.verbose_msg('Splitting slave')
        e = util.call([XOBJDUMP, '--split', SLAVE_XE])
        for x in range(self.numcores):
            node = floor(x / CORES_PER_NODE)
            core = floor(x % CORES_PER_NODE)
            if core == 0:
                self.verbose_msg('\r  Replacing node {}, core 0'.format(node),
                        end='')
            else:
                self.verbose_msg(', {}'.format(core), end='')
            e = util.call([XOBJDUMP, MASTER_XE, 
                    '-r', '{},{},image_n0c0.elf'.format(node, core)])
        self.verbose_msg('')
        return e

    def insert_labels(self, file, buf):
        """ Insert top and bottom labels for each function 
        """
        # Look for the structure and insert:
        # > .globl <bottom-label>
        #   foo:
        #     ...
        # > <bottom-label>
        #   .cc_bottom foo.function
        
        self.verbose_msg('Inserting function labels')
        lines = util.read_file(file, readlines=True)

        # For each function, for each line...
        # (Create a new list and modify it each time...)
        b = False
        for x in self.sem.proc_names:
            new = []
            for (i, y) in enumerate(lines):
                new.append(y)
                if y == x+':\n' and not b:
                    new.insert(len(new)-1, '.globl '+self.function_label_bottom(x)+'\n')
                    b = True
                elif y[0] == '.' and b:
                    if y.split(' ')[0] == '.cc_bottom':
                        new.insert(len(new)-1, self.function_label_bottom(x)+':\n')
                        b = False
            lines = new
    
        # Make sure the buffer is empty and write the lines
        for x in lines:
            buf.write(x)

    def build_jumptab(self, buf):

        self.verbose_msg('Building master jump table')
        
        # Constant section
        buf.write('\t.section .cp.rodata, "ac", @progbits\n')
        buf.write('\t.align {}\n'.format(BYTES_PER_WORD))
        
        # Header
        buf.write('\t.globl '+JUMP_TABLE+', "a(:ui)"\n')
        buf.write('\t.set {}.globound, {}\n'.format(JUMP_TABLE,
            BYTES_PER_WORD*JUMP_TABLE_SIZE))
        buf.write(JUMP_TABLE+':\n')
        
        # Runtime entries
        buf.write('\t.word '+LBL_MIGRATE+'\n')
        buf.write('\t.word '+LBL_INIT_THREAD+'\n')
        buf.write('\t.word '+LBL_CONNECT+'\n')

        # Program entries
        for x in self.sem.proc_names:
            buf.write('\t.word '+x+'\n')

        # Pad any unused space
        remaining = JUMP_TABLE_SIZE - (NUM_RUNTIME_ENTRIES+
                len(self.sem.proc_names))
        buf.write('\t.space {}\n'.format(remaining))

    def build_sizetab(self, buf):

        self.verbose_msg('Building master size table')
        
        # Data section
        buf.write('\t.section .dp.data, "awd", @progbits\n')
        buf.write('\t.align {}\n'.format(BYTES_PER_WORD))
        
        # Header
        buf.write('\t.globl '+SIZE_TABLE+'\n')
        buf.write('\t.set {}.globound, {}\n'.format(SIZE_TABLE,
            BYTES_PER_WORD*(NUM_RUNTIME_ENTRIES+
                len(self.sem.proc_names))))
        buf.write(SIZE_TABLE+':\n')
        
        # Pad runtime entries
        for x in range(NUM_RUNTIME_ENTRIES):
            buf.write('\t.word 0\n')

        # Program procedure entries
        for x in self.sem.proc_names:
            buf.write('\t.word {}-{}+{}\n'.format(
                self.function_label_bottom(x), x, BYTES_PER_WORD))

    def function_label_top(self, name):
        return '.L'+name+'_top'

    def function_label_bottom(self, name):
        return '.L'+name+'_bottom'

    def cleanup(self, output_xe):
        self.verbose_msg('Cleaning up')
        os.rename(MASTER_XE, output_xe)
        os.remove('image_n0c0.elf')
        os.remove('config.xml')
        os.remove('platform_def.xn')
        os.remove('program_info.txt')
        os.remove('slave.xe')
        for x in glob.glob('*.o'):
            os.remove(x)
        # *.S, *.o, *.xc

    def verbose_msg(self, msg, end='\n'):
        if self.verbose: 
            sys.stdout.write(msg+end)
            sys.stdout.flush()

