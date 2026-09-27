# research-writing-pipeline

> **人文学科与社会科学研究的全流程工程化方法** —— 适用于**任何题目、任何体裁**
> （学位论文／期刊论文／专著／研究报告）。
> Pure-stdlib, cross-device & cross-model. No third-party dependencies.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

---

## 这是什么

把一次**持续数周到数年的研究写作**，做成**可控、可核验、可交接、可复用**的工程。
它不是"写作技巧合集"，而是一套**带出口自检的流程**：每一步做完先验证，再进下一步。

**核心一句话**：

> **先问「以后怎么用」，再决定「现在怎么做」。**
> 选题先问"要证明什么"；收料先问"对应哪一节"；落盘先问"将来怎么引"；
> 写作先问"这条材料证明什么、不证明什么"；交付先问"别人能不能自己核验"。
>
> **「方便现在」永远不能优先于「将来可用」。**

---

## 七阶段流程

```
       ┌──────── 贯穿全场：项目记忆 · 版本管理 · 事实冻结 · 诚实标注 ────────┐
       │                                                                   │
   阶段0        阶段1        阶段2        阶段3        阶段4        阶段5        阶段6
  选题框架  →  目标界定  →  检索获取  →  语料库工程 →  分析対位  →  写作引注  →  审校提交
  与论证框架   收什么       下载入库     编号台账交付   按结构对位    逐节落地     查重投稿
              不收什么
       │                                                                   │
       └── 每个阶段都有【出口自检】；不通过，不得进入下一阶段 ────────────────┘
```

**两个正交的适配轴**（先定这两件事，再套流程）：

| 轴 | 取值 | 影响什么 | 详见 |
|---|---|---|---|
| **体裁** | 学位论文／期刊论文／专著／研究报告 | 结构、篇幅、引注位置、审校重点、交付形态 | [`references/05_体裁适配.md`](references/05_体裁适配.md) |
| **学科** | 历史・文学・语言・哲学・法学・社会・人类・教育・政治・经济・传播・艺术・考古… | 什么算一手材料、常用方法、该学科特有的雷区 | [`references/06_学科适配.md`](references/06_学科适配.md) |

---

## 四条贯穿纪律

1. **先定「引用单元」，再决定「怎么落盘」** —— 引用单元是设计输入，不是事后补救；
2. **事实冻结与版本管理** —— 确认过的判断只写一版；结构性变更先版本化；
3. **诚实标注优先于表面完整** —— 宁可标「待核」，不可写错信息；
4. **一切引用必须可核验** —— 编号能一键跳原件；目录级／标题级材料**不得据题名陈述内容**。

---

## 快速开始

```bash
cp config.example.json config.json      # 改：project_root / libraries / conventions

python scripts/outline_tree.py               --outline 框架.md --out result.json   # 阶段0
python scripts/registry.py                   --config config.json                   # 阶段3
python scripts/dedupe_corpus.py              --config config.json --library B       # 阶段3
python scripts/check_contract.py             --config config.json --md-dir .        # 阶段3 自检
python scripts/check_links.py                --docx-dir ./Word版                    # 阶段3 自检
python scripts/check_writing_conventions.py  --config config.json --md-dir ./正文  # 阶段5-6
```

**环境要求**：Python **3.8+**，**无需 pip install 任何包**。
可选：`pandoc`（md→docx 并保留编号超链接）、`7z`（打包）。

---

## 目录结构

```
.
├── SKILL.md                  ← 主文件（触发词、七阶段、铁律、自检）
├── INSTALL.md                ← 安装到 WorkBuddy/Claude Code/Cursor/纯对话 AI/人工协作
├── SELFTEST.md               ← 端到端实测记录（证明可运行）
├── config.example.json       ← 配置模板（路径、库表、体例、自检阈值全部外置）
├── references/               ← 17 篇分阶段详细做法
│   ├── 00_阶段总览与自检.md
│   ├── 05_体裁适配.md               ★ 学位论文/期刊论文/专著/研究报告
│   ├── 06_学科适配.md               ★ 16 个学科的材料/方法/雷区
│   ├── 10_选题框架与论证设计.md
│   ├── 11_目标界定.md
│   ├── 12_检索与获取.md
│   ├── 13_多语言与译本文献.md
│   ├── 20_引用单元与编号契约.md       ← 五条铁律
│   ├── 21_采集与去重.md
│   ├── 22_聚合文件与引用层级.md
│   ├── 23_台账与交付包.md
│   ├── 24_按论证结构生成分析.md
│   ├── 25_复盘案例_引用单元事故.md    ← 真实事故复盘＋跨学科通用化（建议先读）
│   ├── 26_工具脚本说明.md
│   ├── 30_写作与引注落地.md
│   ├── 31_审校查重与提交.md
│   ├── 32_协作与迭代.md
│   └── 90_原则纪律与常见坑.md
└── scripts/                  ← 6 个纯标准库 Python 脚本
    ├── outline_tree.py               大纲→结构化配置＋结构自检
    ├── registry.py                   编号注册表（含冻结）
    ├── dedupe_corpus.py              按主键去重建「全集」
    ├── check_contract.py             契约自检（编号冻结/台账/裸编号）
    ├── check_links.py                链接自检（断链=0）
    └── check_writing_conventions.py   体例自检（篇幅/摘要/关键词/引注/参考文献/标题层级）
```

---

## 安装

| 载体 | 做法 |
|---|---|
| **WorkBuddy / CodeBuddy** | 把本目录放进 `~/.workbuddy/skills/`（用户级）或 `<项目>/.workbuddy/skills/`（项目级）。⚠️ 技能发现**只扫一层**，目录名保持 `research-writing-pipeline`。 |
| **Claude Code** | `~/.claude/skills/research-writing-pipeline/SKILL.md` |
| **Cursor** | 把 `SKILL.md` 并入 `<项目>/.cursor/rules/` |
| **纯对话型 AI** | 把 `SKILL.md` 全文放进系统提示/项目知识；需要细节时附对应 `references/*.md`。脚本不能跑时，按 references 手工执行（每步都有可人工完成的口径）。 |
| **人工/多人协作** | `SKILL.md` 本身即工作规程。⚠️ 阶段 3（编号）**不可并发**，注册表是唯一写入点。 |

详见 [`INSTALL.md`](INSTALL.md)。

---

## 三条强制自检（任一不过，不得进入下一阶段）

```
编号冻结：连跑两次，编号变动 = 0
台账：内容提要为空的条目 = 0；文字粒度全部已标
编号完整性：库级锚点 = 0；未知编号 = 0；断链 = 0
```

---

## 它从哪来

取自一个真实的历史学硕士学位论文项目的完整实践（2025-11 — 2026-09）：
从选题规划、资料收集与整理，到按论证结构生成材料分析、体例与引注自检。

其中**阶段 3（语料库工程）**诞生于一次真实事故——把"一次检索产出一份文件"当成了组织单位，
于是同一条材料有多个"家"、引用无法核验。完整因果链与**跨学科通用化对照**见
[`references/25_复盘案例_引用单元事故.md`](references/25_复盘案例_引用单元事故.md)。
**读那个案例，比读十条规则更有效。**

---

## License

MIT —— 自由复制、修改、转授，保留版权声明即可。
