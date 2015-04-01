# Lab1 erport

## [练习1]

[练习1.1] 操作系统镜像文件 ucore.img 是如何一步一步生成的?(需要比较详细地解释 Makefile 中
每一条相关命令和命令参数的含义,以及说明命令导致的结果)

```
#注意Makefile中文注释部分
PROJ	:= challenge
EMPTY	:=
SPACE	:= $(EMPTY) $(EMPTY)
SLASH	:= /

V       := @
#定义并指向正确的gccprefix
# try to infer the correct GCCPREFX
ifndef GCCPREFIX
GCCPREFIX := $(shell if i386-elf-objdump -i 2>&1 | grep '^elf32-i386$$' >/dev/null 2>&1; \
	then echo 'i386-elf-'; \
	elif objdump -i 2>&1 | grep 'elf32-i386' >/dev/null 2>&1; \
	then echo ''; \
	else echo "***" 1>&2; \
	echo "*** Error: Couldn't find an i386-elf version of GCC/binutils." 1>&2; \
	echo "*** Is the directory with i386-elf-gcc in your PATH?" 1>&2; \
	echo "*** If your i386-elf toolchain is installed with a command" 1>&2; \
	echo "*** prefix other than 'i386-elf-', set your GCCPREFIX" 1>&2; \
	echo "*** environment variable to that prefix and run 'make' again." 1>&2; \
	echo "*** To turn off this error, run 'gmake GCCPREFIX= ...'." 1>&2; \
	echo "***" 1>&2; exit 1; fi)
endif
#定义并指向正确的qemu
# try to infer the correct QEMU
ifndef QEMU
QEMU := $(shell if which qemu-system-i386 > /dev/null; \
	then echo 'qemu-system-i386'; exit; \
	elif which i386-elf-qemu > /dev/null; \
	then echo 'i386-elf-qemu'; exit; \
	else \
	echo "***" 1>&2; \
	echo "*** Error: Couldn't find a working QEMU executable." 1>&2; \
	echo "*** Is the directory containing the qemu binary in your PATH" 1>&2; \
	echo "***" 1>&2; exit 1; fi)
endif
#消除默认的后缀规则
#使用以下的规定的拓展名规则
# eliminate default suffix rules
.SUFFIXES: .c .S .h

# delete target files if there is an error (or make is interrupted)
.DELETE_ON_ERROR:

# define compiler and flags

HOSTCC		:= gcc
HOSTCFLAGS	:= -g -Wall -O2

CC		:= $(GCCPREFIX)gcc
CFLAGS	:= -fno-builtin -Wall -ggdb -m32 -gstabs -nostdinc $(DEFS)
CFLAGS	+= $(shell $(CC) -fno-stack-protector -E -x c /dev/null >/dev/null 2>&1 && echo -fno-stack-protector)
CTYPE	:= c S

LD      := $(GCCPREFIX)ld
LDFLAGS	:= -m $(shell $(LD) -V | grep elf_i386 2>/dev/null)
LDFLAGS	+= -nostdlib

OBJCOPY := $(GCCPREFIX)objcopy
OBJDUMP := $(GCCPREFIX)objdump

COPY	:= cp
MKDIR   := mkdir -p
MV		:= mv
RM		:= rm -f
AWK		:= awk
SED		:= sed
SH		:= sh
TR		:= tr
TOUCH	:= touch -c

OBJDIR	:= obj
BINDIR	:= bin

ALLOBJS	:=
ALLDEPS	:=
TARGETS	:=

include tools/function.mk

listf_cc = $(call listf,$(1),$(CTYPE))

# for cc
add_files_cc = $(call add_files,$(1),$(CC),$(CFLAGS) $(3),$(2),$(4))
create_target_cc = $(call create_target,$(1),$(2),$(3),$(CC),$(CFLAGS))

# for hostcc
add_files_host = $(call add_files,$(1),$(HOSTCC),$(HOSTCFLAGS),$(2),$(3))
create_target_host = $(call create_target,$(1),$(2),$(3),$(HOSTCC),$(HOSTCFLAGS))

cgtype = $(patsubst %.$(2),%.$(3),$(1))
objfile = $(call toobj,$(1))
asmfile = $(call cgtype,$(call toobj,$(1)),o,asm)
outfile = $(call cgtype,$(call toobj,$(1)),o,out)
symfile = $(call cgtype,$(call toobj,$(1)),o,sym)

# for match pattern
match = $(shell echo $(2) | $(AWK) '{for(i=1;i<=NF;i++){if(match("$(1)","^"$$(i)"$$")){exit 1;}}}'; echo $$?)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# include kernel/user
#生成kernel
INCLUDE	+= libs/

CFLAGS	+= $(addprefix -I,$(INCLUDE))

LIBDIR	+= libs

$(call add_files_cc,$(call listf_cc,$(LIBDIR)),libs,)

# -------------------------------------------------------------------
# kernel

KINCLUDE	+= kern/debug/ \
			   kern/driver/ \
			   kern/trap/ \
			   kern/mm/

KSRCDIR		+= kern/init \
			   kern/libs \
			   kern/debug \
			   kern/driver \
			   kern/trap \
			   kern/mm

KCFLAGS		+= $(addprefix -I,$(KINCLUDE))
#由KSRCDIR定义的文件生成.o如下
#kernel.ld init.o readline.o stdio.o kdebug.o kmonitor.o panic.o clock.o console.o intr.o picirq.o trap.o trapentry.o vectors.o pmm.o  printfmt.o string.o
$(call add_files_cc,$(call listf_cc,$(KSRCDIR)),kernel,$(KCFLAGS))

KOBJS	= $(call read_packet,kernel libs)

# create kernel target
kernel = $(call totarget,kernel)
#ld 指令已经存在，无需重新生成
$(kernel): tools/kernel.ld

$(kernel): $(KOBJS)
	@echo + ld $@
	$(V)$(LD) $(LDFLAGS) -T tools/kernel.ld -o $@ $(KOBJS)
	@$(OBJDUMP) -S $@ > $(call asmfile,kernel)
	@$(OBJDUMP) -t $@ | $(SED) '1,/SYMBOL TABLE/d; s/ .* / /; /^$$/d' > $(call symfile,kernel)

$(call create_target,kernel)

# -------------------------------------------------------------------
#生成bootblock为ucore.img做准备
#bootblock由bootblock.out被sign工具处理得到。
#bootblock.out由bootblock.o生成
#bootmain.o,bootasm.o生成bootblock.o
#sign由sign.c编译生成

# create bootblock
#首先生成bootmain.o 需要编译boot/bootmain.c文件
bootfiles = $(call listf_cc,boot)
$(foreach f,$(bootfiles),$(call cc_compile,$(f),$(CC),$(CFLAGS) -Os -nostdinc))

bootblock = $(call totarget,bootblock)
#此处编译boot/bootasm.S文件生成bootasm.o
$(bootblock): $(call toobj,$(bootfiles)) | $(call totarget,sign)
	@echo + ld $@
	$(V)$(LD) $(LDFLAGS) -N -e start -Ttext 0x7C00 $^ -o $(call toobj,bootblock)
	@$(OBJDUMP) -S $(call objfile,bootblock) > $(call asmfile,bootblock)
	@$(OBJDUMP) -t $(call objfile,bootblock) | $(SED) '1,/SYMBOL TABLE/d; s/ .* / /; /^$$/d' > $(call symfile,bootblock)
	@$(OBJCOPY) -S -O binary $(call objfile,bootblock) $(call outfile,bootblock)
	@$(call totarget,sign) $(call outfile,bootblock) $(bootblock)
#生成boot block
$(call create_target,bootblock)

# -------------------------------------------------------------------
#调用tools/sign.c文件生成sign
#sign.c文件中规定了主引导扇区512字节
# create 'sign' tools
$(call add_files_host,tools/sign.c,sign,sign)
$(call create_target_host,sign,sign)

# -------------------------------------------------------------------
#此处开始创建ucore.img
# create ucore.img

UCOREIMG	:= $(call totarget,ucore.img)
#为生成ucoreimg，需要$(kernel) $(bootblock)，两个在前面已经生成完毕
#生成一个有10000个块的文件
#把bootblock中的内容写到第一个块
#从第二个块开始写kernel中的内容
#使用dd 指令将ucore.img加载到虚拟硬盘中
$(UCOREIMG): $(kernel) $(bootblock)
	$(V)dd if=/dev/zero of=$@ count=10000
	$(V)dd if=$(bootblock) of=$@ conv=notrunc
	$(V)dd if=$(kernel) of=$@ seek=1 conv=notrunc
	
#产生镜像文件

$(call create_target,ucore.img)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#以下部分makefile省略....


```

