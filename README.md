# Alfred Open Obsidian

在 Alfred 中按笔记标题搜索指定 Obsidian 文档库，回车即可在 Obsidian 中打开对应笔记。

## 要求

- [Alfred](https://www.alfredapp.com/) + **Powerpack**（Script Filter 需要）
- [Obsidian](https://obsidian.md/) for macOS
- macOS 自带 Python 3

## 安装

1. 克隆或下载本仓库
2. 打包工作流：

```bash
./pack.sh
```

3. 双击生成的 `Open Obsidian.alfredworkflow`，导入 Alfred
4. 在 Alfred → Workflows → **Open Obsidian** → 左上角 **Configure Workflow**（齿轮）
5. 填写 **Obsidian 库路径**（文档库根目录的绝对路径），例如：

```
/Users/you/Documents/MyVault
```

可在 Obsidian 中右键库名 → **在 Finder 中显示** 获取路径。

## 使用

1. 唤起 Alfred
2. 输入 `obs` 查看最近笔记；**继续输入关键词**即可搜索（空格可选）
3. 用方向键选择结果，按 **Enter** 在 Obsidian 中打开

示例：

```
obs              → 最近 15 篇笔记
obs wechat       → 搜索 wechat
obswechat        → 同上（无空格也行）
obs 会议纪要      → 搜索含「会议纪要」的笔记
```

仅输入 `obs` 时，会显示最近修改的 15 篇笔记。

## 搜索说明

- 主标题为文件名（去掉 `.md`）
- 同时匹配 front matter 中的 `title:` 与正文首个 `# 标题`
- 副标题为库内相对路径
- 索引会缓存；文档库有文件变动时会自动重建

## 搜不到结果？

1. **重新导入**最新的 `Open Obsidian.alfredworkflow`（右键旧工作流 → Delete，再双击新包导入）
2. 确认 **Configure Workflow** 里 `Obsidian 库路径` 为：

   ```
   /Users/xiushanfan/Documents/obsidian
   ```

   必须是文档库**根目录**（包含 `.obsidian` 文件夹的那一层）。若留空，会自动使用 Obsidian 当前打开的库。
3. 先只输入 `obs`（加空格），应出现最近 15 篇笔记；若仍为空，在 Alfred 工作流窗口右上角点 **Debug** 查看脚本是否报错
4. 搜索时用**文件名**或 front matter / 标题里的文字，支持多个词，例如：`obs 会议 纪要`

## 开发 / 本地测试

```bash
export vault_path="/path/to/your/vault"
python3 workflow/search.py "关键词" | python3 -m json.tool
```

## 文件结构

```
workflow/
  info.plist   # Alfred 工作流定义
  search.py    # Script Filter 搜索脚本
  icon.png     # 工作流图标
pack.sh        # 打包为 .alfredworkflow
```

## 许可证

MIT
