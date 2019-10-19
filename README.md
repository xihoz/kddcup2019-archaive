# KDDCup2019

# 冠军方案经验总结

## 题目特点
在这次比赛中，主要有以下难点：

1.挖掘有效的特征

与传统数据挖掘竞赛不同的是，AutoML竞赛中，参赛选手只知道数据的类型（数值变量、分类变量、时间变量、多值分类变量等），而不知道数据的含义，这毫无疑问会增加特征工程的难度，如何挖掘到有效的通用特征成为一个难点。

2.赛题数据和时序相关

时序相关数据的数据挖掘难度较大，在传统的机器学习应用中，需要经验丰富的专家才能从时序关系型数据中挖掘出有效的时序信息，并加以利用提升机器学习模型的效果。即使具备较深的知识储备，专家也需要通过不断的尝试和试错，才能构建出有价值的时序特征，并且利用好多个相关联表来提升机器学习模型的性能。

3.赛题数据按照多表给出

赛题的数据是按照多表给出的，这就要求参赛选手能够构建一个处理多表之间多样的连接关系的自动化机器学习系统。多表数据无疑提升了对系统的稳定性的要求，稍有不慎，有可能合并出来的数据过于庞大就直接超时或者超内存而导致没有最终成绩。

4.时间内存限制严格

比赛代码运行环境是一个4核CPU，16G内存的docker环境，对于未知大小的数据集，在代码执行过程中的某些操作很容易使得内存峰值超过16G，导致程序崩溃。因此选手要严格优化某些操作，或使用采样等方式完成任务。此外，比赛方对于每个数据集严格限制了代码的执行时间，稍有不慎就会使得运行时间超时而崩溃。

## 解决方案
我们团队基于所给数据实现了一套支持多表的AutoML框架，包括自动多表合并、自动特征工程、自动特征选择、自动模型调参、自动模型融合等步骤，在时间和内存的控制上我们也做了很多优化工作。

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/1.png %}

## 数据预处理

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/2.png %}

我们通过对表结构及其属性的分析，针对不同类型的数据制定不同的数据预处理方案。首先，在多表间的多个连接key中，我们在主表中种类最多的一个key识别为user。基于识别出的user，可以尝试在主表的category中识别出session。另外，我们尝试在category数据中识别出只有两类有效值的binary数据。我们对category、user、session、key进行重新编码，对numerical数据尝试将其转换为占用内存更少的类型，将time数据转换为容易操作的datetime类型。

## 多表连接

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/3.png %}

比赛给的数据结构如上图所示，表和表之间的连接关系可以分为四种，分别是1-1、1-M、M-1、M-M。因为时间和内存的限制，所以我们需要在尽可能保留信息的同时，让最后生成的表的数据规模不至于过大。而处理多表连接的方式，直接影响到后面的结果。我们针对不同的连接方式采用了不同的方法。首先将四种连接方式分成了两种类型：类型1包含了1-1、M-1，类型2包含了1-M、M-M。对于类型1，我们可以直接将副表的数据通过key合并到主表上。对于类型2，我们首先对副表做一些聚集操作，生成聚集的结果，而这些聚集的结果可以理解为和主表是类型1的关系。接下来，我们只要对生成聚集的结果做类型1的操作，直接将其合并到主表上即可。并且，对于主表和副表都有时间戳的情况下，我们为了尽可能保留信息，将副表上离主表当前数据早且最近并且为相同key值的数据合并到主表上。

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/4.png %}

其具体操作可以见图示，key为147714011的数据项的n_1列的数据为3.6，连接到Main Table对应的147714011的所有数据项之上。

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/5.png %}

该图表示了类型2的连接方式，这个例子为对n_1列做了均值聚集操作，key为147714011的数据项在n_1列上的均值为2.3，之后就是将该数据对应合并到主表上。

## 采样
因为AutoML比赛方给定的数据集大小未知，在对其进行操作处理之前首先要判断当前环境是否能够支持整个数据集共同参与特征工程及模型训练过程。我们在读入数据进入预处理之前做了一次判断，即要求训练集与测试集的总样本数不超过某一个可以接受的阈值。如训练集与测试集的总样本数过多，我们就考虑对其进行采样，在当前给定的16G内存的条件下，我们经过估算，得到400万条数据是一个比较好的阈值。

此外，在特征工程的组合特征模块中，同样用到了采样的思想。组合特征的特点是产生的特征数量多，特征工程的时间长，内存峰值高，起作用的特征数量少。因此，为了避免内存溢出，我们在做组合特征之前，在小数据集上进行特征工程，经过筛选后得到真正有效的特征，再在整个数据集上仅做出这些有效的特征这样不仅可以减少系统运行时间也能避免爆内存的风险。

## 自动特征工程

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/6.png %}

