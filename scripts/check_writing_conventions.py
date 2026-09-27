#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_writing_conventions.py —— 论文体例与引注的**机械自检**
================================================================
对应流程阶段 5–6。检查能机械判定的部分，把人工判断留给作者。

检查项：
  ① 正文字数（可指定只统计正文范围；默认统计全部 md 的中日文字符数）
  ② 摘要字数（自动找含"摘要/Abstract"的块）
  ③ 关键词个数（找"关键词/キーワード/Keywords"行）
  ④ 引注编号连续性（按出现顺序抽 `[n]`，报跳号/重复/起点非 1）
  ⑤ 参考文献条目数 + 外文条目占比（按是否含拉丁字母/西里尔/假名粗判）
  ⑥ 标题层级完整性（不跳级，如 # → ###）
  ⑦ 残留占位符（"待核/TODO/待补/XXX"计数，供人工确认）

纯标准库。用法：
    python check_writing_conventions.py --config config.json --md-dir ./正文
    python check_writing_conventions.py --md-dir ./正文 --body-only 第一章 第三章
"""
import argparse
import json
import re
import sys
from pathlib import Path

CJK = re.compile(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]")
LATIN = re.compile(r"[A-Za-z\u0400-\u04ff]")
CITE = re.compile(r"\[(\d{1,4})\]")
PLACEHOLDER = re.compile(r"(待核|待补|TODO|XXX|xx待|占位)")
HEAD = re.compile(r"^(#{1,6})\s", re.M)


def load_cfg(p):
    if not p:
        return {}
    return json.loads(Path(p).read_text(encoding="utf-8"))


def collect(md_dir: Path, body_only=None):
    files = []
    for f in sorted(md_dir.rglob("*.md")):
        parts = f.relative_to(md_dir).parts
        if any(s.startswith("_") for s in parts):
            continue
        if body_only and not any(b in str(f) for b in body_only):
            continue
        files.append(f)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--md-dir", required=True)
    ap.add_argument("--body-only", nargs="*", default=None)
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    conv = cfg.get("conventions", {}) or {}
    md_dir = Path(a.md_dir)
    files = collect(md_dir, a.body_only)
    if not files:
        sys.exit("未找到 md 文件")
    text = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in files)

    fails = []
    # ① 篇幅（中日韩按字符计，其余语言按词计；两种都报）
    n_cjk = len(CJK.findall(text))
    latin_words = len(re.findall(r"[A-Za-z\u0400-\u04ff]{1,}", text))
    words_total = n_cjk + latin_words          # 混排时的粗略总词量
    lo, hi = conv.get("body_words_min"), conv.get("body_words_max")
    s = f"中日韩字符 {n_cjk:,}｜拉丁/西里尔词 {latin_words:,}｜合计约 {words_total:,}"
    if lo and hi:
        ok = lo <= words_total <= hi
        s += f"（目标 {lo:,}–{hi:,}）" + ("✅" if ok else "⚠ 超出区间")
        if not ok:
            fails.append("篇幅超出区间")
    print(f"① 篇幅：{s}｜扫描 {len(files)} 个文件")

    # ② 摘要（中日韩按字符、其余按词；两种语言混排时取合计）
    for m in re.finditer(r"(摘要|要旨|ABSTRACT|Abstract)\s*[:：]?\s*(.{0,3000}?)(?=\n#{1,3}\s|关键词|キーワード|Keywords|\Z)",
                         text, re.S):
        body = m.group(2)
        n = len(CJK.findall(body)) + len(re.findall(r"[A-Za-z\u0400-\u04ff]{1,}", body))
        lab = m.group(1)
        lim = conv.get("abstract_words_min"), conv.get("abstract_words_max")
        st = ""
        if lim[0]:
            st = ("✅" if lim[0] <= n <= lim[1] else f"⚠ 目标 {lim[0]}–{lim[1]}")
        print(f"② 摘要（{lab}）长度：{n:,}（中日韩字符＋西文词） {st}")

    # ③ 关键词（兼容两种写法：`关键词：a；b` 与 `# 关键词` 换行后跟列表）
    for m in re.finditer(r"(?:^|\n)#{0,3}\s*(关键词|キーワード|Keywords)\s*[:：]?\s*\n?\s*(.{0,300})",
                         text):
        seg = m.group(2).split("\n")[0]
        items = [x for x in re.split(r"[;；,，、\s]+", seg.strip()) if x and len(x) < 40]
        if not items:
            continue
        k = len(items)
        lo2, hi2 = conv.get("keywords_min"), conv.get("keywords_max")
        st = ""
        if lo2:
            st = ("✅" if lo2 <= k <= hi2 else f"⚠ 目标 {lo2}–{hi2}")
        print(f"③ 关键词（{m.group(1)}）个数：{k} {st}｜{items[:8]}")

    # ④ 引注编号连续性（仅顺序编码制；作者—年份制改查文内引文与文后条目的呼应）
    style = (conv.get("citation_style") or "").lower()
    nums = [int(x) for x in CITE.findall(text)]
    if nums:
        seq = list(dict.fromkeys(nums))          # 按首次出现顺序
        gaps = [i for i in range(1, max(seq) + 1) if i not in set(seq)]
        st = "✅" if (not gaps and seq[0] == 1) else "❌"
        print(f"④ 引注编号（顺序编码制）：出现 {len(nums)} 次｜唯一 {len(seq)} 个｜"
              f"最大 [{max(seq)}]｜**跳号 {len(gaps)}**｜起点 {seq[0]} {st}")
        if gaps:
            print(f"      ↳ 缺：{gaps[:12]}{' …' if len(gaps) > 12 else ''}")
            fails.append(f"引注跳号 {len(gaps)} 处")
        if seq[0] != 1:
            fails.append("引注起点不是 [1]")
    else:
        # 作者—年份制（或脚注制）：改为检查「文内引文」与「参考文献」的呼应
        intext = re.findall(r"[（(]([A-Z][A-Za-z\-']+)[^)）]{0,30}?(\d{4})[a-z]?[)）]", text)
        if intext:
            keys = {f"{a} {y}" for a, y in intext}
            print(f"④ 引注（作者—年份制）：文内引文 {len(intext)} 处｜唯一 {len(keys)} 个")
            refs_block = re.search(r"(#{1,3}\s*(参考文献|引用文献|References|Bibliography|"
                                   r"Works\s+cited)\b.*)", text, re.S | re.I)
            if refs_block:
                miss = [k for k in sorted(keys)
                        if not re.search(re.escape(k.split()[0]) + r".{0,80}?"
                                         + re.escape(k.split()[1]), refs_block.group(1))]
                st = "✅" if not miss else "❌"
                print(f"      → 文后条目中未匹配到的引文：{len(miss)} {st}")
                if miss:
                    print(f"        ↳ 例：{miss[:6]}")
                    fails.append(f"文内引文在文后条目中缺失 {len(miss)} 处")
            else:
                print("      · 未找到参考文献章节（若在单独文件，请用 --body-only 指定）")
        else:
            print(f"④ 引注：未检出编号或作者—年份引文"
                  f"（citation_style={conv.get('citation_style') or '未配置'}；"
                  f"若为脚注制请人工核对）")

    # ⑤ 参考文献
    refs = []
    m = re.search(r"(#{1,3}\s*(参考文献|引用文献|References)\b.*)", text, re.S)
    if m:
        for line in m.group(1).splitlines()[1:]:
            t = line.strip()
            if not t or re.match(r"^(#{1,6}\s|<|>)", t):
                continue
            if len(CJK.findall(t)) + len(t) > 12:
                refs.append(t)
        foreign = sum(1 for r in refs if LATIN.search(r))
        ratio = (foreign / len(refs) * 100) if refs else 0
        lo3 = conv.get("foreign_ref_ratio_min")
        st = ""
        if lo3:
            st = "✅" if ratio >= lo3 else f"⚠ 目标 ≥{lo3}%"
        print(f"⑤ 参考文献：{len(refs)} 条｜外文 {foreign} 条（{ratio:.0f}%）{st}")
        lo4 = conv.get("refs_min")
        if lo4 and len(refs) < lo4:
            fails.append(f"参考文献不足（{len(refs)} < {lo4}）")
    else:
        print("⑤ 参考文献：未找到章节（若在单独文件里，请以 --body-only 指定）")

    # ⑥ 标题层级
    levels = [len(x) for x in HEAD.findall(text)]
    jumps = [(levels[i - 1], levels[i]) for i in range(1, len(levels)) if levels[i] - levels[i - 1] > 1]
    st = "✅" if not jumps else "❌"
    print(f"⑥ 标题层级：{len(levels)} 个标题｜**跳级 {len(jumps)}** {st}")
    if jumps:
        print(f"      ↳ 例：{jumps[:6]}")
        fails.append(f"标题跳级 {len(jumps)} 处")

    # ⑦ 占位符
    ph = len(PLACEHOLDER.findall(text))
    st = "✅" if ph == 0 else "⚠ 需人工确认（可接受：显式标注的待核项）"
    print(f"⑦ 残留占位符（待核/待补/TODO/XXX）：{ph} 处 {st}")

    print()
    if fails:
        print("体例自检未通过：" + "；".join(fails))
        sys.exit(1)
    print("体例自检通过 ✅")


if __name__ == "__main__":
    main()
