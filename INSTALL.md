# 安装与移植说明（research-writing-pipeline）

本技能包是**纯文本 + 纯 Python 标准库**，无第三方依赖、无网络依赖、无平台绑定。
因此可以**复制到任何设备、喂给任何 AI 模型**使用（见下文四类载体）。

---

## 一、包内结构

```
research-writing-pipeline/
├── SKILL.md                  ← 主文件：七阶段全景、四条纪律、各阶段要点与出口自检
├── INSTALL.md                ← 本文件
├── SELFTEST.md               ← 端到端实测记录（证明可运行）
├── config.example.json       ← 配置模板（阶段0体例/编号前缀/库表/自检阈值 全部外置）
├── references/               ← 分阶段详细做法（15 篇）
│   ├── 00_阶段总览与自检.md
│   ├── 05_体裁适配.md              ← ★学位论文/期刊论文/专著/研究报告 差异
│   ├── 06_学科适配.md              ← ★人文各科/社科各科 材料与方法对照
│   ├── 10_选题框架与开题.md          ← 阶段0
│   ├── 11_目标界定.md                ← 阶段1
│   ├── 12_检索与获取.md              ← 阶段2
│   ├── 20_引用单元与编号契约.md      ← 阶段3
│   ├── 21_采集与去重.md              ← 阶段3
│   ├── 22_聚合文件与引用层级.md      ← 阶段3
│   ├── 23_台账与交付包.md            ← 阶段3
│   ├── 24_按大纲生成分析.md          ← 阶段4
│   ├── 25_复盘案例_报刊标题事件.md       ← 阶段3 的真实事故复盘（**最值得先读**）
│   ├── 26_工具脚本说明.md
│   ├── 30_写作与引注落地.md          ← 阶段5
│   ├── 31_审校查重与提交.md          ← 阶段6
│   ├── 32_导师沟通与迭代.md          ← 贯穿
│   └── 90_原则纪律与常见坑.md        ← 贯穿
└── scripts/                  ← 纯标准库 Python（6 个）
    ├── registry.py                   ← 编号注册表（含冻结）
    ├── dedupe_corpus.py              ← 按主键去重建「全集」
    ├── check_contract.py             ← 契约自检（编号冻结／台账／裸编号）
    ├── check_links.py                ← 链接自检（断链=0）
    ├── outline_tree.py               ← 大纲→结构化配置＋结构自检
    └── check_writing_conventions.py   ← 体例自检（字数/摘要/关键词/引注连续性/参考文献/标题层级）
```

**环境要求**：Python **3.8+**（无需 pip install 任何包）。
可选：`pandoc`（md→docx 且保留编号超链接）、`7z`（打包）。

---

## 二、安装到各载体

### A. WorkBuddy / CodeBuddy（技能目录）
```bash
# ① 用户级（对所有项目生效，推荐）
unzip research-writing-pipeline.zip -d ~/.workbuddy/skills/

# ② 项目级（只对某个项目生效）
unzip research-writing-pipeline.zip -d <项目根>/.workbuddy/skills/
```
**注意**：技能发现**只扫一层目录**——必须是 `<skills>/research-writing-pipeline/SKILL.md`，
不能嵌套（`<skills>/pack/research-writing-pipeline/` 会扫不到）。

### B. Claude Code / Cursor / 其他"技能·规则目录"型工具
同一份 SKILL.md 即可，只是目录名不同：
```
Claude Code :  ~/.claude/skills/research-writing-pipeline/SKILL.md
Cursor      :  <项目>/.cursor/rules/research-writing-pipeline.md   （把 SKILL.md 并入）
通用约定    :  在 <项目>/AGENTS.md 或 CLAUDE.md 里加一行
               「遵循 skills/research-writing-pipeline/SKILL.md」
```
若工具只吃单文件：把 SKILL.md 整段粘进去即可；`references/`、`scripts/` 保持**同目录相对位置**。

