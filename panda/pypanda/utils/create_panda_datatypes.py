#!/usr/bin/env python3
import re
import os

# Autogenerate panda_datatypes.py and include/panda_datatypes.h
#
# Both of these files contain info in or derived from stuff in
# panda/include/panda.  Here, we autogenerate the two files so that we
# never have to worry about how to keep them in sync with the info in
# those include files.  See panda/include/panda/README.pypanda for 
# so proscriptions wrt those headers we use here. They need to be kept
# fairly clean if we are to be able to make sense of them with this script
# which isn't terriby clever.
#

OUTPUT_DIR = os.path.abspath(os.path.join(*[os.path.dirname(__file__), "..", "panda", "autogen"]))        # panda-git/panda/pypanda/panda/autogen
PLUGINS_DIR = os.path.abspath(os.path.join(*[os.path.dirname(__file__), "..", "..", "plugins"]))          # panda-git/panda/plugins
INCLUDE_DIR = os.path.abspath(os.path.join(*[os.path.dirname(__file__), "..", "..", "include", "panda"])) # panda-git/panda/include/panda



pypanda_start_pattern = """// BEGIN_PYPANDA_NEEDS_THIS -- do not delete this comment bc pypanda
// api autogen needs it.  And don't put any compiler directives
// between this and END_PYPANDA_NEEDS_THIS except includes of other
// files in this directory that contain subsections like this one.
"""

pypanda_end_pattern = "// END_PYPANDA_NEEDS_THIS -- do not delete this comment!\n"


pypanda_headers = []


def create_pypanda_header(filename):
    contents = open(filename).read()
    a = contents.find(pypanda_start_pattern)
    if a == -1: return None
    a += len(pypanda_start_pattern)
    b = contents.find(pypanda_end_pattern)
    if b == -1: return None
    subcontents = contents[a:b]
    # look for local includes
    rest = []
    (plugin_dir,fn) = os.path.split(filename)
    for line in subcontents.split("\n"):
        foo = re.search('\#include "(.*)"$', line)
        if foo:
            nested_inc = foo.groups()[0]
            print("Found nested include of %s" % nested_inc)
            create_pypanda_header("%s/%s" % (plugin_dir,nested_inc))
        else:
            rest.append(line)
    new_contents = "\n".join(rest)
    foo = re.search("([^\/]+)\.h$", filename)
    assert (not (foo is None))
    pypanda_h = os.path.join(INCLUDE_DIR, foo.groups()[0])
    print("Creating pypanda header [%s] for [%s]" % (pypanda_h, filename))
    with open(pypanda_h, "w") as pyph:
        pyph.write(new_contents)
    pypanda_headers.append(pypanda_h)


# examine all plugin dirs looking for pypanda-aware headers and pull
# out pypanda bits to go in INCLUDE_DIR files
for plugin in os.listdir(PLUGINS_DIR):
    if plugin == ".git": continue
    plugin_dir = PLUGINS_DIR + "/" + plugin
    if os.path.isdir(plugin_dir):
        # just look for plugin_int_fns.h
        plugin_file = plugin + "_int_fns.h"
        if os.path.exists("%s/%s" % (plugin_dir, plugin_file)):
            print("Examining [%s] for pypanda-awareness" % plugin_file)
            create_pypanda_header("%s/%s" % (plugin_dir, plugin_file))
                        

# First, create panda_datatypes.py from INCLUDE_DIR/panda_callback_list.h
#