特征工程部分往往是数据挖掘竞赛的关键核心内容，也是我们团队在竞赛中取得显著优势的重要因素。我们通过LightGBM模型来验证特征效果。我们将特征工程分成几个模块。第一个模块是基础特征部分，这一部分主要是针对user、key、session的统计特征，产生新特征的数目较少却有很好的效果，因此放在最先。第二模块是一阶组合特征部分，我们尝试将主表中较为重要的user、key、session与其余的numerical或categorical挑选出的数据进行组合，对某些数据集有非常好的效果。第三个是大量组合特征部分，我们对时间分桶，尝试使用时间桶对categorical和numerical数据进行组合，此外我们还根据不同数据集的数据量大小，筛选出适量的categorical或numerical数据两两组合形成新的特征，在希望挖掘到有用的特征的同时，尽量减小内存溢出的风险。最后的部分是有监督学习的CTR和均值编码特征，将其放在最后的原因是一方面在这一阶段会产生很多特征，容易造成生成过多的特征而导致爆内存；另一方面是我们认为这些特征和其他特征组合没有什么实际意义，因此将其放在最后不参与组合。同时，因为本次竞赛的时间和内存的控制比较严格，在面对百万级的数据量上，每个特征生成几乎都要控制在几秒内生成，为了满足这一要求，我们的代码加入了许多优化。比如对于类别数据在多类别数据中的位置这一特征，如果用传统的Pandas实现，时间会达到几个小时，而加入多线程之后，情况会有所改善，但是仍旧要消耗大量的时间。我们退而求其次，使用numpy来实现该特征，特征的生成时间直接到达了几十秒的级别，但是这仍旧不能满足我们的要求。最后我们对这块代码使用cython去优化，并且对cython代码进行精雕细琢，最后该特征的生成只需要几秒。

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/7.png %}

## 自动特征选择

在自动特征工程阶段，我们将特征工程分为多个阶段。在每一个模块结束后，我们都会做一次特征选择来筛掉那些在这一阶段做出的无效的特征，来避免内存溢出并且加速最终的模型训练。我们通过结合特征重要性及序列后向选择算法，设置一个阈值，将在参与模型训练中，筛出重要性较低的特征而尽可能小地损失模型精度。我们还尝试了基于特征的信息增益来对特征进行筛选，亦或是对两种筛选方法进行结合，但因为没能找到更好的切分点，最终还是使用了基于特征重要性的方法。

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/8.png %}

## 类别不平衡问题处理
我们对类别不平衡的数据在训练时做了处理。正负样本比例超过1:3时，我们采用欠采样的方式，缓和正负样本不平衡。此外，我们还尝试通过增加正样本的权重等方式来优化类别不平衡带来的问题。在模型融合的部分，我们在保留原始较少的正样本的同时，换一批负样本来进行训练，这样能够尽可能保留更多的原始数据的信息，同时缓解类别不平衡的问题。

## 模型融合
由于比赛环境对时间和内存做了严格的限制，我们在模型融合方面考虑了bagging、blending、stacking等方案，最终选用了使用bagging的方法。我们通过计算一个demo模拟真实数据集训练和预测来预估真实数据集所需要的时间，如时间不足则选择在训练时early-stop，允许精度上的损失来保证代码能够在规定时间内运行完毕。如时间充裕，则通过当前剩余时间计算允许多少个模型进行融合。为了保证代码通过，我们采用了保守估计的方式，即在计算出模型融合数量的基础上，选择少融合一个模型。

## 运行时间优化
我们的时间控制在各个过程中都有体现。

在自动化数据处理和自动化特征工程的过程中，我们使用Cython对编码以及一些生成效率较慢的特征进行加速。这里举一个特征为例，对于两列数据，一列为category类型的数据，一列为multi-category类型的数据，我们提前判断了两列数据的数据项集具有交集，我们要计算这一category列中的数据项在multi-category列对应的数据项集中的位置信息。比如说有有一条数据。data : [ 2137 ,  (134,2137,576,816) ] ，前者2137在后者的第2个位置上。所以这条数据该特征为2。如果没有出现的话，规定为0。对于这一特征，如果我们使用pandas提供的apply接口来实现，在本次竞赛的环境下，该类特征的生成需要大约几个小时的时间。考虑到DataFrame不适合做遍历，以及接口泛化性带来的性能上的损失。我们使用Numpy，做遍历来实现该特征，能够让特征的生成达到分钟级。而本次竞赛的时间和内存有严格的控制，像那些需要超过10秒才能生成的一类特征就算非常耗时的了。之后我们采用Cython，应用Cython提前编译，静态类型等机制我们将该特征的生成时间控制在了10秒内。其中生成该特征的过程中有一些细节。比如如果在Cython中继续使用Python原生类型，那么遍历的效率还是比较缓慢。但是multi-category类型的数据存储又不好离开Python原生类型的支持。考虑我们在生成特征的过程中，主要是对multi-category类型做遍历操作，所以可以使用一个数组去存储multi-category的每个数据项。并且用额外一个数组去保存每个multi-category的数据项集的长度。这样根据其长度数组和数据数组，我们就能做一个高效的遍历。在测试这段优化的过程中，纯粹的Python代码经过Cython优化，效率大概能到60秒。而经过这段优化，很轻松就能到达10秒内（测试环境就是以我们的本次计算机为主，线上环境会多一些时间）。

