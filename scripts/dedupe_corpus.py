#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dedupe_corpus.py —— 按「引用单元主键」去重，建**全集**（可再分卷）
================================================================
用途：当某库的资料是"一次检索/一次导出 = 一份文件"（引用单元 < 文件单元）时，
      必须先把**多轮产物合并去重**，建成"全集"，作为**唯一引用对象**。
      —— 否则同一条会出现多个归属（本技能诞生的事故即由此而来）。

纯标准库。用法：
    python dedupe_corpus.py --config config.json --library B
    python dedupe_corpus.py --config config.json --library B --verify   # 只出报告，不写文件

输出：<corpus_dir>/<库名>_全集/…（按 partition_by 分卷）；同目录 _去重报告.json
"""
import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from registry import load_cfg, iter_files   # noqa: E402


def read_rows(p: Path, enc: str, delim=None):
    raw = p.read_bytes()
    for e in (enc, "utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            txt = raw.decode(e)
            break
        except Exception:
            continue
    else:
        return [], []
    sniffer = csv.Sniffer()
    try:
        d = delim or sniffer.sniff(txt[:4096], delimiters=",\t;|").delimiter
    except Exception:
        d = ","
    rows = [r for r in csv.reader(io.StringIO(txt), delimiter=d) if any(x.strip() for x in r)]
    return rows[:1], rows[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--library", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    root: Path = cfg["_root"]
    lib = next((x for x in cfg["libraries"] if x["code"] == a.library), None)
    if not lib:
        sys.exit(f"配置里没有库 {a.library}")
    key = lib.get("dedupe_key")
    if not key:
        sys.exit("该库未声明 dedupe_key（引用单元＝文件单元时不需要去重）")

    files = iter_files(root, lib["glob"])
    print(f"库 {a.library}（{lib['name']}）｜输入 {len(files)} 份")
    print(f"去重键：{key}")

    agg, total = {}, 0
    header = None
    for p in files:
        h, rows = read_rows(p, lib.get("encoding", "utf-8"))
        if h and not header:
            header = h
        for r in rows:
            total += 1
            r = (r + [""] * len(key))[:max(len(key), len(r))]
            k = tuple((r[i] if i < len(r) else "").strip() for i in key_idx(header, key, r))
            agg.setdefault(k, {"row": r, "srcs": set()})["srcs"].add(p.name)
    uniq = len(agg)
    print(f"输入行 {total:,}｜去重后 {uniq:,}｜重复率 {1 - uniq/max(total,1):.1%}")

    part = lib.get("partition_by", "")
    bypart = defaultdict(list)
    for k, v in agg.items():
        r = v["row"]
        val = "ALL"
        # 支持 `日付[:4]`（省略起始）与 `日付[0:4]` 两种写法
        m = re.match(r"^(\w+)\[(\d*):(\d*)\]$", part)
        if m:
            idx = header.index(m.group(1)) if header and m.group(1) in header else 2
            s = r[idx] if idx < len(r) else ""
            lo = int(m.group(2)) if m.group(2) else 0          # ⚠️ 勿用 a/b：会遮蔽 argparse 的 args
            hi = int(m.group(3)) if m.group(3) else len(s)
            val = s[lo:hi] or "未分区"
        bypart[val].append((list(k), r, sorted(v["srcs"])))

    report = {"库": a.library, "输入文件数": len(files), "输入行数": total,
              "去重后": uniq, "去重键": key,
              "分卷": {k: len(v) for k, v in sorted(bypart.items())}}
    # 抽样 20 条供人工核对
    sample = []
    for k in sorted(bypart):
        for kk, r, srcs in bypart[k][:2]:
            sample.append({"分区": k, "键": kk, "行": r[:8], "来源文件数": len(srcs),
                           "来源示例": srcs[:3]})
    report["抽样20"] = sample[:20]
    print(json.dumps(report["分卷"], ensure_ascii=False))
    if a.verify:
        print("（--verify：只出报告，未写文件）")
        print(json.dumps(report, ensure_ascii=False, indent=1)[:1500])
        return

    outdir = Path(a.out) if a.out else (root / cfg["corpus_dir"] / f"{lib['name']}_全集")
    outdir.mkdir(parents=True, exist_ok=True)
    # ★ 陈旧文件告警：上一轮的分卷若已不在本轮清单里，会让人误以为"数据还在"
    fresh = {f"全集_{k}.csv" for k in bypart}
    stale = [p.name for p in outdir.glob("全集_*.csv") if p.name not in fresh]
    if stale:
        print(f"⚠ 目录里存在 {len(stale)} 个上一轮的分卷（本轮不需要）：{stale[:6]}")
        print(f"  请自行确认后清理——**不要静默留着**，否则下游会把陈旧分卷也当引用对象。")
    for k, items in sorted(bypart.items()):
        items.sort(key=lambda x: str(x[1]))
        with (outdir / f"全集_{k}.csv").open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow((header or []) + ["命中来源数", "命中来源文件"])
            for _kk, r, srcs in items:
                w.writerow(list(r) + [len(srcs), "；".join(srcs)])
    (outdir / "_去重报告.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {outdir}（{len(bypart)} 卷）｜ 报告：_去重报告.json")


def key_idx(header, key, row):
    """把键名映射到列号；没有表头时按顺序取前 N 列。"""
    if header:
        try:
            return [header.index(k) for k in key]
        except ValueError:
            pass
    return list(range(len(key)))


if __name__ == "__main__":
    main()