[练习1.2] 一个被系统认为是符合规范的硬盘主引导扇区的特征是什么?
阅读sign.c的代码,sign.c编译出的sign.o读取bootlock.out的生成数据。
磁盘主引导扇区为512字节。
char buf[512];
且
buf[510] = 0x55;
buf[511] = 0xAA;



## [练习2]

[练习2.1] 从 CPU 加电后执行的第一条指令开始,单步跟踪 BIOS 的执行。

1.make之后在lab1目录下打开终端，运行qemu
```
> cd bin
> qemu -S -s -hda ucore.img -monitor stdio
```
2.运行gdb调试kernel
```
> gdb kernel //运行指向kernel的gdb
> target remote :1234 //连接qemu
> b bootmain //bootmain启动前断点
```
3.经过上述步骤后kernel等待c指令运行。
[练习2.2] 在初始化位置0x7c00 设置实地址断点,测试断点正常。

接练习2.1的内容在gdb中输入

```
> set architecture i8086  //设置当前调试的CPU是8086
> b *0x7c00  //在0x7c00处设置断点。此地址是bootloader入口点地址
> c 
> x /2i $pc  //显示当前eip处的汇编指令
> set architecture i386  //设置当前调试的CPU是80386
```
得到以下结果

```
	Breakpoint 2, 0x00007c00 in ?? ()
	=> 0x7c00:      cli 
	   0x7c01:      cld 
	   0x7c02:      xor    %eax,%eax
	   0x7c04:      mov    %eax,%ds
	   0x7c06:      mov    %eax,%es
	   0x7c08:      mov    %eax,%ss 
	   0x7c0a:      in     $0x64,%al
	   0x7c0c:      test   $0x2,%al
	   0x7c0e:      jne    0x7c0a
	   0x7c10:      mov    $0xd1,%al
```

