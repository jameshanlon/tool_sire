import sys
import re
import os
import subprocess

def read_file(filename, readlines=False):
    """ Read a file and return its contents as a string 
    """
    #verbose_report("Reading input file '{}'...\n".format(filename))
    contents=None
    try:
        file = open(filename, 'r')
        if readlines:
            contents = file.readlines()
        else:
            contents = file.read()
        file.close()
        return contents
    except IOError as err:
        print('Error reading input ({}): {}'.format(err.errno, err.strerror),
                file=sys.stderr)
        return None
    except:
        raise Exception('Unexpected error:', sys.exc_info()[0])

def write_file(filename, s):
    """ Write the output to a file 
    """
    #verbose_report("Writing output file '{}'...\n".format(filename))
    try:
        file = open(filename, 'w')
        file.write(s)
        file.close()
        return True
    except IOError as err:
        print('Error writing output ({}): {}'.format(err.errno, err.strerror),
                file=sys.stderr)
        return False
    except:
        raise Exception('Unexpected error:', sys.exc_info()[0])

def call(args):
    """ Try to execute a shell command
    """
    try:
        s = subprocess.check_output(args, stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError as err:
        s = err.output.decode('utf-8').replace("\\n", "\n")
        print('Error executing command:\n{}\nOuput:\n{}'.format(err.cmd, s))
        return False

def remove_file(filename):
    """ Remove a file if it exists
    """
    if os.path.isfile(filename):
        os.remove(filename)

def rename_file(filename, newname):
    """ Rename a file if it exists
    """
    if os.path.isfile(filename):
        os.rename(filename, newname)

def camel_to_under(s):
    return re.sub("([A-Z])([A-Z][a-z])|([a-z0-9])([A-Z])", 
            lambda m: '{}_{}'.format(m.group(3), m.group(4)), s).lower()

def indexed_dict(elements):
    return dict([(e,i) for i, e in list(enumerate(elements))])

