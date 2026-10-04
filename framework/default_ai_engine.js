// 通用默认本地推理引擎（当科目目录没有 ai_engine.js 时由 build_guide.py 注入）
// 只依赖模板保证的全局量: psycDict 数组 / lastDiscussedTopic 变量
// 数据形状契约: psycDict 条目 = { term, keys[], lecture, def, caution }
        function generateComprehensiveLocalAIResponse(rawQuery) {
            const q = (rawQuery || "").trim();
            const lowerKey = q.toLowerCase();

            // 1) 追问：有上下文 + 追问意图词 → 就当前话题补充学习路径
            const isFollowUp = /为什么|展开|再解释|详细说|举个例子|why|more detail|example/i.test(q);
            if (isFollowUp && lastDiscussedTopic) {
                const cur = psycDict.find(d => (d.keys || []).some(k => k === lastDiscussedTopic));
                if (cur) {
                    return `<h4>🔁 接着「${cur.term}」往下挖</h4>
            <p>${cur.def}</p>
            <p><strong>建议的追问路径：</strong>① 它上游的机制是什么？② 有什么实验证据（方法+结果）？③ 常见误解/考试陷阱是什么？</p>
            <div class="ai-tip">💡 提示：直接输入下一个概念名即可切换话题；问"X 和 Y 的区别"也能获得对照式回答。</div>`;
                }
            }

            // 2) 词典命中（含反向匹配，长度≥2 守卫防止单字母误命中）
            const hit = psycDict.find(d => (d.keys || []).some(k =>
                lowerKey.includes(k) || (lowerKey.length >= 2 && k.includes(lowerKey))));
            if (hit) {
                lastDiscussedTopic = hit.keys[0];
                return `<h4>📖 ${hit.term}</h4>
        <p>${hit.def}</p>
        ${hit.caution ? `<div class="ai-warning">⚠️ <strong>易错提示：</strong>${hit.caution}</div>` : ""}
        <p style="color: var(--text-muted); font-size: 0.8rem;">（离线词典 · 不是 Grok。启动学习助手后可连 SuperGrok 追问。）</p>`;
            }

            // 3) 未命中：学习引导 + 可问话题样例
            const sample = psycDict.slice(0, 6).map(d => d.term).join("、");
            lastDiscussedTopic = null;
            return `<h4>🤔 本地词库暂未覆盖这个问题</h4>
    <p>你可以：① 换个关键词（通常是概念英文名或中文术语）再试；② 双击启动学习助手，用 Grok 依据本讲资料追问。</p>
    <p><strong>本地词库示例话题：</strong>${sample} …（共 ${psycDict.length} 条）</p>`;
        }