[练习2.3] 在调用qemu 时增加-d in_asm -D q.log 参数，便可以将运行的汇编指令保存在q.log 中。
将执行的汇编代码与bootasm.S 和 bootblock.asm 进行比较，看看二者是否一致。
在bin目录下打开terminal将运行的汇编指令保存在q.log
```
> qemu -S -s -d in_asm -D q.log ucore.img -monitor stdio
```
在gdb中输入
```
> b bootmain
> c
> x /10i $pc
```

便可以在q.log中读到"call bootmain"前执行的命令
```
	----------------
	IN: 
	0x00007c00:  cli    
	
	----------------
	IN: 
	0x00007c01:  cld    
	0x00007c02:  xor    %ax,%ax
	0x00007c04:  mov    %ax,%ds
	0x00007c06:  mov    %ax,%es
	0x00007c08:  mov    %ax,%ss
	
	----------------
	IN: 
	0x00007c0a:  in     $0x64,%al
	
	----------------
	IN: 
	0x00007c0c:  test   $0x2,%al
	0x00007c0e:  jne    0x7c0a
	
	----------------
	IN: 
	0x00007c10:  mov    $0xd1,%al
	0x00007c12:  out    %al,$0x64
	0x00007c14:  in     $0x64,%al
	0x00007c16:  test   $0x2,%al
	0x00007c18:  jne    0x7c14
	
	----------------
	IN: 
	0x00007c1a:  mov    $0xdf,%al
	0x00007c1c:  out    %al,$0x60
	0x00007c1e:  lgdtw  0x7c6c
	0x00007c23:  mov    %cr0,%eax
	0x00007c26:  or     $0x1,%eax
	0x00007c2a:  mov    %eax,%cr0
	
	----------------
	IN: 
	0x00007c2d:  ljmp   $0x8,$0x7c32
	
	----------------
	IN: 
	0x00007c32:  mov    $0x10,%ax
	0x00007c36:  mov    %eax,%ds
	
	----------------
	IN: 
	0x00007c38:  mov    %eax,%es
	
	----------------
	IN: 
	0x00007c3a:  mov    %eax,%fs
	0x00007c3c:  mov    %eax,%gs
	0x00007c3e:  mov    %eax,%ss
	
	----------------
	IN: 
	0x00007c40:  mov    $0x0,%ebp
	
	----------------
	IN: 
	0x00007c45:  mov    $0x7c00,%esp
	0x00007c4a:  call   0x7d0d
	
	----------------
	IN: 
	0x00007d0d:  push   %ebp
```

