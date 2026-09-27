#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
registry.py —— 编号注册表（**冻结语义**：跑两次，已有编号变动必须为 0）
================================================================
纯标准库（Python 3.8+）。路径全部来自 config.json，脚本内不硬编码。

用法：
    python registry.py --config config.json
    python registry.py --config config.json --check   # 只校验冻结稳定性，不写盘

输出：<registry_file> = { 相对路径: {编号, 名称, 库, 库名, 引用单元, 层级, strategy} }
"""
import argparse
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^([A-Z]+)-(\d+)$")


def load_cfg(p):
    cfg = json.loads(Path(p).read_text(encoding="utf-8"))
    cfg["_root"] = Path(cfg["project_root"])
    return cfg


def iter_files(root: Path, pattern: str):
    """支持 `<dir>/*.ext` 与 `<dir>/**/*.ext`；相对 project_root 解析。"""
    pattern = pattern.replace("\\", "/")
    base = root
    parts = pattern.split("/")
    # 取最长的非通配前缀作为搜索起点
    while parts and not any(ch in parts[0] for ch in "*?["):
        base = base / parts.pop(0)
    rest = "/".join(parts)
    if not rest:
        return []
    out = []
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(base)).replace("\\", "/")
        if fnmatch.fnmatch(rel, rest) or fnmatch.fnmatch(p.name, rest):
            out.append(p)
    return out


def next_free(used: set, prefix: str, width: int):
    i = 1
    while f"{prefix}-{i:0{width}d}" in used:
        i += 1
    return f"{prefix}-{i:0{width}d}", i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    root: Path = cfg["_root"]
    regp = root / cfg["registry_file"]

    old = {}
    if regp.exists():
        old = json.loads(regp.read_text(encoding="utf-8"))
    reg, changed = {}, 0
    used = set()

    for lib in cfg["libraries"]:
        code = lib["code"]
        pref = cfg["prefixes"].get(code, {})
        width = int(pref.get("num_width", 3))
        files = iter_files(root, lib["glob"])
        # 先认领旧编号（冻结：沿用不移位）
        claimed = {}
        for f in files:
            rel = str(f.relative_to(root)).replace("\\", "/")
            if rel in old and str(old[rel].get("编号", "")).startswith(code + "-"):
                claimed[rel] = old[rel]["编号"]
                used.add(old[rel]["编号"])
        # 再给新文件发号
        for f in files:
            rel = str(f.relative_to(root)).replace("\\", "/")
            if rel in claimed:
                rid = claimed[rel]
            else:
                rid, _ = next_free(used, code, width)
                used.add(rid)
                if rel in old:
                    changed += 1
            reg[rel] = {
                "编号": rid, "名称": f.name, "库": code, "库名": lib["name"],
                "引用单元": lib.get("citation_unit", ""),
                "策略": lib.get("strategy", ""), "层级": lib.get("level", ""),
            }

    # 冻结校验：旧注册表里的编号是否被改动
    moved = 0
    for rel, v in old.items():
        if rel in reg and v.get("编号") != reg[rel]["编号"]:
            moved += 1
            print(f"!! 编号变动：{rel}  {v.get('编号')} -> {reg[rel]['编号']}")

    n_by_lib = {}
    for v in reg.values():
        n_by_lib[v["库"]] = n_by_lib.get(v["库"], 0) + 1
    ids = [v["编号"] for v in reg.values()]
    print(f"注册表：{len(reg)} 个文件｜唯一编号 {len(set(ids))}｜重复 {len(ids)-len(set(ids))}")
    for k in sorted(n_by_lib):
        lib = next((x for x in cfg["libraries"] if x["code"] == k), {})
        exp = lib.get("unit_count_expected")
        flag = ""
        if exp:
            flag = "  ✅ 与预期一致" if exp == n_by_lib[k] else f"  ⚠ 预期 {exp}"
        print(f"   {k}: {n_by_lib[k]:>6}{flag}   {lib.get('name','')}")
    print(f"新旧编号变动 {moved}（必须为 0）｜本次新发号 {changed}")

    if not a.check:
        regp.parent.mkdir(parents=True, exist_ok=True)
        regp.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {regp}")
    sys.exit(1 if moved else 0)


if __name__ == "__main__":
    main()
