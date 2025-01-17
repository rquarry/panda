# PANDA Plugins



### Runtime QEMU Control

## Callbacks

---

**before_block_exec_invalidate_opt**: called before execution of every basic
block, with the option to invalidate the TB

**Callback ID**: PANDA_CB_BEFORE_BLOCK_EXEC_INVALIDATE_OPT

**Arguments**:

* `CPUState *env`: the current CPU state
* `TranslationBlock *tb`: the TB we are about to execute

**Return value**:

`true` if we should invalidate the current translation block and retranslate, `false` otherwise

**Signature**:
```C
bool (*before_block_exec_invalidate_opt)(CPUState *env, TranslationBlock *tb);
```
---

**before_block_exec**: called before execution of every basic block

**Callback ID**: PANDA_CB_BEFORE_BLOCK_EXEC

**Arguments**:

* `CPUState *env`: the current CPU state
* `TranslationBlock *tb`: the TB we are about to execute

**Return value**:

unused

**Signature**:
```C
int (*before_block_exec)(CPUState *env, TranslationBlock *tb);
```
---

**after_block_exec**: called after execution of every basic block

**Callback ID**: PANDA_CB_AFTER_BLOCK_EXEC

**Arguments**:

* `CPUState *env`: the current CPU state
* `TranslationBlock *tb`: the TB we just executed
* `uint8_t exitCode`: one of the `TB_EXIT_` constants found in `tcg.h`

**Return value**:

unused

**Notes**:

The `exitCode` can be used to determine if the `tb` was executed to completion, or was interrupted due to an exit request.  If `exitCode <= TB_EXIT_IDX1` then the block ran to completion; otherwise it did not, and will be retried later.

**Signature**:
```C
int (*after_block_exec)(CPUState *env, TranslationBlock *tb, uint8_t exitCode);
```
---

**before_block_translate**: called before translation of each basic block

**Callback ID**: PANDA_CB_BEFORE_BLOCK_TRANSLATE

**Arguments**:

* `CPUState *env`: the current CPU state
* `target_ulong pc`: the guest PC we are about to translate

**Return value**:

unused

**Signature**:
```C
int (*before_block_translate)(CPUState *env, target_ulong pc);
```
---

**after_block_translate**: called after the translation of each basic block

**Callback ID**: PANDA_CB_AFTER_BLOCK_TRANSLATE

**Arguments**:

* `CPUState *env`: the current CPU state
* `TranslationBlock *tb`: the TB we just translated

**Return value**:

unused

**Notes**:

This is a good place to perform extra passes over the generated
code (particularly by manipulating the LLVM code)
**FIXME**: How would this actually work? By this point the out ASM
has already been generated. Modify the IR and then regenerate?

**Signature**:
```C
int (*after_block_translate)(CPUState *env, TranslationBlock *tb);
```
---

**insn_translate**: called before the translation of each instruction

**Callback ID**: PANDA_CB_INSN_TRANSLATE

**Arguments**:

* `CPUState *env`: the current CPU state
* `target_ulong pc`: the guest PC we are about to translate

**Return value**:

`true` if PANDA should insert instrumentation into the generated code,
`false` otherwise

**Notes**:

This allows a plugin writer to instrument only a small number of
instructions, avoiding the performance hit of instrumenting everything.
If you do want to instrument every single instruction, just return
true. See the documentation for `PANDA_CB_INSN_EXEC` for more detail.

**Signature**:
```C
bool (*insn_translate)(CPUState *env, target_ulong pc);
```
---

**insn_exec**: called before execution of any instruction identified
by the `PANDA_CB_INSN_TRANSLATE` callback

**Callback ID**: PANDA_CB_INSN_EXEC

**Arguments**:

* `CPUState *env`: the current CPU state
* `target_ulong pc`: the guest PC we are about to execute

**Return value**:

unused

**Notes**:

This instrumentation is implemented by generating a call to a
helper function just before the instruction itself is generated.
This is fairly expensive, which is why it's only enabled via
the `PANDA_CB_INSN_TRANSLATE` callback.

**Signature**:
```C
int (*insn_exec)(CPUState *env, target_ulong pc);
```
---

**guest_hypercall**: called when a program inside the guest makes a
hypercall to pass information from inside the guest to a plugin