with open(os.path.join(OUTPUT_DIR, "panda_datatypes.py"), "w") as pdty:

    pdty.write("""
# NOTE: panda_datatypes.py is auto generated by the script create_panda_datatypes.py
# Please do not tinker with it!  Instead, fix the script that generates it
""")

    pdty.write("""
from enum import Enum
from ctypes import *
from collections import namedtuple
from cffi import FFI

ffi = FFI()
pyp = ffi

def read_cleanup_header(fname):
    # CFFI can't handle externs, but sometimes we have to extern C (as opposed to 
    r = open(fname).read()
    for line in r.split("\\n"):
        assert("extern \\"C\\" {{" not in line), "Externs unsupported by CFFI. Change {{}} to a single line without braces".format(r)
    r = r.replace("extern \\"C\\" ", "") # This allows inline externs like 'extern "C" void foo(...)'
    return r

ffi.cdef("typedef uint32_t target_ulong;")
ffi.cdef(read_cleanup_header("{inc}/pthreadtypes.h"))
ffi.cdef(read_cleanup_header("{inc}/panda_x86_support.h"))
ffi.cdef(read_cleanup_header("{inc}/panda_qemu_support.h"))
ffi.cdef(read_cleanup_header("{inc}/panda_datatypes.h"))
ffi.cdef(read_cleanup_header("{inc}/panda_osi.h"))
ffi.cdef(read_cleanup_header("{inc}/panda_osi_linux.h"))
ffi.cdef(read_cleanup_header("{inc}/hooks.h"))
""".format(inc=INCLUDE_DIR))

    for pypanda_header in pypanda_headers:
        pdty.write('ffi.cdef(read_cleanup_header("%s"))\n' % pypanda_header)

    pdty.write("""
# so we need access to some data structures, but don't actually
# want to open all of libpanda yet because we don't have all the
# file information. So we just open libc to access this.
C = ffi.dlopen(None)

class PandaState(Enum):
    UNINT = 1
    INIT_DONE = 2
    IN_RECORD = 3
    IN_REPLAY = 4
""")

    cbn = 0
    cb_list = {}
    with open (os.path.join(INCLUDE_DIR, "panda_callback_list.h")) as fp:
        for line in fp:
            foo = re.search("^(\s+)PANDA_CB_([^,]+)\,", line)
            if foo:
                cbname = foo.groups()[1]
                cbname_l = cbname.lower()
                cb_list[cbn] = cbname_l
                cbn += 1
    cb_list[cbn] = "last"
    cbn += 1


    pdty.write('\nPandaCB = namedtuple("PandaCB", "init \\\n')
    for i in range(cbn-1):
        pdty.write(cb_list[i] + " ")
        if i == cbn-2:
            pdty.write('")\n')
        else:
            pdty.write("\\\n")

    in_tdu = False
    cb_types = {}
    with open (os.path.join(INCLUDE_DIR, "panda_callback_list.h")) as fp:
        for line in fp:
            foo = re.search("typedef union panda_cb {", line)
            if foo:
                in_tdu = True
                continue
            foo = re.search("} panda_cb;", line)
            if foo:
                in_tdu = False
                continue
            if in_tdu:
                # int (*before_block_translate)(CPUState *env, target_ulong pc);
                for i in range(cbn):
                    foo = re.search("^\s+(.*)\s+\(\*%s\)\((.*)\);" % cb_list[i], line)
                    if foo:
                        rvtype = foo.groups()[0]
                        params = foo.groups()[1]
                        partypes = []
                        for param in (params.split(',')):
                            j = 1
                            while True:
                                c = param[-j]
                                if not (c.isalpha() or c.isnumeric() or c=='_'):
                                    break
                                if j == len(param):
                                    break
                                j += 1
                            if j == len(param):
                                typ = param
                            else:
                                typ = param[:(-j)+1].strip()
                            partypes.append(typ)
                        cb_typ = rvtype + " (" +  (", ".join(partypes)) + ")"
                        cb_name = cb_list[i]
                        cb_types[i] = (cb_name, cb_typ)

    # Sanity check: input files must match
    for i in range(cbn-1):
        if i not in cb_types:
            print(cb_types[i-1])
            raise RuntimeError("Callback #{} missing from cb_types- is it in panda_callback_list.h's panda_cb_type enum AND as a prototype later in the source?".format(i))

    pdty.write("""

pcb = PandaCB(init = pyp.callback("bool(void*)"), 
""")

    for i in range(cbn-1):
        pdty.write('%s = pyp.callback("%s")' % cb_types[i])
        if i == cbn-2:
            pdty.write(")\n")
        else:
            pdty.write(",\n")

    pdty.write("""

pandacbtype = namedtuple("pandacbtype", "name number")

""")


    pdty.write("""

callback_dictionary = {
pcb.init : pandacbtype("init", -1),
""")


    for i in range(cbn-1):
        cb_name = cb_list[i]
        cb_name_up = cb_name.upper()
        pdty.write('pcb.%s : pandacbtype("%s", C.PANDA_CB_%s)' % (cb_name, cb_name, cb_name_up))
        if i == cbn-2:
            pdty.write("}\n")
        else:
            pdty.write(",\n")


    pdty.write("""
class Hook(object):
    def __init__(self,is_enabled=True,is_kernel=True,hook_cb=True,target_addr=0,target_library_offset=0,library_name=None,program_name=None):
        self.is_enabled = is_enabled
        self.is_kernel = is_kernel
        self.hook_cb = hook_cb
        self.target_addr = target_addr
        self.target_library_offset = target_library_offset
        self.library_name = library_name
        self.program_name = program_name
        """)


#########################################################
#########################################################
# second, create panda_datatypes.h by glomming together
# files in panda/include/panda

with open(os.path.join(INCLUDE_DIR, "panda_datatypes"), "w") as pdth:

    pdth.write("""
// NOTE: panda_datatypes.h is auto generated by the script create_panda_datatypes.py
// Please do not tinker with it!  Instead, fix the script that generates it

#define PYPANDA 1

""")

    def read_but_exclude_garbage(filename):
        nongarbage = []
        with open(filename) as thefile:
            for line in thefile:
                keep = True
                foo = re.search("^\s*\#", line)
                if foo:
                    foo = re.search("^\s*\#define [^_]", line)
                    if not foo:
                        keep = False
                if keep:
                    nongarbage.append(line)
            return nongarbage
    pn = 1
    def include_this(fn):
        global pn
        fn = os.path.join(INCLUDE_DIR, fn)
        pdth.write("\n\n// -----------------------------------\n")
        pdth.write("// Pull number %d from %s\n" % (pn,fn))
        for line in read_but_exclude_garbage(fn):
            pdth.write(line)
        pn += 1
    include_this("panda_callback_list.h")
    include_this("panda_plugin_mgmt.h")
    include_this("panda_args.h")
    include_this("panda_api.h")
    include_this("panda_os.h")
    # probably a better way... 
    pdth.write("typedef target_ulong target_ptr_t;\n")
    include_this("panda_common.h")
