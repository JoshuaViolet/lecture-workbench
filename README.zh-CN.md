# lecture-workbench

把讲义变成**单个、离线可用的 HTML 学习页**：双击打开即可高亮、写批注、看术语卡、刷抽认卡和选择题。不需要服务器、CDN 或安装。图片也嵌在页面里，所以不管是邮件发出、网页下载还是拷到手机上，学生拿到这一个文件就够了。

[在线示例](https://joshuaviolet.github.io/lecture-workbench/) · [架构说明（英文）](docs/architecture.md) · [English README](README.md)

> 状态：**v0.3，早期版本**。最初是我为自己的大学课程写的工具，现在整理成可复用的框架。页面界面支持简体中文（默认）和英文。未解决的问题见 [KNOWN_ISSUES.md](KNOWN_ISSUES.md)。

## 功能

- **高亮与批注**：正文各处都能划（段落、列表、表格、定义列表、代码），刷新后不丢；划选范围跨过加粗或术语也能正确保存。按讲义分别存在浏览器本地；可导出 JSON 备份，在另一台设备上导入（导入时选择「合并」保留本机已有的，或「覆盖」换成备份里的），或按阅读顺序复制为 Markdown。同时开两个标签页不会互相覆盖，批注写到一半点到别处也不会丢。
- **术语卡**：悬停显示音标、重读拼读、词源和记忆提示，可用系统语音朗读（自动挑本机已安装的英文语音）。
- **抽认卡与选择题**：每次渲染都会打乱选项顺序，学生没法靠「答案总在 B」答题；题目可以附一段按原样显示的代码。页面记得每道题上次答对还是答错，可以只练上次答错的题。
- **图片**：引用科目文件夹里的图片，构建时嵌进页面；点击可放大。
- **教学组件**：章节主线、证据 / 限制 / 易混淆 / 迁移块、研究卡。
- **打印模式**：强制浅色，折叠的内容展开打印；讲义有抽认卡或选择题时，末尾附上自测清单和答案。
- 在不运行脚本的地方打开（有些邮件和文件预览就是这样），页面会说明原因，直接展开理解检查的答案，并隐藏用不了的按钮。
- 页面配色默认跟随系统（页面开着时系统切换也会跟着变），也可以在目录栏里固定为亮色或暗色；目录标出正在读的章节、适配手机（宽表格可以左右滑动）、阅读进度、键盘操作、减弱动态效果。

## 快速开始

需要 Python 3.9+。建议装 Node.js：验证器用它检查页面脚本语法、审计术语卡覆盖；没有 Node 时这两项会跳过，并在结果里说明。

```bash
git clone https://github.com/JoshuaViolet/lecture-workbench.git
cd lecture-workbench
python3 framework/cli.py build --all --validate
open subjects/demo-binary-search/Binary_Search_Demo.html   # macOS；其他系统直接双击这个文件
```

## 命令

`framework/cli.py` 有三个子命令：

```bash
python3 framework/cli.py new subjects/my-lecture --title "My Lecture"   # 新建一个科目（英文界面加 --lang en）
python3 framework/cli.py build subjects/my-lecture --validate           # 构建并检查页面
python3 framework/cli.py validate subjects/my-lecture --strict          # 检查已经构建好的页面
```

- `new <文件夹> [--title 标题] [--doc-id ID] [--output 文件名.html] [--lang zh|en]`：生成 `config.json`、`content.html`、`data.json`，正文、术语卡、抽认卡、选择题各带一个示例（按界面语言写成中文或英文，默认中文），不改也能构建并通过 `--strict` 检查。不指定时，`doc_id` 和输出文件名由文件夹名推出；文件夹名没有英文字母或数字（比如「线性代数」）时需要手动给 `--doc-id` 和 `--output`。目标文件夹非空、或 `doc_id` 已被同级目录或 `subjects/` 下的其他科目占用时会拒绝。
- `build (<文件夹>... | --all) [--validate] [--strict]`：把科目构建成单文件页面并报告文件大小，某个科目失败也会继续构建其余的。`--all` 构建 `subjects/` 下所有带 `config.json` 的文件夹。
- `validate (<文件夹> | <页面.html>) [--strict]`：检查已构建的页面；给文件夹时检查 `config.output` 指定的那个文件。

失败时退出码非零，可以直接放进 CI。`framework/build_guide.py` 和 `framework/validate_guide.py` 仍可单独运行，参数不变。

## 写一个科目

在 `subjects/` 下建一个文件夹（`cli.py new` 会帮你建好），放四样东西（文件都用 UTF-8 保存，带不带 BOM 都行；GBK 等其他编码会构建失败，并指出是哪一行）：

- `config.json`：标识、标题、页头和目录 HTML、输出文件名。`doc_id` 是本地存储的命名空间，各讲义之间不能重复，开始使用后也不要再改。可选的 `lang` 决定页面自身界面（工具栏、目录、提示、打印页）的语言：`"zh"` 为简体中文（默认），`"en"` 为英文；正文用什么语言由你决定。界面文字都在 `framework/ui_strings.json` 里。
- `content.html`：正文，由若干 `<section>` 组成。
- `data.json`：`flashcards`、`mcqData`、`termLexicon` 三个数组。构建时会逐条校验，报错会指出具体是哪一项、哪个字段。选择题的选项每次渲染都会打乱，需要固定顺序的题写 `"shuffle": false`；考代码的题把代码放在可选的 `"code"` 字段里，会在题干下方按等宽字体原样显示（保留换行和缩进），含换行（`\n`）的选项也按代码显示。看图题把图放进 `"fig"`（`assets/` 里的图片文件），并用 `"fig_alt"` 说明图里画了什么：构建时会嵌进页面，图显示在题干下方，点击可放大，打印时随答案一起印出。
- `assets/`：正文引用的图片（可选）。构建时会把图片以 `data:` URI 嵌进页面，生成的 HTML 单独拿走也能显示；引用的图片不存在会直接构建失败。`config.json` 里写 `"embed_images": false` 可以关掉嵌入，但那样页面就必须和 `assets/` 一起分发。图片写法见 [examples/README.md](examples/README.md)；幻灯片截图建议用 JPEG 或 WebP，页面超过 25 MB 时构建会提示。

完整字段示例见英文 README。正文和题目怎么写（核心块顺序、题型、哪些内容不进页面）见 [AGENTS.md](AGENTS.md)，另有[心理学](docs/writing/psychology.md)、[经济学](docs/writing/economics.md)和[数据科学 / 编程](docs/writing/data-science.md)的分科补充（英文），可以直接交给帮你起草科目的 AI 助手。旧版 `data.js` 可以用 `python3 framework/migrate_datajs.py subjects/<名字>` 转换。

## 验证

`cli.py build --validate`（或 `cli.py validate`）会检查生成页面的结构（锚点、元素 id、事件函数、标签配对、脚本语法）、离线可用性（指向的本地文件必须存在；页面要从网络加载的东西，比如 CDN 脚本、网络字体、外链图片、iframe，离线时显示不出来，会给出警告但不算失败；需要额外文件才能显示时也给出提醒）和内容（正文和题目里的 LaTeX 残留，代码和「$5 到 $10」这类金额不算；术语卡覆盖：标成 `span.en` 的术语都要有卡，中文界面的讲义里加粗的英文也算术语，英文界面里加粗只当强调），并对选择题做教学质量检查：正确选项是唯一最长项的题是否超过 40%、题干里是否带题型标签（如 `Mechanism: …`、`自编·限制`）、解析是否用字母指代已打乱的选项、固定顺序的题答案是否集中在同一个字母、是否有重复题目。质量检查默认只给警告，加 `--strict` 会让它变成失败。

## 开发

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium   # 或设置 PW_CHANNEL=chrome 使用已安装的 Chrome
.venv/bin/pytest
```

发版：先开一个 PR，把 [CHANGELOG.md](CHANGELOG.md) 里的 `## Unreleased` 改成新版本号（如 `## 0.4.0`），并更新两份 README 的状态行；合并后启动 Release workflow，两种方式任选：不用 git、手机上也行的，在 **Actions → Release → Run workflow** 里选 `main`、填版本号（如 `0.4.0`），它会给 `main` 的最新提交打标签；或者给合并提交打标签并推送（`git tag v0.4.0 <合并提交> && git push origin v0.4.0`）。workflow 会自动发布 GitHub Release，说明就是 CHANGELOG 里该版本那一节；CHANGELOG 里没有对应版本的不会发布任何东西。在 Releases 页面手动发布的版本，workflow 会原样保留、不再报错。

## 许可证

[MIT](LICENSE)

## 致谢

开发过程中使用了 AI 辅助（Claude）。