其与bootasm.S和bootblock.asm中的代码相同。

## [练习3]
分析bootloader 进入保护模式的过程。
```
#include <asm.h>

# Start the CPU: switch to 32-bit protected mode, jump into C.
# The BIOS loads this code from the first sector of the hard disk into
# memory at physical address 0x7c00 and starts executing in real mode
# with %cs=0 %ip=7c00.
#计算机加电后，由BIOS将bootasm.S生成的可执行代码从硬盘的第一个扇区复制到内存中的物理地址0x7c00处,并开始执行。此时系统处于实模式。可用内存不多于1M。
.set PROT_MODE_CSEG,        0x8                     # kernel code segment selector
.set PROT_MODE_DSEG,        0x10                    # kernel data segment selector
#两个段选择子的作用其实是提供了gdt中代码段和数据段的索引
.set CR0_PE_ON,             0x1                     # protected mode enable flag

# start address should be 0:7c00, in real mode, the beginning address of the running bootloader
#定义了C语言中的main函数，start就相当于main，BIOS调用程序时，从这里开始执行
.globl start
start:
.code16                                             # Assemble for 16-bit mode
#以下代码是在实模式下执行，所以要告诉编译器使用16位模式编译。
    cli                                             # Disable interrupts
    #关中断，设置字符串操作是递增方向。
    cld                                             # String operations increment
	#cld的作用是将direct flag标志位清零
    # Set up the important data segment registers (DS, ES, SS).

    xorw %ax, %ax                                   # Segment number zero
    #x寄存器就是eax寄存器的低十六位，使用xorw清零ax
    movw %ax, %ds                                   # -> Data Segment
    movw %ax, %es                                   # -> Extra Segment
    movw %ax, %ss                                   # -> Stack Segment
	#将段选择子清零
    # Enable A20:
    #  For backwards compatibility with the earliest PCs, physical
    #  address line 20 is tied low, so that addresses higher than
    #  1MB wrap around to zero by default. This code undoes this.
    #由于需要兼容早期pc，物理地址的第20位绑定为0，所以高于1MB的地址又回到了0x00000.好了，激活A20后，就可以访问所有4G内存了，就可以使用保护模式了。
	#由于历史原因A20地址位由键盘控制器芯片8042管理。所以要给8042发命令激活A20
#8042有两个IO端口：0x60和0x64， 激活流程位： 发送0xd1命令到0x64端口 --> 发送0xdf到0x60，done！
seta20.1:
    inb $0x64, %al                                  # Wait for not busy(8042 input buffer empty).
    testb $0x2, %al
    jnz seta20.1
	#发送命令之前，要等待键盘输入缓冲区为空，这通过8042的状态寄存器的第2bit来观察，而状态寄存器的值可以读0x64端口得到。
    movb $0xd1, %al                                 # 0xd1 -> port 0x64
    outb %al, $0x64                                 # 0xd1 means: write data to 8042's P2 port

seta20.2:
    inb $0x64, %al                                  # Wait for not busy(8042 input buffer empty).
    testb $0x2, %al
    jnz seta20.2

    movb $0xdf, %al                                 # 0xdf -> port 0x60
    outb %al, $0x60                                 # 0xdf = 11011111, means set P2's A20 bit(the 1 bit) to 1
#-----------------A20激活完成。--------------------------------------------------------------------------------
    # Switch from real to protected mode, using a bootstrap GDT
    # and segment translation that makes virtual addresses
    # identical to physical addresses, so that the
    # effective memory map does not change during the switch.
    #转入保护模式，这里需要指定一个临时的GDT，来翻译逻辑地址。这里使用的GDT通过gdtdesc段定义，它翻译得到的物理地址和虚拟地址相同，所以转换过程中内存映射不会改变
    #载入并设置gdt 一个简单的GDT表和其描述符已经静态储存在引导区中，载入即可
    lgdt gdtdesc
    #打开保护模式标志位，相当于按下了保护模式的开关。cr0寄存器的第PE位就是这个开关，通过CR0_PE_ON或cr0寄存器，将第0位置1
    movl %cr0, %eax
    orl $CR0_PE_ON, %eax
    movl %eax, %cr0
	#由于上面的代码已经打开了保护模式了，所以这里要使用逻辑地址，而不是之前实模式的地址了。
    # Jump to next instruction, but in 32-bit code segment.
    # Switches processor into 32-bit mode.
    ljmp $PROT_MODE_CSEG, $protcseg
	#这里用到了PROT_MODE_CSEG, 他的值是0x8。根据段选择子的格式定义，0x8就翻译成：
　#　　　　　　　INDEX　　　　　　　　 TI CPL
　　　#　0000 0000 0000 1000
#INDEX代表GDT中的索引，TI代表使用GDTR中的GDT， CPL代表处于特权级。

#PROT_MODE_CSEG选择子选择了GDT中的第1个段描述符。这里使用的gdt就是变量gdt，下面可以看到gdt的第1个段描述符的基地址是0x0000,所以经过映射后和转换前的内存映射的物理地址一样。
.code32                                             # Assemble for 32-bit mode
protcseg:
    # Set up the protected-mode data segment registers
    movw $PROT_MODE_DSEG, %ax                       # Our data segment selector
    #重新初始化各个段寄存器。
    movw %ax, %ds                                   # -> DS: Data Segment
    movw %ax, %es                                   # -> ES: Extra Segment
    movw %ax, %fs                                   # -> FS
    movw %ax, %gs                                   # -> GS
    movw %ax, %ss                                   # -> SS: Stack Segment

    # Set up the stack pointer and call into C. The stack region is from 0--start(0x7c00)
    #栈顶设定在start处，也就是地址0x7c00处，call函数将返回地址入栈，将控制权交给bootmain，进入boot主方法
    movl $0x0, %ebp
    movl $start, %esp
    call bootmain

    # If bootmain returns (it shouldn't), loop.
spin:
    jmp spin

# Bootstrap GDT 一个简单静态的全局描述符表
.p2align 2                                          # force 4 byte alignment
gdt:
    SEG_NULLASM                                     # null seg
    SEG_ASM(STA_X|STA_R, 0x0, 0xffffffff)           # code seg for bootloader and kernel
    SEG_ASM(STA_W, 0x0, 0xffffffff)                 # data seg for bootloader and kernel

gdtdesc:
    .word 0x17                                      # sizeof(gdt) - 1
    .long gdt                                       # address gdt

```