**Callback ID**: PANDA_CB_GUEST_HYPERCALL

**Arguments**:

* `CPUState *env`: the current CPU state

**Return value**:

unused

**Notes**:

On x86, this is called whenever CPUID is executed. Plugins then check for magic
values in the registers to determine if it really is a guest hypercall.
Parameters can be passed in other registers.  We have modified translate.c to
make CPUID instructions end translation blocks.  This is useful, if, for
example, you want to have a hypercall that turns on LLVM and enables heavyweight
instrumentation at a specific point in execution.

S2E accomplishes this by using a (currently) undefined opcode. We
have instead opted to use an existing instruction to make development
easier (we can use inline asm rather than defining the raw bytes).

AMD's SVM and Intel's VT define hypercalls, but they are privileged
instructions, meaning the guest must be in ring 0 to execute them.

For hypercalls in ARM, we use the MCR instruction (move to coprocessor from ARM
register), moving to coprocessor 7.  CP 7 is reserved by ARM, and isn't
implemented in QEMU.  The MCR instruction is present in all versions of ARM, and
it is an unprivileged instruction in this scenario.  Plugins can also check for
magic values in registers on ARM.

**Signature**:
```C
int (*guest_hypercall)(CPUState *env);
```
---

**monitor**: called when someone uses the `plugin_cmd` monitor command

**Callback ID**: PANDA_CB_MONITOR

**Arguments**:

* `Monitor *mon`: a pointer to the Monitor
* `const char *cmd`: the command string passed to plugin_cmd

**Return value**:

unused

**Notes**:

The command is passed as a single string. No parsing is performed
on the string before it is passed to the plugin, so each plugin
must parse the string as it deems appropriate (e.g. by using `strtok`
and `getopt`) to do more complex option processing.

It is recommended that each plugin implementing this callback respond
to the "help" message by listing the commands supported by the plugin.

Note that every loaded plugin will have the opportunity to respond to
each `plugin_cmd`; thus it is a good idea to ensure that your plugin's
monitor commands are uniquely named, e.g. by using the plugin name
as a prefix (`sample_do_foo` rather than `do_foo`).

**Signature**:
```C
int (*monitor)(Monitor *mon, const char *cmd);
```
---

**cb_cpu_restore_state**: Called inside of cpu_restore_state(), when there is a
CPU fault/exception

**Callback ID**: PANDA_CB_CPU_RESTORE_STATE

**Arguments**:

* `CPUState *env`: the current CPU state
* `TranslationBlock *tb`: the current translation block
       
**Return value**: unused

**Signature**:
```C
int (*cb_cpu_restore_state)(CPUState *env, TranslationBlock *tb);
```
---

**replay_hd_transfer**: Called during a replay of a hard drive transfer action

**Callback ID**: PANDA_CB_REPLAY_HD_TRANSFER 
 
**Arguments**:

* `CPUState* env`: pointer to CPUState
* `uint32_t type`: type of transfer (Hd_transfer_type)
* `uint64_t src_addr`: address for src
* `uint64_t dest_addr`: address for dest
* `uint32_t num_bytes`: size of transfer in bytes
      
**Return value**: unused

**Notes**:
In replay only, some kind of data transfer involving hard drive.  NB: We are
neither before nor after, really.  In replay the transfer doesn't really happen.
We are *at* the point at which it happened, really.  Even though the transfer
doesn't happen in replay, useful instrumentations (such as taint analysis) can
still be applied accurately.

**Signature**:
```C
int (*replay_hd_transfer)(CPUState *env, uint32_t type, uint64_t src_addr,
                            uint64_t dest_addr, uint32_t num_bytes);
```
---

**replay_before_cpu_physical_mem_rw_ram**: In replay only, we are about to dma
from some qemu buffer to guest memory

**Callback ID**: PANDA_CB_REPLAY_BEFORE_CPU_PHYSICAL_MEM_RW_RAM

**Arguments**:

* `CPUState* env`: pointer to CPUState                   
* `uint32_t is_write`: type of transfer going on (is_write == 1 means IO -> RAM else RAM -> IO)
* `uint64_t src_addr`: src of dma
* `uint64_t dest_addr`: dest of dma
* `uint32_t num_bytes`: size of transfer

