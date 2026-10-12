# lecture-workbench

把讲义变成**单个、离线可用的 HTML 学习页**：双击打开即可高亮、写批注、看术语卡、刷抽认卡和选择题。不需要服务器、CDN 或安装。

[在线示例](https://joshuaviolet.github.io/lecture-workbench/) · [架构说明（英文）](docs/architecture.md) · [English README](README.md)

> 状态：**v0.2，早期版本**。最初是我为自己的大学课程写的工具，现在整理成可复用的框架。页面界面支持简体中文（默认）和英文。未解决的问题见 [KNOWN_ISSUES.md](KNOWN_ISSUES.md)。

## 功能

- **高亮与批注**：刷新后不丢，划选范围跨过加粗或术语标签也能正确保存。按讲义分别存在浏览器本地，可导出/导入 JSON，或复制为 Markdown。
- **术语卡**：悬停显示音标、重读拼读、词源和记忆提示，可用系统语音朗读。
- **抽认卡与选择题**：每次渲染都会打乱选项顺序，学生没法靠「答案总在 B」或「最长的就是对的」答题。
- **教学组件**：章节主线、证据 / 限制 / 易混淆 / 迁移块、研究卡。
- **打印模式**：强制浅色，并在末尾附上自测清单和答案。
- 暗色模式、可收起目录、阅读进度、键盘操作、减弱动态效果。

## 快速开始

需要 Python 3.9+ 和 Node.js（验证器用 Node 检查页面脚本语法、审计术语卡覆盖）。

```bash
git clone https://github.com/JoshuaViolet/lecture-workbench.git
cd lecture-workbench
python3 framework/cli.py build --all --validate
open subjects/demo-binary-search/Binary_Search_Demo.html
```

## 命令

`framework/cli.py` 有三个子命令：

```bash
python3 framework/cli.py new subjects/my-lecture --title "My Lecture"   # 新建一个科目
python3 framework/cli.py build subjects/my-lecture --validate           # 构建并检查页面
python3 framework/cli.py validate subjects/my-lecture --strict          # 检查已经构建好的页面
```

- `new <文件夹> [--title 标题] [--doc-id ID] [--output 文件名.html]`：生成 `config.json`、`content.html`、`data.json`，正文、术语卡、抽认卡、选择题各带一个示例，不改也能构建并通过 `--strict` 检查。不指定时，`doc_id` 和输出文件名由文件夹名推出；文件夹名没有英文字母或数字（比如「线性代数」）时需要手动给 `--doc-id` 和 `--output`。目标文件夹非空、或 `doc_id` 已被同级目录或 `subjects/` 下的其他科目占用时会拒绝。
- `build (<文件夹>... | --all) [--validate] [--strict]`：把科目构建成单文件页面，某个科目失败也会继续构建其余的。`--all` 构建 `subjects/` 下所有带 `config.json` 的文件夹。
- `validate (<文件夹> | <页面.html>) [--strict]`：检查已构建的页面；给文件夹时检查 `config.output` 指定的那个文件。

失败时退出码非零，可以直接放进 CI。`framework/build_guide.py` 和 `framework/validate_guide.py` 仍可单独运行，参数不变。

## 写一个科目

在 `subjects/` 下建一个文件夹（`cli.py new` 会帮你建好），放四样东西：

- `config.json`：标识、标题、页头和目录 HTML、输出文件名。`doc_id` 是本地存储的命名空间，各讲义之间不能重复，开始使用后也不要再改。可选的 `lang` 决定页面自身界面（工具栏、目录、提示、打印页）的语言：`"zh"` 为简体中文（默认），`"en"` 为英文；正文用什么语言由你决定。界面文字都在 `framework/ui_strings.json` 里。
- `content.html`：正文，由若干 `<section>` 组成。
- `data.json`：`flashcards`、`mcqData`、`termLexicon` 三个数组。构建时会逐条校验，报错会指出具体是哪一项、哪个字段。
- `assets/`：正文引用的图片（可选）。

完整字段示例见英文 README。旧版 `data.js` 可以用 `python3 framework/migrate_datajs.py subjects/<名字>` 转换。

## 验证

`cli.py build --validate`（或 `cli.py validate`）会检查生成页面的结构（锚点、元素 id、事件函数、标签配对、脚本语法）和内容（LaTeX 残留、图片、术语卡覆盖），并对选择题做教学质量检查：正确选项是否经常是最长的一个、答案是否集中在同一个字母、是否有重复题目。质量检查默认只给警告，加 `--strict` 会让它变成失败。

## 开发

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium   # 或设置 PW_CHANNEL=chrome 使用已安装的 Chrome
.venv/bin/pytest
```

## 许可证

[MIT](LICENSE)

## 致谢

开发过程中使用了 AI 辅助（Claude）。