## [练习4]
分析bootloader加载ELF格式的OS的过程。

```
	/* bootmain - the entry of bootloader */
void
bootmain(void) {
    // read the 1st page off disk
	//从设备扇区读取ELF
    readseg((uintptr_t)ELFHDR, SECTSIZE * 8, 0);

    // is this a valid ELF?
    if (ELFHDR->e_magic != ELF_MAGIC) {
        goto bad;
    }
    //ELF头部格式合法
    struct proghdr *ph, *eph;
    //描述符表的头地址放在ph

    // load each program segment (ignores ph flags)
    ph = (struct proghdr *)((uintptr_t)ELFHDR + ELFHDR->e_phoff);
    eph = ph + ELFHDR->e_phnum;

    for (; ph < eph; ph ++) {
        readseg(ph->p_va & 0xFFFFFF, ph->p_memsz, ph->p_offset);
        //每个Program Header描述的Segment加载到对应的虚拟地址
    }

    // call the entry point from the ELF header
    // note: does not return
    //从描述符表取出entry地址，跳转执行，将控制权交给ucore-os
    ((void (*)(void))(ELFHDR->e_entry & 0xFFFFFF))();

bad:
    outw(0x8A00, 0x8A00);
    outw(0x8A00, 0x8E00);

    /* do nothing */
    while (1);
}
```


## [练习5] 
实现函数调用堆栈跟踪函数 

由于堆栈是从高地址到低地址，调用函数时候将返回值压入栈中，所有
ss:ebp指向的堆栈位置储存着caller的ebp.
ss:ebp+4指向caller调用时的eip,
ss:ebp+8等是（可能的）参数列表。

