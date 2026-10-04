# lecture-workbench

把讲义变成**单个、离线可用的 HTML 学习页**：双击打开即可高亮、写批注、看术语卡、刷抽认卡和选择题。不需要服务器、CDN 或安装。

[在线示例](https://joshuaviolet.github.io/lecture-workbench/) · [架构说明（英文）](docs/architecture.md) · [English README](README.md)

> 状态：**v0.1，早期版本**。最初是我为自己的大学课程写的工具，现在整理成可复用的框架。页面界面目前是简体中文。未解决的问题见 [KNOWN_ISSUES.md](KNOWN_ISSUES.md)。

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
python3 framework/build_guide.py --all --validate
open subjects/demo-binary-search/Binary_Search_Demo.html
```

## 写一个科目

在 `subjects/` 下建一个文件夹，放四样东西：

- `config.json`：标识、标题、页头和目录 HTML、输出文件名。`doc_id` 是本地存储的命名空间，各讲义之间不能重复，开始使用后也不要再改。
- `content.html`：正文，由若干 `<section>` 组成。
- `data.json`：`flashcards`、`mcqData`、`termLexicon` 三个数组。构建时会逐条校验，报错会指出具体是哪一项、哪个字段。
- `assets/`：正文引用的图片（可选）。

完整字段示例见英文 README。旧版 `data.js` 可以用 `python3 framework/migrate_datajs.py subjects/<名字>` 转换。

## 验证

`build_guide.py --validate` 会检查生成页面的结构（锚点、元素 id、事件函数、标签配对、脚本语法）和内容（LaTeX 残留、图片、术语卡覆盖），并对选择题做教学质量检查：正确选项是否经常是最长的一个、答案是否集中在同一个字母、是否有重复题目。质量检查默认只给警告，加 `--strict` 会让它变成失败。

## 开发

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium   # 或设置 PW_CHANNEL=chrome 使用已安装的 Chrome
.venv/bin/pytest
```

## 许可证

[MIT](LICENSE)
