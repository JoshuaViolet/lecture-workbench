        const flashcards = [
          {front:"二分查找每一步凭什么能丢掉一半？",back:"数组有序：中间元素比目标小，说明它左边的元素全都更小，目标只可能在右半边。没有有序性，这一步推理就不成立。"},
          {front:"二分查找的循环不变式是什么？它有什么用？",back:"如果目标在数组中，它一定在 [lo, hi] 内。每次只丢掉已证明不可能的部分，所以不变式保持；区间为空时就能断定目标不存在。"},
          {front:"n 个元素，二分查找最坏要比较几次？",back:"⌊log₂ n⌋ + 1 次。一百万个元素最多 20 次，因为 2²⁰ ≥ 1,000,000。n 翻倍只多 1 次。"},
          {front:"什么时候先排序再二分反而不划算？",back:"只查一次的时候。排序 O(n log n) 已经比一次线性扫描 O(n) 贵；排好一次、查很多次，二分才划算。"},
          {front:"为什么链表上不用二分查找？",back:"链表没有随机访问，走到中间就要 O(n) 步，每次「看中间」的代价抵消了减半的好处。"},
          {front:"判断一个新问题能否二分，关键看什么？",back:"一次检查能否把候选分成「一定不在这边」和「可能在那边」，也就是答案对检查结果单调。猜数字、git bisect 都满足。"}
        ];

        const mcqData = [
          {q:"在有序数组中找 42，第一次比较时中间元素是 23。接下来应该怎么做？",opts:["把查找范围缩到左半边，因为 23 更小","继续逐个检查 23 两侧的元素","把查找范围缩到 23 右边的那一半","重新从数组开头做一次线性查找"],ans:2,exp:"23 &lt; 42 且数组有序，所以 23 及其左边全都小于 42，目标只可能在右半边，令 lo = mid + 1。选左半边是把大小方向弄反了。"},
          {q:"对一个没有排序的数组执行二分查找，最可能出现什么结果？",opts:["可能把确实存在的元素报告为找不到","程序一定会抛出异常并停止运行","结果正确，只是比排序后慢一些","会自动退化成线性查找，结果仍正确"],ans:0,exp:"二分查找不检查前提，不会报错。但「丢掉一半」的推理依赖有序性，在无序数据上被丢掉的一半里可能正有目标，于是返回找不到。"},
          {q:"数组从 1,000 个元素增加到 1,000,000 个，二分查找的最坏比较次数大约怎样变化？",opts:["也变成原来的 1,000 倍左右","大约变成原来的 2 倍，从 10 次到 20 次","大约变成原来的 log₂ 1000 倍","保持不变，因为每次都只看中间元素"],ans:1,exp:"最坏次数是 ⌊log₂ n⌋ + 1：1,000 个元素是 10 次，1,000,000 个元素是 20 次。n 乘以 1,000 ≈ 2¹⁰，比较次数只增加约 10 次。"},
          {q:"把 lo = mid + 1 写成 lo = mid 后，下面哪种情况会让循环永远不结束？",opts:["数组为空，lo 大于 hi 的时候","目标恰好位于数组正中间的时候","目标比数组里所有元素都小的时候","lo 与 hi 相邻且 items[lo] 小于目标"],ans:3,exp:"lo 与 hi 相邻时 mid = lo；若 items[lo] 小于目标，执行 lo = mid 后区间没有缩小，下一轮完全重复。正确写法必须让区间每轮严格变小。"},
          {q:"数据无序，你只需要查找一次。哪种做法总代价最低？",opts:["直接线性扫描一遍，代价是 O(n)","先排序再二分，因为二分是 O(log n)","先排序再线性扫描，因为排序后更快","把数据放进链表后再做二分查找"],ans:0,exp:"先排序要 O(n log n)，已经超过一次线性扫描的 O(n)。二分查找的优势来自排好一次之后多次查询，单次查询不划算。"},
          {q:"用 git bisect 定位引入 bug 的提交，需要满足哪个前提才可靠？",opts:["每个提交修改的文件数量大致相同","bug 一旦出现，之后的每个版本都稳定复现","提交历史必须按作者名字排好顺序","每次测试都必须在同一台机器上进行"],ans:1,exp:"二分依赖单调性：从某个提交开始一直是坏的。只有这样，测一个中间版本才能可靠地丢掉一半历史。bug 时有时无时，一次测试的结论不足以排除任何一半。"}
        ];

        const termLexicon = [
          {keys:["binary search"],term:"Binary search 二分查找",ipa:"/ˈbaɪnəri sɜːtʃ/",chunks:"BI-na-ry SEARCH",parts:"binary 源自拉丁语 <strong>bini</strong>（两个一组）；指每次把候选一分为二。",hook:"每比较一次，候选减半。"},
          {keys:["linear search"],term:"Linear search 线性查找",ipa:"/ˈlɪniə sɜːtʃ/",chunks:"LIN-e-ar SEARCH",parts:"linear 源自拉丁语 <strong>linea</strong>（线）；沿着一条线逐个检查。",hook:"从头到尾一个个看。"},
          {keys:["sorted array"],term:"Sorted array 有序数组",ipa:"/ˈsɔːtɪd əˈreɪ/",chunks:"SOR-ted a-RAY",parts:"array 经古法语 <strong>areer</strong>（排列）而来。",hook:"二分查找的第一个前提。"},
          {keys:["invariant","loop invariant"],term:"Invariant 不变式",ipa:"/ɪnˈveəriənt/",chunks:"in-VAIR-i-ant",parts:"<strong>in-</strong>（不）+ variant（变化的，源自拉丁语 variare）。",hook:"每一轮循环前后都成立的断言。"},
          {keys:["logarithmic time","logarithm"],term:"Logarithmic time 对数时间",ipa:"/ˌlɒɡəˈrɪðmɪk taɪm/",chunks:"lo-ga-RITH-mic TIME",parts:"logarithm 由 Napier 用希腊语 <strong>logos</strong>（比率）+ <strong>arithmos</strong>（数）造词。",hook:"规模翻倍，只多一步。"},
          {keys:["random access"],term:"Random access 随机访问",ipa:"/ˈrændəm ˈækses/",chunks:"RAN-dom AC-cess",parts:"random 在这里指「任意位置」，不是「随机抽取」。",hook:"一步跳到任意下标。"},
          {keys:["off-by-one error","off by one error"],term:"Off-by-one error 差一错误",ipa:"/ˌɒf baɪ ˈwʌn ˈerə/",chunks:"OFF-by-ONE ER-ror",parts:"字面意思是「差了一」：边界多算或少算一个。",hook:"<= 还是 <？mid 要不要 ±1？"}
        ];
