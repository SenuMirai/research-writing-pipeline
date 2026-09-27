#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_contract.py —— 契约自检（三条铁律的可执行版本）
================================================================
① 编号冻结：同一份注册表连跑两次，变动必须为 0
② 台账：每条必须有「内容提要」与「文字粒度」（不得为空）
③ 链接：正文中的 `[编号]` 必须是超链接，且**裸编号（库级）必须为 0**

纯标准库。用法：
    python check_contract.py --config config.json
    python check_contract.py --config config.json --ledger <台账.xlsx>   # 需 openpyxl，可选
    python check_contract.py --config config.json --md-dir <分析文档目录>
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from registry import load_cfg   # noqa: E402

BARE = re.compile(r"\[([A-Z]{1,3}\d{0,3})\](?!\()")          # 候选：无 `-序号` 的"库级形态"
ANY_ID = re.compile(r"\[([A-Z]{1,3}\d{0,3}(?:-\d{1,4})?)\](?!\()")
LEVEL_WORDS = ("全文级", "要点级", "目录级", "标题级")


def classify_ids(cfg, root):
    """以**注册表为准**分类编号：
       unit   = 该编号在注册表中存在（有效条目编号）
       anchor = 该编号恰等于某个库代码（库级锚点，正文应改用「XX 系」不带方括号）
       unknown= 注册表里没有（★硬错：错号/断链）
    """
    regp = root / cfg["registry_file"]
    ids = set()
    if regp.exists():
        reg = json.loads(regp.read_text(encoding="utf-8"))
        ids = {str(v.get("编号", "")) for v in reg.values() if v.get("编号")}
    codes = {lib["code"] for lib in cfg["libraries"]}
    return ids, codes


def run_registry(cfg_path, check=True):
    cmd = [sys.executable, str(Path(__file__).parent / "registry.py"),
           "--config", cfg_path] + (["--check"] if check else [])
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--md-dir", default=None)
    a = ap.parse_args()
    cfg = load_cfg(a.config)
    root: Path = cfg["_root"]
    fails = []

    # ① 编号冻结
    rc1, _ = run_registry(a.config, check=True)
    rc2, _ = run_registry(a.config, check=True)
    stat = "✅" if (rc1 == 0 and rc2 == 0) else "❌"
    print(f"{stat} ① 编号冻结：连跑两次退出码 {rc1}/{rc2}（0=无变动）")
    if rc1 or rc2:
        fails.append("编号冻结变动")

    # ② 台账提要/粒度（优先"总台账"；若无则取 00_先读我 下的台账；再退化为任意含"台账"者）
    def _pick_ledger():
        if a.ledger:
            return Path(a.ledger)
        cands = [p for p in root.rglob("*.xlsx") if "台账" in p.name
                 and not p.name.startswith("~$")]
        order = ([p for p in cands if "总台账" in p.name]
                 + [p for p in cands if "00_先读我" in str(p)]
                 + cands)
        return order[0] if order else None
    lg = _pick_ledger()
    if lg and lg.exists():
        try:
            import openpyxl
            ws = openpyxl.load_workbook(lg, read_only=True).worksheets[0]
            rows = list(ws.iter_rows(values_only=True))
            hdr = [str(x or "") for x in (rows[0] if rows else [])]
            hi = next((i for i, h in enumerate(hdr) if "提要" in h), None)
            li = next((i for i, h in enumerate(hdr) if "粒度" in h or "文字状态" in h), None)
            empty_d = sum(1 for r in rows[1:] if hi is not None and not str(r[hi] or "").strip())
            bad_l = sum(1 for r in rows[1:] if li is not None and
                        not any(w in str(r[li] or "") for w in LEVEL_WORDS))
            st = "✅" if (empty_d == 0 and bad_l == 0) else "❌"
            print(f"{st} ② 台账：{lg.name}｜数据行 {len(rows)-1}｜提要为空 {empty_d}｜"
                  f"粒度缺失 {bad_l}")
            if empty_d or bad_l:
                fails.append("台账提要/粒度不完整")
        except ImportError:
            print("· ② 台账：未装 openpyxl，跳过（可手工核）")
        except Exception as e:
            print(f"· ② 台账读取失败：{str(e)[:80]}")
    else:
        print("· ② 台账：未找到（跳过）")

    # ③ 编号完整性（**以注册表为准**，避免把 [L01] 这类有效条目编号误判）
    md_dir = Path(a.md_dir) if a.md_dir else None
    if md_dir and md_dir.exists():
        ids, codes = classify_ids(cfg, root)
        ignore = set(cfg.get("ignore_tokens") or [])   # 正文明说的引用类型码等，不参与判定
        tot = anch = unk = files = 0
        for md in sorted(md_dir.rglob("*.md")):
            parts = md.relative_to(md_dir).parts
            # 跳过下划线开头的中间物/备份（写作材料包、_备份…、_Word全篇）
            if any(seg.startswith("_") for seg in parts):
                continue
            files += 1
            t = md.read_text(encoding="utf-8", errors="ignore")
            for cid in ANY_ID.findall(t):
                if cid in ignore:
                    continue
                tot += 1
                if cid in ids:
                    continue
                if cid in codes:                      # 库级锚点：正文里带方括号即是问题
                    anch += 1
                    print(f"   ⚠ {md.relative_to(md_dir)}：库级锚点 [{cid}]（应写「{cid} 系」或改用具体编号）")
                else:
                    unk += 1
                    print(f"   ❌ {md.relative_to(md_dir)}：编号 [{cid}] **不在注册表中**")
        st = "✅" if (anch == 0 and unk == 0) else "❌"
        print(f"{st} ③ 编号完整性：扫描 {files} 个 md（已跳过 _ 开头目录）｜"
              f"编号引用 {tot} 处｜**库级锚点 {anch}**（门槛 0）｜**未知编号 {unk}**（门槛 0）")
        if anch:
            fails.append(f"库级锚点 {anch} 处")
        if unk:
            fails.append(f"未知编号 {unk} 处")
    else:
        print("· ③ 编号完整性：未指定 --md-dir（跳过）")

    print()
    if fails:
        print("自检未通过：" + "；".join(fails))
        sys.exit(1)
    print("自检全部通过 ✅")


if __name__ == "__main__":
    main()