在模型集成部分，我们会做提前计算，记录到当前用时，通过训练模型几个轮次来计算出模型启动的时间以及模型训练每一轮数据所消耗的时间，通过这两个时间，我们能够预估出后续的参数调优，模型训练的时间。从而决定最后模型融合的数量。

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/9.png %}

## 运行内存优化
在内存控制方面，我们首先实现了一个内存的监听器。我们首先完整运行一轮我们的系统，记录下内存情况，对不同数据集的内存峰值进行分析。可以发现的是，内存峰值往往就出现在几个典型的地方。比如：数据合成时、在模型开始训练时、某些特征生成时。经过分析，可以概括为几个点，其中比较典型的是数据合成时，如果使用pandas的接口pandas.concat进行数据合并，其合并过程中，会生成大约两倍当前数据内存的量。这个是显然的，因为其合并返回的结果不是就地的，而是创建出第三块内存。因此，我们将合成的过程改为按列赋值，这样合并时就几乎不存在内存峰值了。但是这么做，同时会带来较差的时间效率。所以在系统的早期，内存比较宽松的情况下，我们仍旧采用pandas的接口来进行对数据的合并。

另外，我们同样对训练预测时内存的情况进行了提前计算，在最后的特征筛选的过程中，我们会计算模拟出在生成多大的数据量下，能够完整进行系统后续的过程。从而来控制最后筛选出来的数据量。并且在最后一次特征筛选前，生成特征时，我们也会先时候小数据集进行一个模拟过程，来计算出整个过程中的内存情况，来对生成期生成的特征数量进行一个控制。

最后，我们会做一些比较精细的内存管理，在变量生命周期结束的时候，我们都会对其进行内存回收。以下是我们内存优化前后的一个对比。里面包含了比赛中给的5个数据集的运行过程中的内存情况。

{%img https://github.com/xijunlee/KDDCup2019/blob/master/img/10.png %}

## 系统测试
对于系统的测试，我们分为了两个方面进行。第一个方面是测试系统的扩展性，第二个方面是测试系统的性能。

对于系统的扩展性，我们测试过如下：

对于不同的数据类型缺失的情况。

对于不同数据类型数值全为空的情况。

对于表的结构为单表、复杂多表的情况。

以及其他一系列的极限状态。

而对于系统的性能方面，我们测试过如下：

扩大数据的条目，就本次竞赛的5个数据集而言，我们扩展每个数据集数据条目2倍，3倍，6倍都能够在规定的时间和内存下顺利运行。

扩大数据的字段数量，同样，我们扩展5个数据集的字段数量2倍也能够顺利运行。

构造特定的数据集，观察是否会因为某些组合特征而系统崩溃。最后测试了大约数十个构造的极端数据集都能够运行成功。

限制数据集允许运行时间，我们通过调整数据集允许运行时间，观察我们的系统是否能够自适应调整自身的运行时间。我们调整本次竞赛中原本时间就比较紧张的A数据集以及数据量较大的B数据集，将其允许的运行时间变为原来的1/2，1/3，甚至是1/4。我们的系统都能够顺利运行。

## 总结
本次KDD Cup AutoML竞赛在赛制上得到进一步完善。相对于NeurIPS 2018 AutoML竞赛增加了一次AutoML阶段的提交次数，这样能够尽量保障参赛选手顺利跑通B榜数据。相对于PAKDD 2019 AutoML竞赛改进评分机制，最终得分只受各任务最高分的影响。完善后的竞赛机制让参赛选手得到更好的竞赛体验和技术发挥，感谢主办方的辛勤付出。

在这次竞赛中我们的工作围绕着竞赛的挑战而进行，主要有几个比较重要的过程：自动化多表数据处理、自动多表连接、自动化特征工程、自动化模型构建、选择和融合。同时为了满足竞赛的时间和内存的需求，我们在代码上做了相当多的优化，比如使用了多线程、Cython、预处理、提前估算等方法。最后我们的成绩相当不错，A，B榜单上均在多个任务集上有比较大的优势。

时序关系型数据在在线广告、推荐系统、金融市场分析等应用场景中十分常见。本次AutoML聚焦时序关系型数据，为参赛者提出了挑战，同时也为AutoML的发展提供了新的思路。近年来AutoML因为其高适应性、高效性、可扩展性、高可用性，在工业应用中可以大大降低应用门槛，在不同的场景中均可以发挥出用武之地，大大缩短项目开发周期。最后祝贺所有的Top队伍，愿大家在未来都能取得自己满意的成绩！

## 作者介绍
罗志鹏

深兰北京AI研发中心负责人，深兰科技机器学习科学家

硕士毕业于北大

获得过PAKDD，KDD，NeurIPS，CIKM，CVPR, SIGIR等顶级会议竞赛冠军，以一作发表KDD Oral一篇，共同一作WWW一篇，多年机器学习实战经验

开源链接
https://github.com/DeepBlueAI/AutoSmart