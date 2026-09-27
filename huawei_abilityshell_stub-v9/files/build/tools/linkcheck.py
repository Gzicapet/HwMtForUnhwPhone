#!/usr/bin/env python3
"""检查「固件真类」的方法体在**本机运行时**是否完全可链接。

删掉遮蔽真类的手写桩前，必须回答两个问题：
  1. 它引用的类型在应用类加载器里都能解析吗（app dex + jar + boot classpath）？
  2. 它调用的方法（含父类链）都真的存在吗？
只做**直接**引用检查（传递闭包无意义，实测几乎任何类都能连到缺失类型）。
"""
import re, sys, os, glob

TYPE = re.compile(r'L[a-zA-Z0-9_$/]+;')
INV = re.compile(r'invoke-\S+\s+\{[^}]*\},\s*(L[^;]+;)->(\S+?)(\([^)]*\)\S+)')
FIELD = re.compile(r'^\.field.*?:([L\[][^;\s]+;|[BCDFIJSZ])')
SUPER = re.compile(r'^\.super\s+(L[^;]+;)')

sys.path.insert(0, '/workspace/tools')
from dexparse import Dex

# ── 构建运行时可见类型/方法表（按优先级）──
import itertools
ORDER = []
for root, tag in (('/workspace/mjar/o2', 'stub'), ('/workspace/mjar/o3', 'fw3'), ('/workspace/mjar/o4', 'fw4')):
    m, s = {}, {}
    for dp, _, fs in os.walk(root):
        for fn in fs:
            if not fn.endswith('.smali'):
                continue
            p = os.path.join(dp, fn)
            cls = os.path.relpath(p, root)[:-6].replace('/', '.')
            sigs, sup = [], None
            for line in open(p, encoding='utf-8', errors='ignore'):
                line = line.strip()
                if line.startswith('.super '):
                    t = line.split()[-1]
                    sup = t[1:-1].replace('/', '.') if t.startswith('L') else t
                elif line.startswith('.method'):
                    sigs.append(line.split()[-1])
            m[cls] = set(sigs)
            s[cls] = sup
    ORDER.append((tag, m, s))

fw_m, fw_s = {}, {}
for f in sorted(glob.glob('/workspace/fw/*.dex') + glob.glob('/workspace/fw2/*/*.dex')):
    t, s = Dex(f).build()
    for k, v in t.items():
        fw_m.setdefault(k, set()).update(v.keys())
    for k, v in s.items():
        fw_s.setdefault(k, v)
ORDER.append(('fw', fw_m, fw_s))
# 应用自身 dex 也可见
app = set()
for line in open('/tmp/app.txt', encoding='utf-8'):
    t = line.strip()
    if t.startswith('L') and t.endswith(';'):
        app.add(t[1:-1].replace('/', '.'))
VISIBLE = set(fw_m) | app
for tag, m, s in ORDER[:3]:
    VISIBLE |= set(m)
SUPERS = {}
for tag, m, s in ORDER:
    for k, v in s.items():
        SUPERS.setdefault(k, v)


IGNORE_STUB = set()


def define(cls):
    for tag, m, s in ORDER:
        if tag == 'stub' and cls in IGNORE_STUB:
            continue
        if cls in m:
            return m[cls], s.get(cls)
    return None, None


def has_method(cls, name, sig):
    seen, c = set(), cls
    while c and c not in seen:
        seen.add(c)
        ms, sup = define(c)
        if ms is not None and (name + sig) in ms:
            return True, c
        c = sup if sup is not None else SUPERS.get(c)
    return False, None


def check(path):
    bad_type, bad_meth = [], []
    in_method = False
    in_ann = False
    sup = None
    for ln, raw in enumerate(open(path, encoding='utf-8', errors='ignore'), 1):
        s = raw.strip()
        if s.startswith('.super '):
            m = SUPER.match(s)
            if m:
                sup = m.group(1)[1:-1].replace('/', '.')
            continue
        if s.startswith('.method'):
            in_method = True
            continue
        if s.startswith('.end method'):
            in_method = False
            continue
        if s.startswith('.annotation'):
            in_ann = True
            continue
        if s.startswith('.end annotation'):
            in_ann = False
            continue
        if not in_method or in_ann:
            continue
        if s.startswith('#') or s.startswith('.line') or s.startswith('.local') or s.startswith('.param'):
            continue
        for m in INV.finditer(s):
            cls = m.group(1)[1:-1].replace('/', '.')
            name, sig = m.group(2), m.group(3)
            if cls not in VISIBLE:
                bad_type.append((ln, cls, s[:110]))
                continue
            ok, _ = has_method(cls, name, sig)
            if not ok:
                bad_meth.append((ln, cls + '->' + name + sig, s[:110]))
        for m in TYPE.finditer(s):
            t = m.group(0)[1:-1].replace('/', '.')
            if t not in VISIBLE:
                bad_type.append((ln, t, s[:110]))
    return sup, bad_type, bad_meth


IGNORE_STUB.update(sys.argv[1:])

for cls in sys.argv[1:]:
    p = os.path.join('/workspace/mjar/o4', cls.replace('.', '/') + '.smali')
    if not os.path.exists(p):
        print("■ %-56s 真类不存在" % cls)
        continue
    sup, bt, bm = check(p)
    supok = sup in VISIBLE if sup else False
    print("■ %s" % cls)
    print("    父类 %-52s %s" % (sup, 'OK' if supok else '缺失!'))
    real_bt = sorted(set(x[1] for x in bt))
    real_bm = sorted(set(x[1] for x in bm))
    print("    缺失类型 %d 个: %s" % (len(real_bt), ', '.join(real_bt) if real_bt else '无'))
    for x in real_bt:
        s = [y for y in bt if y[1] == x][0]
        print("        ✗ (L%d) %s" % (s[0], s[2]))
    print("    解析不到的方法 %d 个" % len(real_bm))
    for x in real_bm[:12]:
        s = [y for y in bm if y[1] == x][0]
        print("        ✗ %-70s (L%d)" % (x, s[0]))
    print()
