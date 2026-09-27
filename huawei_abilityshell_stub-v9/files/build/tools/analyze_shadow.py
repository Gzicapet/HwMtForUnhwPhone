#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为「桩 vs 固件真类」的选择生成严格判据。

教训
----
上一版只用「类能否 Class.forName 成功」做判据，结果漏掉了 ImmersionStyle：
它本身加载成功，但方法体引用 android.hwcontrol.HwWidgetFactory（非华为机上不存在），
一执行就 NoClassDefFoundError 把应用打崩。

因此正确判据必须覆盖「可达性」：
  若真类（含其传递引用）能到达任何一个不可解析的类型 → 必须保留桩兜底。

方法
----
1. BAD  = 校验台在真机上枚举出的、jar 引用但无法解析的类型（568 个，平台即 Ground Truth）
2. 为每个 jar 内类提取它引用的全部类型（正则扫 smali，宁多勿漏）
3. 反向 BFS：算出所有「能到达 BAD」的类
4. 对每个与桩重名的类：
     真类能到达 BAD → 保留桩
     否则           → 丢桩，让真类胜出（语义更正确）
"""

import io
import os
import re
import sys
from collections import defaultdict, deque

WS = '/workspace'
MJ = os.path.join(WS, 'mjar')
DIRS = ['o1', 'o2', 'o3', 'o4']          # 对应 classes.dex ~ classes4.dex
TYPE_RE = re.compile(r'L[0-9a-zA-Z_$/]+;')


def norm(desc):
    return desc[1:-1].replace('/', '.')


def collect_classes(root):
    out = set()
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.endswith('.smali'):
                rel = os.path.relpath(os.path.join(dp, f), root)
                out.add(rel[:-6].replace('/', '.'))
    return out


def refs_of(path):
    txt = io.open(path, encoding='utf-8', errors='replace').read()
    return {norm(d) for d in TYPE_RE.findall(txt)}


def main():
    bad = set()
    for line in io.open(os.path.join(WS, 'badres.txt'), encoding='utf-8', errors='replace'):
        if line.startswith('FAIL '):
            bad.add(line[5:].split(' :')[0].strip())
    print('  BAD（不可解析类型）: %d' % len(bad))

    defined = {}          # 类 -> 提供它的 dex 序号（小 = 优先）
    refs = {}             # 类 -> 引用类型集合
    for i, d in enumerate(DIRS, 1):
        root = os.path.join(MJ, d)
        if not os.path.isdir(root):
            continue
        for cls in collect_classes(root):
            f = os.path.join(root, cls.replace('.', '/') + '.smali')
            if not os.path.exists(f):
                continue
            defined.setdefault(cls, i)
            refs.setdefault(cls, set())
            refs[cls] |= refs_of(f)
    print('  jar 定义类: %d' % len(defined))

    # 反向边：被引用者 -> 引用者
    rev = defaultdict(set)
    for cls, rs in refs.items():
        for r in rs:
            rev[r].add(cls)

    # 从 BAD 反向 BFS（BAD 自身也算「能到达」）
    reach = set(bad)
    q = deque(bad)
    while q:
        cur = q.popleft()
        for p in rev.get(cur, ()):
            if p not in reach:
                reach.add(p)
                q.append(p)
    print('  能到达 BAD 的类: %d' % len(reach))

    # 影子类决策
    stubs = collect_classes(os.path.join(MJ, 'o2'))
    keep, drop = [], []
    for cls in sorted(stubs):
        # 真类所在 dex：o3 优先于 o4
        real = None
        for idx in (3, 4):
            if defined.get(cls) == idx:
                real = DIRS[idx - 1]
                break
        if real is None:
            keep.append((cls, '独有'))
            continue
        if cls in reach:
            keep.append((cls, real))
        else:
            drop.append((cls, real))

    print()
    print('  ★ 保留桩（真类可到达 BAD）: %d' % len(keep))
    print('  ★ 丢弃桩（真类安全）      : %d' % len(drop))
    print()
    print('  ── 丢弃清单 ──')
    for c, _ in drop:
        print('    %s' % c)

    io.open(os.path.join(WS, 'keep_stubs.txt'), 'w', encoding='utf-8').write(
        '\n'.join(c for c, _ in keep) + '\n')
    io.open(os.path.join(WS, 'drop_stubs.txt'), 'w', encoding='utf-8').write(
        '\n'.join(c for c, _ in drop) + '\n')
    print()
    print('  已写出 keep_stubs.txt / drop_stubs.txt')


if __name__ == '__main__':
    sys.exit(main())
