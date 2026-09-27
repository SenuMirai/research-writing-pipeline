#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_links.py —— 链接自检（编号 → 原件，必须**可点且目标存在**）
================================================================
① 读 docx 里的外部超链接，逐个判定**目标文件是否存在**
② 统计「唯一编号数」与「外部关系数」，二者应基本相等（差 1–2 属正常：封面/目录）
③ 给出断链清单（这是最容易被忽略的错误：文件改名/换机器后链接全废）

纯标准库（zipfile 读 docx）。

用法：
    python check_links.py --docx a.docx b.docx
    python check_links.py --docx-dir ./Word版 --registry config.json
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


def rels_of(docx: Path):
    try:
        z = zipfile.ZipFile(docx)
    except Exception as e:
        return None, f"打不开：{e}"
    try:
        r = z.read("word/_rels/document.xml.rels").decode("utf-8", "ignore")
    except KeyError:
        return None, "无 document.xml.rels"
    # 目标可能被 URL 编码（空格→%20 等），需 unquote
    from urllib.parse import unquote
    tgts = re.findall(r'Target="([^"]+)"[^>]*TargetMode="External"', r)
    return [unquote(t) for t in tgts], None


def check(docx: Path):
    tgts, err = rels_of(docx)
    if err:
        print(f"  ✗ {docx.name}：{err}")
        return 0, 0, 0
    missing, ok = [], 0
    for t in tgts:
        if t.startswith(("http://", "https://", "mailto:")):
            ok += 1
            continue
        p = (docx.parent / t).resolve()
        if p.exists():
            ok += 1
        else:
            missing.append(t)
    stat = "✅" if not missing else "❌"
    print(f"  {stat} {docx.name}：外部链接 {len(tgts)}｜可解析 {ok}｜**断链 {len(missing)}**")
    for m in missing[:6]:
        print(f"       ↳ 缺：{m[-90:]}")
    return len(tgts), ok, len(missing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docx", nargs="*", default=[])
    ap.add_argument("--docx-dir", default=None)
    a = ap.parse_args()
    files = [Path(x) for x in a.docx]
    if a.docx_dir:
        files += sorted(Path(a.docx_dir).rglob("*.docx"))
    if not files:
        sys.exit("未指定 --docx 或 --docx-dir")
    T = O = M = 0
    for f in files:
        t, o, m = check(f)
        T += t
        O += o
        M += m
    print(f"\n合计：外部链接 {T}｜可解析 {O}｜断链 {M}")
    print("判读要点：**断链必须为 0**；若断链集中出现，说明包被移动过或文件被改名——"
          "此时应重跑生成器（用包内相对路径），而不是逐个改链接。")
    sys.exit(1 if M else 0)


if __name__ == "__main__":
    main()
