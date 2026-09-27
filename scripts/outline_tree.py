#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
outline_tree.py —— 把「论文大纲」文本变成**结构化配置**，并做结构自检
================================================================
用途（对应流程阶段 0 与阶段 4）：
  1. 解析 markdown 风格大纲 → 结构化 JSON（code / chap / title / point / kw），
     这份 JSON 就是阶段 4「按大纲匹配分析」的输入；
  2. 结构自检：编号是否连续、是否有"只有标题没有下位节"的空节、
     是否有"下有节却自己无标题"的畸形层级；
  3. 为每个节点生成待填的 `point`（要证明什么）与 `kw`（检索词）模板。

纯标准库。用法：
    python outline_tree.py --outline 大纲.md --out outline.json [--check]
"""
import argparse
import json
import re
import sys
from pathlib import Path

CN = "一二三四五六七八九十"
ROMAN = "IVXLCivxlc"
# ① 「第X章 / 第X部分 / 一、」中文体
#    ⚠️ 「部分」必须排在「部」之前，否则「第二部分」会被切成「第二部」+「分 …」
RE_CN_CHAP = re.compile(r"^#{1,3}\s*(第[%s]+(?:部分|章|部|篇|节)|[%s]、)\s*(.+)$" % (CN, CN))
# ② 「Chapter 1 / Part II / Section 3」
#    ⚠️ 必须加 (?!\d)：否则 `1.1 Background` 会被当成 `1.` + 标题「1 Background」
RE_EN_CHAP = re.compile(r"^#{1,3}\s*((?:chapter|part|section|ch|pt)\.?\s*[0-9%s]+|[0-9%s]+\.(?!\d))\s*[:.．、]?\s*(.+)$"
                        % (ROMAN, ROMAN), re.I)
# ③ 多级编号 1.1 / 1.1.1
RE_NUM = re.compile(r"^#{1,3}\s*(\d+(?:\.\d+){1,3})\s*[　 ]*[:.．]?\s*(.+)$")
# ④ 单级编号 1 / 1. / 1、
RE_NUM1 = re.compile(r"^#{1,3}\s*(\d+)\s*[、.．]\s*(.+)$")
# ⑤ 通用结构名（绪论/结论/参考文献…与英文对应）
RE_GENERIC = re.compile(
    r"^#{1,3}\s*(绪\s*论|绪\s*言|导\s*论|引\s*言|前\s*言|结\s*论|結\s*论|结\s*语|余\s*论|"
    r"参考文献|引用文献|致\s*谢|附\s*录|摘\s*要|关键词|"
    r"introduction|conclusion|concluding\s+remarks|discussion|"
    r"references|bibliography|works\s+cited|appendix|acknowledg\w*|abstract|keywords|"
    r"einleitung|schluss|fazit|literaturverzeichnis|anhang)\s*[:：]?\s*(.*)$", re.I)


def parse(md: str):
    nodes, chap, chapcode = [], "", ""
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.startswith("#"):
            continue
        lv = line.count("#")
        m = RE_CN_CHAP.match(line)
        if m:
            title, chap, chapcode = m.group(2).strip(), m.group(1), m.group(1)
            nodes.append(dict(code=chapcode, chap=title, title=title, level=lv,
                              parent="", point="", kw=[]))
            continue
        m = RE_EN_CHAP.match(line)
        if m:
            code, title = m.group(1).strip().rstrip("."), m.group(2).strip()
            chap, chapcode = title, code
            nodes.append(dict(code=code, chap=title, title=title, level=lv,
                              parent="", point="", kw=[]))
            continue
        m = RE_NUM.match(line)
        if m:
            code, title = m.group(1), m.group(2).strip()
            depth = code.count(".")
            nodes.append(dict(code=code, chap=chap, title=title, level=lv, parent=chapcode,
                              kind=("节" if depth == 1 else "三级"), point="", kw=[]))
            continue
        m = RE_NUM1.match(line)
        if m:                                  # 单级编号：有章则视为节，无章则视为章
            code, title = m.group(1), m.group(2).strip()
            if chapcode:
                nodes.append(dict(code=code, chap=chap, title=title, level=lv,
                                  parent=chapcode, kind="节", point="", kw=[]))
            else:
                chap, chapcode = title, code
                nodes.append(dict(code=code, chap=title, title=title, level=lv,
                                  parent="", point="", kw=[]))
            continue
        m = RE_GENERIC.match(line)
        if m:
            name = re.sub(r"\s+", "", m.group(1))
            tail = (m.group(2) or "").strip()
            label = (name + (("　" + tail) if tail else "")).strip()
            chapcode = ""
            nodes.append(dict(code=name, chap=name, title=label, level=lv,
                              parent="", point="", kw=[]))
            continue
    # ★ 唯一标识：各章下小节编号常各自从 1 开始 → 用「章-节」拼出 uid，
    #    避免 English 式大纲出现重复 code（否则下游按 code 索引会串号）
    seen = {}
    for n in nodes:
        base = f"{n['parent']}-{n['code']}" if n.get("parent") else n["code"]
        k = seen.get(base, 0) + 1
        seen[base] = k
        n["uid"] = base if k == 1 else f"{base}#{k}"
    return nodes


def check(nodes):
    bad = []
    # ① 编号连续性：**在该节点的父章范围内**校验（English 式大纲各章小节从 1 重起，不能全局比）
    seen = {}
    for n in nodes:
        c = n["code"]
        if not re.match(r"^\d+(\.\d+)*$", c):
            continue
        up = c.rsplit(".", 1)[0] if "." in c else ""
        seq = int(c.rsplit(".", 1)[-1])
        key = (n.get("parent", ""), up, c.count("."))
        exp = seen.get(key, 0) + 1
        if seq != exp:
            bad.append(f"编号不连续：{n.get('parent','') + '.' if n.get('parent') else ''}{c}"
                       f"（该位置应为 …{exp}）")
        seen[key] = seq

    # ② 层级畸形：**仅在"父节点应当是数字编号"时才校验**
    all_codes = {n["code"] for n in nodes}
    numeric_chap = any(re.fullmatch(r"\d+", n["code"]) for n in nodes)
    for n in nodes:
        c = n["code"]
        if "." not in c:
            continue
        parent = c.rsplit(".", 1)[0]
        if parent in all_codes:
            continue
        if numeric_chap or "." in parent:
            bad.append(f"层级畸形：{c} 的上级 {parent} 没有对应节点")

    # ③ 空标题 / uid 重复（uid 重复 = 同一位置出现两次，下游会串号）
    for n in nodes:
        if not n["title"].strip():
            bad.append(f"节点 {n['code']} 无标题")
    uids = [n["uid"] for n in nodes]
    dup = {u for u in uids if uids.count(u) > 1}
    for u in sorted(dup):
        bad.append(f"uid 重复：{u}（同一位置出现多次，建议给标题加区分词）")

    has_child = {n["code"].rsplit(".", 1)[0] for n in nodes if "." in n["code"]}
    leaves = [n for n in nodes if n["code"] not in has_child]
    return bad, leaves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outline", required=True)
    ap.add_argument("--out", default="outline.json")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    md = Path(a.outline).read_text(encoding="utf-8")
    nodes = parse(md)
    if not nodes:
        sys.exit("未解析到任何章节行（支持 `# 第一章 …` / `## 1.1 …` / `### 1.1.1 …`）")
    bad, leaves = check(nodes)
    print(f"解析到 {len(nodes)} 个节点｜其中叶子（需填论证要点）{len(leaves)} 个")
    for n in nodes:
        print(f"  {'  ' * (n.get('kind') == '三级')}{n['code']}  {n['title'][:52]}")
    if bad:
        print("\n⚠ 结构问题：")
        for b in bad:
            print("   " + b)
    else:
        print("\n✅ 结构自检通过（编号连续、无畸形层级）")
    print("\n⚠ 还需人工补齐：每个叶子的 `point`（这节要证明什么）与 `kw`（检索词）"
          "——**答不出 point 的节，就是多余的节**。")
    Path(a.out).write_text(json.dumps(nodes, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {a.out}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