**Return value**: unused

**Notes**:
In the current version of QEMU, this appears to be a less commonly used method
of performing DMA with the hard drive device.  For the hard drive, the most
common DMA mechanism can be seen in the PANDA_CB_REPLAY_HD_TRANSFER_TYPE under
type HD_TRANSFER_HD_TO_RAM (and vice versa).  Other devices still appear to use
cpu_physical_memory_rw() though.

**Signature**:
```C
int (*replay_before_cpu_physical_mem_rw_ram)(
        CPUState *env, uint32_t is_write, uint64_t src_addr, uint64_t dest_addr,
        uint32_t num_bytes);
```
---

**replay_handle_packet**: used for network packet replay

**Callback ID**:   PANDA_CB_REPLAY_HANDLE_PACKET

**Arguments**:

* `CPUState *env`: pointer to CPUState
* `uint8_t *buf`: buffer containing packet data
* `int size`: num bytes in buffer
* `uint8_t direction`: `PANDA_NET_RX` for receive, `PANDA_NET_TX` for transmit
* `uint64_t old_buf_addr`: the address that the buffer had when the recording was taken

**Signature**:
```C
int (*replay_handle_packet)(CPUState *env, uint8_t *buf, int size,
                            uint8_t direction, uint64_t old_buf_addr);
```
---

**after_cpu_exec_enter**: called right after cpu_exec calls the cpu_exec_enter function

**Callback ID**:   PANDA_CB_AFTER_CPU_EXEC_ENTER

**Arguments**:

* `CPUState *env`: pointer to CPUState

**Return value**: unused

**Signature**:
```C
int (*after_cpu_exec_enter)(CPUState *env);
```
---

**before_cpu_exec_exit**: called right before cpu_exec calls the cpu_exec_exit function

**Callback ID**:   PANDA_CB_BEFORE_CPU_EXEC_EXIT

**Arguments**:

* `CPUState *env`: pointer to CPUState
* `bool ranBlock`: true if ran a block since the previous cpu_exec_enter

**Return value**: unused

**Signature**:
```C
int (*before_cpu_exec_exit)(CPUState *env, bool ranBlock);
```
---

## Sample Plugin: Syscall Monitor

To make the information in the preceding sections concrete, we will now show how to implement a low-overhead x86 system call monitor as a PANDA plugin. To do so, we will use the `PANDA_CB_INSN_TRANSLATE` and `PANDA_CB_INSN_EXEC` callbacks to create instrumentation that will execute only when the `sysenter` command is executed on x86.

First, we will create a `Makefile` for our plugin, and place it in `panda/qemu/panda_plugins/syscalls`:

```Makefile
# Don't forget to add your plugin to config.panda!

# Set your plugin name here. It does not have to correspond to the name
# of the directory in which your plugin resides.
PLUGIN_NAME=syscalls

# Include the PANDA Makefile rules
include ../panda.mak

# If you need custom CFLAGS or LIBS, set them up here
# CFLAGS+=
# LIBS+=

# The main rule for your plugin. Please stick with the panda_ naming
# convention.
panda_$(PLUGIN_NAME).so: $(PLUGIN_TARGET_DIR)/$(PLUGIN_NAME).o
    $(call quiet-command,$(CC) $(QEMU_CFLAGS) -shared -o $(SRC_PATH)/$(TARGET_DIR)/$@ $^ $(LIBS),"  PLUGIN  $@")

all: panda_$(PLUGIN_NAME).so
```

Next, we'll create the main code for the plugin, and put it in `panda/qemu/panda_plugins/syscalls.c`:

