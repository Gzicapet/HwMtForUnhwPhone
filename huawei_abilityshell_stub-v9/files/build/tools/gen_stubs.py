#!/usr/bin/env python3
"""分析并生成桩方法：优先转发 AOSP 父类 / 同名 AOSP 类，否则返回默认值。"""
import sys, re, io, os
sys.path.insert(0, '/workspace/tools')
import fix_stubs as F

ROOT = '/workspace/mjar/o2'


def mapped(cls):
    """com.huawei.android.os.ServiceManagerEx -> android.os.ServiceManager"""
    m = re.match(r'^com\.huawei\.android\.(.+?)Ex$', cls)
    if not m:
        return None
    path = m.group(1)
    base = path.split('.')[-1]
    pkg = path[:-len(base) - 1] if '.' in path else ''
    return 'android.' + (pkg + '.' if pkg else '') + base


def scan_params(params):
    """返回 (参数起始寄存器偏移列表, 占用寄存器总数)"""
    regs = []
    n = 0
    i = 0
    while i < len(params):
        c = params[i]
        if c == '[':
            while params[i] == '[':
                i += 1
            i += 1
            regs.append(n); n += 1
        elif c == 'L':
            i = params.index(';', i) + 1
            regs.append(n); n += 1
        elif c in 'JD':
            i += 1
            regs.append(n); regs.append(n + 1); n += 2
        else:
            i += 1
            regs.append(n); n += 1
    return regs, n


def split_sig(sig):
    i = sig.index('('); j = sig.rindex(')')
    return sig[:i], sig[i + 1:j], sig[j + 1:]


results = []
for cls, sigs in F.gaps.items():
    base = F.super_of(cls)
    alt = mapped(cls)
    for sig in sigs:
        name, params, ret = split_sig(sig)
        target = None; static = False; via = ''
        r = F.lookup(base, sig) if base else None
        if r:
            target, static, via = r[0], r[1], 'super'
        elif alt:
            r2 = F.lookup(alt, sig)
            if r2:
                target, static, via = r2[0], r2[1], 'mapped'
        results.append(dict(cls=cls, sig=sig, name=name, params=params, ret=ret,
                            target=target, static=static, via=via))

fwd = [r for r in results if r['target']]
new = [r for r in results if not r['target']]
print('可转发: %d   需默认返回: %d\n' % (len(fwd), len(new)))
print('--- 经「同名 AOSP 类」映射转发 ---')
for r in fwd:
    if r['via'] == 'mapped':
        print('  %s.%s\n        -> %s [%s]' % (r['cls'], r['sig'], r['target'], 'static' if r['static'] else 'instance'))
print('\n--- 需默认返回（全部）---')
for r in new:
    print('  %s.%s' % (r['cls'], r['sig']))
print('\n--- 转发目标分布 ---')
from collections import Counter
for k, v in Counter(r['target'] for r in fwd).most_common(12):
    print('  %-52s %d' % (k, v))
