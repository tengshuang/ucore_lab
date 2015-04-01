# Lab2 report

## [练习1]
实现 first-fit 连续物理内存分配算法

1-0 设计实现过程

1）首先看视频关于first-fit算法的部分，充分理解first-fit算法
2）阅读注释中的提示后，理解list.h中关于链表基本操作。
3）阅读实验指导书相关部分，理解page与物理内存之间到关系，freelist，page-link等变量的意义，明白此处没有段表相关的内容，此处做好了准备工作。
4）仔细阅读default_init default_init_memmap default_alloc_pages
default_free_pages中的代码，并理解各个函数的含义与作用，然后修改default_alloc_pages完成此项练习。
```
//free_area 管理区描述符
//free_list 管理区描述符指针，指向page
static void
default_init(void) {
    list_init(&free_list); //指向页框块的双向循环链表free_list初始化
    nr_free = 0; //开始时空闲页框块总数为 0（未形成双向循环链表）
}
```
```
//使用参数 每个连续地址空闲块到起始页, 页个数初始化双向循环链表
static void
default_init_memmap(struct Page *base, size_t n) {
    assert(n > 0);
    struct Page *p = base;
    //从base开始遍历所有页框块
    for (; p != base + n; p ++) {
        assert(PageReserved(p));
        p->flags = 0; //物理页未被kernel等占用
	SetPageProperty(p);
	p->property = 0; //连续的块的大小，head page设为n，否则为0
        set_page_ref(p, 0);//该页空闲且尚未被引用
	list_add_before(&free_list, &(p->page_link));//将初始完的页框块添加到双向循环链表freelist中
    }
    base->property = n;//以base为起始连续空间大小为n
    nr_free += n;//freelist中空闲页到个数
}
default_free_pages函数：
首先遍历链表，找到当前页需要插入的位置。然后将这n个页插入到当前位置前。
之后考虑是否需要进行合并操作。
如果base＋n＝p，那么需要和后面的页进行合并，那么只需要修改base和p的property的值即可。如果前面页和base相连，那么还需要向前进行合并，不断向前查找直到property不为0，修改该页和base页的property集合即可。
```
具体实现参见代码段注释。
5）克服链表指针混乱的错误，解决双向循环链表书写的问题。

1-1 你的first fit算法是否有进一步的改进空间？
```
在合并过程中需要向前不断遍历。可以在page中设立一个head表，每一段连续页空间中的页的head值都指向首个页，这样在向前查找时，直接命中。
```

## [练习2]
实现寻找虚拟地址对应的页表项

2-0 设计实现过程
```
1）阅读实验参考书，明确各个变量到意义。
如pde表示一级页表，pte表示二级页表等。
2）按照注释中给出的步骤修改完成get_pte函数。
具体实现为：
pde_t *pdep = pgdir+PDX(la);//在一级页表项中查找二级页表的物理内存页 la为逻辑地址
    if (!(*pdep & PTE_P)) {//如果二级页表项不存在 PTE_P = 1 表示物理内存存在
        struct Page *page;
        if (!create || (page = alloc_page()) == NULL) {
            return NULL; // 若不需要创建或者分配物理页失败，返回NULL 否则获得空白物理页给页表
        }
        set_page_ref(page, 1);//创建映射
        uintptr_t pa = page2pa(page); //得到这个path的物理地址
        memset(KADDR(pa), 0, PGSIZE); //物理地址清零
        //*pdep = page2pa(page) | PTE_USER //设置用户权限？
        *pdep = pa | PTE_U | PTE_W | PTE_P; //页表项的内容
    }
    //PDE_ADDR : pa + 0xC0000000
    return &((pte_t *)KADDR(PDE_ADDR(*pdep)))[PTX(la)]; //返回页表物理地址
```
2-1 请描述页目录项（Pag Director Entry）和页表（Page Table Entry）中每个组成部分的含义和以及对ucore而言的潜在用处。
```
1）lab1中断相关,得到相应的中断,准备好中断栈,
2)设置相应权限
#define T_PGFLT 14 // page fault
3）进入中断执行段.如果再次缺失,则会发出double fault.如果顺利会将需要的页换进内存(调用相关算法),调用page_remove,page_insert(会诉继续调用get_pte),然后返回新的页.
```
2-2 如果ucore执行过程中访问内存，出现了页访问异常，请问硬件要做哪些事情？
```
会出现 #define T_DBLFLT 8 // double fault 的异常后退出系统.
```

## [练习3]
释放某虚地址所在的页并取消对应二级页表项的映射

3-0 设计实现过程
```
按照注释中给出的步骤修改完成page_remove_pte函数。
if (*ptep & PTE_P) { //如果二级页表存在
        struct Page *page = pte2page(*ptep);//找到对应page
        if (page_ref_dec(page) == 0) {//减少后到ref变为0表示无映射可以释放
            free_page(page);
        }
        *ptep = 0;//清空ptep
        tlb_invalidate(pgdir, la);//更新快表
    }
```
3-1 数据结构Page的全局变量（其实是一个数组）的每一项与页表中的页目录项和页表项有无对应关系？如果有，其对应关系是啥？
```
有,阅读实验参考书：npage是与最大的物理内存相关,ends是bootloader结束标志,通过ROUNDUP找到第一张可以使用的页,给内核态使用的空间.设置空闲物理空间。
uintptr_t freemem = PADDR((uintptr_t)pages + sizeof(struct Page) * npage);pages指向的是可管理的物理内存空间的起始页。
通过查询pde,pte之后再加上偏移得到是KADDR。
```
3-2 如果希望虚拟地址与物理地址相等，则需要如何修改lab2，完成此事？
```
更改PADDR和KADDR函数的返回值，去掉+- KERNBASE的部分。
```
#与参考答案的区别：
参考标准答案进行实现，first-fit算法的双向链表指针的实现有点区别。
get_te的函数指针和引用有一定的差别。
#重要的知识点：
1）first-fit算法。
2）线性地址与物理地址的转换。
3）物理内存的页式管理。
4）页表的添加、删除操作。
