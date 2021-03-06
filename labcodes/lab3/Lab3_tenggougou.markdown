# Lab3 report

## [练习1] 给未被映射的地址映射上物理页

[练习1.1] 请描述页目录项（Pag Director Entry）和页表（Page Table Entry）中组成部分对ucore实现页替换算法的潜在用处。
>目录项(PDE): 用于从线性地址索引对应的页表项。
页表(PTE): 存放逻辑页与物理页帧的映射关系。
ucore通过页目录项和页表可以实现从线性地址到物理地址的映射。
同时还有过滤掉非法访问的页面的作用。

[练习1.2] 如果ucore的缺页服务例程在执行过程中访问内存，出现了页访问异常，请问硬件要做哪些事情？

> 
保存中断地址、中断号、寄存器、缺页信息等；
根据中断号调用缺页服务例程,换入上次出现异常的页面。
待缺页服务例程执行完毕后，重新执行该访存指令。 

## [练习2] 补充完成基于FIFO的页面替换算法

[练习2.1] 如果要在ucore上实现"extended clock页替换算法"请给你的设计方案，现有的swap_manager框架是否足以支持在ucore中实现此算法？如果是，请给你的设计方案。如果不是，请给出你的新的扩展和基此扩展的设计方案。并需要回答如下问题

- 需要被换出的页的特征是什么？
- 在ucore中如何判断具有这样特征的页？
- 何时进行换入和换出操作？

> 不是。每个页缺少一个需要维护的标记位（标记其是否被访问过），即没有对应于页面访问时触发的函数，因此页面替换算法无法得知页面是否倍访问过。
扩展方案：在FIFO的基础上面，利用页表项中的修改位和访问位，根据算法特性循环遍历列表。

与参考答案的区别： 具体实现略有不同，整体思路基本一致。

> - 修改位和访问位都是0 
> - 修改位可以利用页面的`PTE_D`标记。访问位和“时钟指针”由页面置换算法自行记录。在每次调用该页的时候将标记位设为1，每次缺页查询到该页的时候清除标记位。每次缺页查询时首个标记位为0的页应该被换出。
> - 发生缺页的同时系统分配的页面数已经饱和

## 与参考答案的区别：

> 具体实现略有不同，整体思路基本一致。 

## 重要的知识点

> FIFO PRA和局部页面替换FIFO算法。
思想上虽然属于同一算法，但是OS原理中，页面换入和换出是同时进行的。
实验中，页面换入是在`_fifo_map_swappable`中实现的，换出是在`_fifo_swap_out_victim`中实现的，非同时进行。
