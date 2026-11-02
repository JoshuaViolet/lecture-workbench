# 教学组件：使用说明

使用 `teaching-components.html` 作为可复制正文片段。它只依赖 `framework/src/css/teaching.css` 中的样式；直接打开片段不会得到完整框架外观；要看完整效果，把片段粘进某个科目的 `content.html` 再构建。

## 选择与位置

- `.teaching-block` 搭配 `.phenomenon-block`、`.evidence-block`、`.limitation-block`、`.misconception-block` 或 `.transfer-block`。真实文本标签分别为“现象、证据、限制、易混淆、迁移”。只使用有教学需要的块，不要求每节套满五种。套满五种块不是覆盖「详尽」的条件，只增加预习负荷。
- `.chapter-spine` 使用 `dl/dt/dd`，紧接章节标题，位于正文前；顺序固定为“本讲问题、关键证据、要解释的机制、迁移目标”。桌面两列，600px 及以下单列。
- 简短观察使用 `.evidence-block`；完整研究设计使用 `article.study-card`。不要把研究卡嵌入证据块或反向嵌套。
- 标题按页面语义层级填写：章节为 h2、小节为 h3 时，卡片标题用 h4。标签是普通文本，不另增标题级别。
- 支持段落、列表、现有 figure/slide-grid 图片组件。图片仍按原规范提供 alt、说明和来源。
- 研究卡来源区可选；如果声明有真实来源却尚未查到，写“待核对”，不要虚构引用。样例均为虚构，不得作为课程事实直接复制。

## 最小标记

```html
<div class="teaching-block limitation-block">
    <span class="block-label">限制</span>
    <h4>这个结果不能说明什么？</h4>
    <p>填写证据边界。</p>
</div>

<dl class="chapter-spine" aria-label="本讲学习主线">
    <div><dt>本讲问题</dt><dd>填写问题。</dd></div>
    <div><dt>关键证据</dt><dd>填写比较或观察。</dd></div>
    <div><dt>要解释的机制</dt><dd>填写解释。</dd></div>
    <div><dt>迁移目标</dt><dd>填写新情境任务。</dd></div>
</dl>

<article class="study-card">
    <header><span class="study-label">研究证据</span><h4>研究名称</h4></header>
    <dl class="study-grid">
        <div><dt>研究问题</dt><dd>填写问题。</dd></div>
        <div><dt>关键操纵或比较</dt><dd>填写设计。</dd></div>
        <div><dt>主要结果</dt><dd>填写结果。</dd></div>
        <div><dt>支持的解释</dt><dd>填写推论。</dd></div>
        <div><dt>不能推出的结论</dt><dd>填写边界。</dd></div>
    </dl>
    <footer class="study-source">来源：待核对。</footer>
</article>
```

## 图片

图片放在科目文件夹的 `assets/` 下，用相对路径引用。构建时会把它们以 `data:` URI 嵌进页面，生成的 HTML 单独复制、发送也能显示图片；引用的文件不存在时构建失败并列出全部缺失项。网络图片（`https://…`）不会被下载嵌入，验证器会报「离线时打不开」，请先保存到 `assets/`。

```html
<figure class="slide-fig">
    <img src="assets/lecture3-s12.png" alt="描述图里画了什么，供读屏和图片加载失败时使用" loading="lazy">
    <figcaption>Lecture 3, S12：说明这张图要看什么。</figcaption>
</figure>
```

- `figure` 里的图片可以点击（或用键盘 Enter）放大，说明文字显示在大图下方。
- 幻灯片截图用 JPEG 或 WebP、宽度 1600px 左右即可；页面超过 25 MB 时构建会提示手机打开会慢。
- 确实想让图片留在页面外（例如几百张大图），在 `config.json` 里写 `"embed_images": false`；这样页面就不再是单个文件，必须和 `assets/` 一起分发，验证器会给出提醒。

## 主题、打印与兼容

- 复用框架现有颜色变量；无需科目 CSS、JS、新配置或新数据字段。
- 浅色、暗色和打印都有真实文本标签，不依赖底色表达含义。
- 打印时短卡优先保持完整；已知长卡在基础类后加 `allow-page-break`，允许自然分页。没有固定高度或裁切。打印中的网格退为纵向排列。
- 旧 callout 不自动转换。新增正式正文时保留已有 section ID；增加标题可能让已保存的高亮/批注容器索引漂移（引擎会按文本回退查找）。
- 改动框架后运行 `python3 framework/cli.py build --all --validate`，确认全部科目全绿。