输出中，堆栈最深一层为
```
	ebp:0x00007bf8 eip:0x00007d68 args: 0xc031fcfa 0xc08ed88e 0x64e4d08e 0xfa7502a8 
    <unknow>: -- 0x00007d67 --

```

其对应的是第一个使用堆栈的函数，bootmain.c中的bootmain。
bootloader设置的堆栈从0x7c00开始，使用"call bootmain"转入bootmain函数。
call指令压栈，所以bootmain中ebp为0x7bf8。

## [练习6]
完善中断初始化和处理

[练习6.1] 中断向量表中一个表项占多少字节？其中哪几位代表中断处理代码的入口？

中断向量表一个表项占用8字节，其中2-3字节是段选择子，0-1字节和6-7字节拼成偏移，
中断服务例程入口地址 = 基址+偏移。
中断号查idt得到段选择子+偏移。
依据段选择子查找GDT中的段描述符表，从而得到基址。

[练习6.2] 请编程完善kern/trap/trap.c中对中断向量表进行初始化的函数idt_init。
```
extern uintptr_t __vectors[];
    int i;
    for (i = 0; i < sizeof(idt) / sizeof(struct gatedesc); i ++) {
        SETGATE(idt[i], 0, GD_KTEXT, __vectors[i], DPL_KERNEL);
    }
    // DPL_KERNEL is kernel text 优先级
    //GD_KTEXT 为段选择子
    //__vectors[i] 为vector.s规定的偏移
	// set for switch from user to kernel
    SETGATE(idt[T_SWITCH_TOK], 0, GD_KTEXT, __vectors[T_SWITCH_TOK], DPL_USER);
	// load the IDT
    lidt(&idt_pd);
```
[练习6.3] 请编程完善trap.c中的中断处理函数trap，在对时钟中断进行处理的部分填写trap函数
```
switch (tf->tf_trapno) {
    case IRQ_OFFSET + IRQ_TIMER:
        /* LAB1 YOUR CODE : STEP 3 */
        /* handle the timer interrupt */
        /* (1) After a timer interrupt, you should record this event using a global variable (increase it), such as ticks in kern/driver/clock.c
         * (2) Every TICK_NUM cycle, you can print some info using a funciton, such as print_ticks().
         * (3) Too Simple? Yes, I think so!
         */
        ticks ++;
        if (ticks % TICK_NUM == 0) {
            print_ticks();
        }
        break;
```

## [练习7]
从此处开始，非本人独立完成。
增加syscall功能，即增加一用户态函数（可执行一特定系统调用：获得时钟计数值），
当内核初始完毕后，可从内核态返回到用户态的函数，而用户态的函数又通过系统调用得到内核态的服务

在idt_init中，将用户态调用SWITCH_TOK中断的权限打开。
	SETGATE(idt[T_SWITCH_TOK], 1, KERNEL_CS, __vectors[T_SWITCH_TOK], 3);

在trap_dispatch中，将iret时会从堆栈弹出的段寄存器进行修改
	对TO User
```
	    tf->tf_cs = USER_CS;
	    tf->tf_ds = USER_DS;
	    tf->tf_es = USER_DS;
	    tf->tf_ss = USER_DS;
```
	对TO Kernel

```
	    tf->tf_cs = KERNEL_CS;
	    tf->tf_ds = KERNEL_DS;
	    tf->tf_es = KERNEL_DS;
```

在lab1_switch_to_user中，调用T_SWITCH_TOU中断。
注意从中断返回时，会多pop两位，并用这两位的值更新ss,sp，损坏堆栈。
所以要先把栈压两位，并在从中断返回后修复esp。
```
	asm volatile (
	    "sub $0x8, %%esp \n"
	    "int %0 \n"
	    "movl %%ebp, %%esp"
	    : 
	    : "i"(T_SWITCH_TOU)
	);
```

在lab1_switch_to_kernel中，调用T_SWITCH_TOK中断。
注意从中断返回时，esp仍在TSS指示的堆栈中。所以要在从中断返回后修复esp。
```
	asm volatile (
	    "int %0 \n"
	    "movl %%ebp, %%esp \n"
	    : 
	    : "i"(T_SWITCH_TOK)
	);
```

但这样不能正常输出文本。根据提示，在trap_dispatch中转User态时，将调用io所需权限降低。
```
	tf->tf_eflags |= 0x3000;
```
