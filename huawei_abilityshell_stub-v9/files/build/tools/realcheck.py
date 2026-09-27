#!/usr/bin/env python3
"""检查固件真类（mjar/o4）的**代码**直接引用了哪些「解析不到」的类型。

用途：判定「删掉遮蔽它的手写桩、让真类接管」是否安全。
判据（与 README 第五节一致）：
  - 只看 .method 体内的代码引用（.annotation 块里的类型不影响运行时，剔除）
  - 只查**直接**引用，不做传递闭包（实测几乎任何类都能连到缺失类型）
输出：每个类的不可解析类型清单 + 引用处，供逐类决定「删桩」还是「补转发」。
"""
import re, sys, os, glob

TYPE = re.compile(r'L[a-zA-Z0-9_$/]+;')
CODE_OPS = ('invoke-', 'new-instance', 'const-class', 'check-cast', 'instance-of',
            'sget', 'sput', 'iget', 'iput', 'filled-new-array', 'new-array',
            'throw', 'move-result-object', 'return-object', 'aput-object', 'aget-object')

universe = set()
for tag in ('app', 'classes2', 'classes3', 'classes4'):
    p = '/tmp/%s.txt' % tag
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            universe.add(line.strip().lstrip('L').rstrip(';').replace('/', '.'))
sys.path.insert(0, '/workspace/tools')
from dexparse import Dex
for f in sorted(glob.glob('/workspace/fw/*.dex') + glob.glob('/workspace/fw2/*/*.dex')):
    t, _ = Dex(f).build()
    universe.update(t.keys())
# 桩里定义的类型也算「我们提供了」
for root in ('/workspace/mjar/o2',):
    for dp, _, fs in os.walk(root):
        for fn in fs:
            if fn.endswith('.smali'):
                universe.add(os.path.relpath(os.path.join(dp, fn), root)[:-6].replace('/', '.'))
print("可解析类型全集: %d" % len(universe))


def check(cls, root='/workspace/mjar/o4'):
    p = os.path.join(root, cls.replace('.', '/') + '.smali')
    if not os.path.exists(p):
        return None
    bad = []
    in_method = False
    in_annotation = False
    for ln, raw in enumerate(open(p, encoding='utf-8', errors='ignore'), 1):
        s = raw.strip()
        if s.startswith('.method'):
            in_method = True
            continue
        if s.startswith('.end method'):
            in_method = False
            continue
        if s.startswith('.annotation'):
            in_annotation = True
            continue
        if s.startswith('.end annotation'):
            in_annotation = False
            continue
        if not in_method or in_annotation:
            continue
        if s.startswith('#') or s.startswith('.line') or s.startswith('.local') or s.startswith('.param'):
            continue
        for m in TYPE.finditer(s):
            t = m.group(0)[1:-1].replace('/', '.')
            if t not in universe:
                bad.append((ln, t, s[:110]))
    return bad


for cls in sys.argv[1:]:
    bad = check(cls)
    if bad is None:
        print("■ %-58s 真类不存在（o4 无此文件）" % cls)
        continue
    uniq = sorted(set(t for _, t, _ in bad))
    print("■ %-58s 直接引用缺失类型 %d 个" % (cls, len(uniq)))
    for t in uniq:
        sample = [x for x in bad if x[1] == t][0]
        print("      ✗ %-60s  (L%d) %s" % (t, sample[0], sample[2]))
