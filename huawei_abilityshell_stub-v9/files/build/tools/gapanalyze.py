#!/usr/bin/env python3
"""判断「应用会调用但桩文件里没有」的方法是否真会在运行时失败。

ART 对 invoke-* 的方法解析沿**运行时类的父类链**查找，而 classes2.dex(桩)
先于 classes3/4.dex(固件真类)，同名真类被遮蔽、不进父类链。
本脚本严格按运行时优先顺序（stub → fw3 → fw4 → framework/core → java.lang.Object）
取**该名字的定义者**再沿 .super 上溯：
  OK   父类链上能解析（含 Object.toString 这类）→ 无风险
  GAP  链上完全找不到 → 必然 NoSuchMethodError / IncompatibleClassChangeError
GAP 按类汇总，并给出固件真类（fw4 同名类）里的对应声明作为修法依据。
"""
import re, sys, glob, os
sys.path.insert(0, '/workspace/tools')
from dexparse import Dex, ACC_STATIC, ACC_ABSTRACT, ACC_NATIVE

ROOTS = [('/workspace/mjar/o2', 'stub'), ('/workspace/mjar/o3', 'fw3'), ('/workspace/mjar/o4', 'fw4')]
FLAGS = {'public': 1, 'private': 2, 'protected': 4, 'static': ACC_STATIC, 'final': 0x10,
         'synchronized': 0x20, 'abstract': ACC_ABSTRACT, 'native': ACC_NATIVE,
         'constructor': 0x10000, 'declared-synchronized': 0x20000, 'strictfp': 0x800,
         'synthetic': 0x1000, 'interface': 0x200}


def load_smali(root):
    methods, sup = {}, {}
    for dp, _, fs in os.walk(root):
        for fn in fs:
            if not fn.endswith('.smali'):
                continue
            p = os.path.join(dp, fn)
            cls = os.path.relpath(p, root)[:-6].replace('/', '.')
            ms, s = {}, None
            for line in open(p, encoding='utf-8', errors='ignore'):
                line = line.strip()
                if line.startswith('.super '):
                    t = line.split()[-1]
                    s = t[1:-1].replace('/', '.') if t.startswith('L') else t
                elif line.startswith('.method'):
                    toks = line.split()
                    acc = 0
                    for a in toks[1:-1]:
                        acc |= FLAGS.get(a, 0)
                    ms[toks[-1]] = acc
            methods[cls] = ms
            sup[cls] = s
    return methods, sup


ORDER = []
for root, tag in ROOTS:
    m, s = load_smali(root)
    ORDER.append((tag, m, s))
fw_m, fw_s = {}, {}
for f in sorted(glob.glob('/workspace/fw/*.dex') + glob.glob('/workspace/fw2/*/*.dex')):
    t, s = Dex(f).build()
    for k, v in t.items():
        fw_m.setdefault(k, {}).update(v)
    for k, v in s.items():
        fw_s.setdefault(k, v)
ORDER.append(('fw', fw_m, fw_s))
SUPERS = {}
for tag, m, s in ORDER:
    for k, v in s.items():
        SUPERS.setdefault(k, v)
SUPERS.setdefault('java.lang.Object', None)


def define(cls):
    for tag, m, s in ORDER:
        if cls in m:
            return m[cls], s.get(cls), tag
    return None, None, None


def lookup(cls, sig):
    seen, c = set(), cls
    while c and c not in seen:
        seen.add(c)
        ms, sup, tag = define(c)
        if ms is not None and sig in ms:
            return c, ms[sig], tag
        c = sup if sup is not None else SUPERS.get(c)
    return None


def fw4_of(cls):
    for tag, m, s in ORDER:
        if tag == 'fw4':
            return m.get(cls), s.get(cls)
    return None, None


gaps, cur = {}, None
for line in open('/tmp/refs.txt', encoding='utf-8'):
    mm = re.match(r'^\u2605 (\S+)\s', line)
    if mm:
        cur = mm.group(1)
        gaps[cur] = []
    elif cur and line.strip().startswith('\u00b7'):
        gaps[cur].append(line.strip()[1:].strip())

n_ok = n_gap = 0
print("═══ 真缺陷清单（父类链完全解析不到）═══\n")
for cls in sorted(gaps):
    bad = []
    for sig in gaps[cls]:
        if lookup(cls, sig):
            n_ok += 1
        else:
            n_gap += 1
            bad.append(sig)
    if not bad:
        continue
    fwm, fws = fw4_of(cls)
    print("■ %s" % cls)
    if fwm is None:
        print("    固件真类: 不存在（必须自己实现）")
    else:
        print("    固件真类: 存在，父类 %s，共 %d 个方法" % (fws, len(fwm)))
    for sig in bad:
        acc = fwm.get(sig) if fwm else None
        if acc is None:
            note = '真类无此签名'
        else:
            note = '真类有: ' + ('static' if acc & ACC_STATIC else 'virtual') + \
                   (' abstract' if acc & ACC_ABSTRACT else '') + (' native' if acc & ACC_NATIVE else '')
        print("      · %-78s %s" % (sig, note))
    print()
print("═══ 汇总：全部 %d 个「缺失」中，可解析 %d，真缺陷 %d ═══" % (n_ok + n_gap, n_ok, n_gap))