### C. 纯对话型 AI（ChatGPT / Claude / Gemini 网页版等）
没有文件系统，用**两段式**：
1. **系统提示／项目知识**里放 `SKILL.md` 全文（它是自足的）；
2. 需要细节时，把对应 `references/0X_*.md` **作为附件或粘贴**给它。
**脚本不能跑时，让模型按 references 里的步骤手工执行**——每一步都有可人工完成的口径
（例如"去重"可手工按主键排序比对；"编号冻结"可人工对照上一版注册表）。

### D. 完全人工／多人协作
`SKILL.md` 本身就是一份**可打印的工作规程**。分工建议：
- 甲：阶段 0–1（选题与大纲、目标界定）
- 乙：阶段 2（检索获取）
- 丙：阶段 3（编号与台账）——**注册表是唯一写入点，必须串行**
- 丁：阶段 4–6（分析、写作、审校）
> ⚠️ **阶段 3 不可多人并发**，否则抢号会破坏冻结语义。

---

## 三、首次使用（四步）

```bash
cd research-writing-pipeline
cp config.example.json config.json        # 改：project_root / libraries / conventions

python scripts/outline_tree.py --outline 大纲.md --out outline.json      # 阶段0
python scripts/registry.py     --config config.json                      # 阶段3
python scripts/check_contract.py --config config.json --md-dir ./分析    # 自检
```

`config.json` 里**必须改**的是 `project_root`、`libraries`、`conventions`；
其余（层级定义、前缀、去重键、自检阈值）都有合理默认值。

---

## 四、移植到别的项目/别的机器时要注意

| 事项 | 说明 |
|---|---|
| **路径** | 全部走 `config.json`，脚本内**不硬编码绝对路径** |
| **编码** | 多语种资料常见 `旧编码 / 旧编码 / UTF-8-BOM`；按 `encoding` 读，**写出一律 UTF-8-BOM**（Excel 不乱码） |
| **分隔符** | Windows 反斜杠与 POSIX 斜杠混用会出 bug；拼接前统一 `.replace("\\","/")` |
| **全角/半角** | 比对前做 **NFKC 归一**，否则 `２０世紀` 与 `20世纪` 配不上 |
| **文件名含空格/全角** | 测试时**至少放一个含空格与全角的样本** |
| **编号连续性** | 换机器后**沿用同一份 `_编号注册表.json`**，否则编号会重排 |
| **删除** | 某些受管控环境里"删除"只进回收站、不释放空间 → 用 `truncate(0)` 再删 |
| **弹窗/原生对话框** | 若某环境不允许弹窗（非交互会话），改用命令行参数而非 GUI 选择器 |

---

## 五、自检回执（建议每次交付前贴给合作者）

```
[阶段0] 每节能答"要证明什么"；体例执行版已成文
[阶段1] 每条料都能指到小节；每节 ≥1 条 A 级
[阶段2] 每条料有 URL；授权与层级已记
[阶段3] 编号冻结（两次变动=0）｜台账提要为空=0｜库级锚点=0｜未知编号=0｜断链=0
[阶段4] 每条含六项字段＋"不得用它证明什么"
[阶段5] 引文可回原件；论断 ≥2 组来源
[阶段6] 引注跳号=0｜标题跳级=0｜版式逐项对照｜查重已出
```

---

## 六、版本与出处

- 来源：一项历史学硕士学位论文项目（2025-11 — 2026-09）的**完整实践**：从选题规划、资料收集、整理分析，
  到按论证结构生成材料分析、体例与引注自检。
- **本技能已通用化**：不绑定任何学科与题目，适用于人文与社科各领域、且覆盖学位论文／期刊论文／专著／研究报告四种体裁。
  （原始案例仅作示例保留在 `references/25`，并附跨学科通用化对照表。）
- 触发本技能**阶段 3** 诞生的一次真实编号事故：见 `references/25_复盘案例_报刊标题事件.md`。
- 许可：随包自由复制、修改、转授；保留本说明即可。