```C
#include "config.h"
#include "qemu-common.h"
#include "cpu.h"

#include "panda_plugin.h"

#include <stdio.h>
#include <stdlib.h>

bool translate_callback(CPUState *env, target_ulong pc);
int exec_callback(CPUState *env, target_ulong pc);

bool init_plugin(void *);
void uninit_plugin(void *);

// This is where we'll write out the syscall data
FILE *plugin_log;

// Check if the instruction is sysenter (0F 34)
bool translate_callback(CPUState *env, target_ulong pc) {
    unsigned char buf[2];
    cpu_memory_rw_debug(env, pc, buf, 2, 0);
    if (buf[0] == 0x0F && buf[1] == 0x34)
        return true;
    else
        return false;
}

// This will only be called for instructions where the
// translate_callback returned true
int exec_callback(CPUState *env, target_ulong pc) {
#ifdef TARGET_I386
    // On Windows and Linux, the system call id is in EAX
    fprintf(plugin_log,
    	"PC=" TARGET_FMT_lx ", SYSCALL=" TARGET_FMT_lx "\n",
    	pc, env->regs[R_EAX]);
#endif
    return 0;
}

bool init_plugin(void *self) {
// Don't bother if we're not on x86
#ifdef TARGET_I386
    panda_cb pcb;

    pcb.insn_translate = translate_callback;
    panda_register_callback(self, PANDA_CB_INSN_TRANSLATE, pcb);
    pcb.insn_exec = exec_callback;
    panda_register_callback(self, PANDA_CB_INSN_EXEC, pcb);
#endif

    plugin_log = fopen("syscalls.txt", "w");    
    if(!plugin_log) return false;
    else return true;
}

void uninit_plugin(void *self) {
    fclose(plugin_log);
}
```

The `init_plugin` function registers the callbacks for instruction translation and execution. Because we are only implementing an x86 callback monitor, we wrap the callback registration in an `#ifdef TARGET_I386`; this means that on other architectures the plugin won't do anything (since no callbacks will be registered). It also opens up a text file that the plugin will use to log the system calls executed by the guest; if opening the file fails, `init_plugin` returns false, which will cause PANDA to unload the plugin immediately.

The `translate_callback` function reads the bytes that make up the instruction that QEMU is about to translate using `cpu_memory_rw_debug`, and and checks to see whether it is a `sysenter` instruction. If so, then it returns `true`, which tells PANDA to insert instrumentation that will cause the `exec_callback` function to be called when the instruction is executed by the guest.

Inside `exec_callback`, we simply log the current program counter (`EIP`) and the contents of the `EAX` register, which is used on both Windows and Linux to hold the system call number.

Finally, in `uninit_plugin`, we simply close the plugin log file.

To make the plugin, we add it to the list of plugins in `panda/panda/plugins/config.panda`:

	sample
	taintcap
	textfinder
	textprinter
	syscalls
	
Then run `make` from the BUILD directory:

```
brendan@laredo3:~/hg/panda/build$ make
  CC    /home/brendan/hg/panda/build//x86_64-softmmu//panda_plugins/syscalls.o
  PLUGIN  panda_syscalls.so
  CC    /home/brendan/hg/panda/build//i386-linux-user//panda_plugins/syscalls.o
  PLUGIN  panda_syscalls.so
  CC    /home/brendan/hg/panda/build//arm-linux-user//panda_plugins/syscalls.o
  PLUGIN  panda_syscalls.so
  CC    /home/brendan/hg/panda/build//arm-softmmu//panda_plugins/syscalls.o
  PLUGIN  panda_syscalls.so
```

Finally, you can run QEMU with the plugin enabled:

```
x86_64-softmmu/panda-system-x86_64 -m 1024 -vnc :0 -monitor stdio \
	-hda /scratch/qcows/qcows/win7.1.qcow2 -loadvm booted -k en-us \
	-panda syscalls
```

When run on a Windows 7 VM, this plugin produces output in `syscalls.txt` that looks like:

```
PC=0000000077bd70b2, SYSCALL=0000000000000153
PC=0000000077bd70b2, SYSCALL=0000000000000188
PC=0000000077bd70b2, SYSCALL=00000000000011fa
PC=0000000077bd70b2, SYSCALL=00000000000011c7
PC=0000000077bd70b2, SYSCALL=00000000000011c7
PC=0000000077bd70b2, SYSCALL=0000000000001232
PC=0000000077bd70b2, SYSCALL=0000000000001232
PC=0000000077bd70b2, SYSCALL=000000000000114d
PC=0000000077bd70b2, SYSCALL=0000000000001275           
```

The raw system call numbers could also be translated into their names, e.g. by using [Volatility's list of Windows 7 system calls](https://code.google.com/p/volatility/source/browse/trunk/volatility/plugins/overlays/windows/win7_sp01_x86_syscalls.py).
