#!/usr/bin/env python3
"""把缺失方法生成为 smali 并追加到桩文件。
   转发：父类/同名 AOSP 类有同签名 -> invoke 过去
   默认：返回 0 / "" / null（String 一律返回 ""，避免调用方 .isEmpty() NPE）
"""
import sys, re, io, os
sys.path.insert(0, '/workspace/tools')
import fix_stubs as F

ROOT = '/workspace/mjar/o2'
WRITE = len(sys.argv) > 1 and sys.argv[1] == 'write'


def mapped(cls):
    m = re.match(r'^com\.huawei\.android\.(.+?)Ex$', cls)
    if not m:
        return None
    path = m.group(1)
    base = path.split('.')[-1]
    pkg = path[:-len(base) - 1] if '.' in path else ''
    return 'android.' + (pkg + '.' if pkg else '') + base


def split_sig(sig):
    i = sig.index('('); j = sig.rindex(')')
    return sig[:i], sig[i + 1:j], sig[j + 1:]


def call_regs(params, static):
    """返回 (调用用寄存器列表, 参数占的寄存器数)"""
    regs = [] if static else ['p0']
    base = 0 if static else 1
    n = 0
    i = 0
    while i < len(params):
        c = params[i]
        if c == '[':
            while params[i] == '[':
                i += 1
            i += 1
            regs.append('p%d' % (base + n)); n += 1
        elif c == 'L':
            i = params.index(';', i) + 1
            regs.append('p%d' % (base + n)); n += 1
        elif c in 'JD':
            i += 1
            regs.append('p%d' % (base + n))
            regs.append('p%d' % (base + n + 1))
            n += 2
        else:
            i += 1
            regs.append('p%d' % (base + n)); n += 1
    return regs, n


def ret_kind(ret):
    if ret == 'V': return 'void'
    if ret in 'JD': return 'wide'
    if ret.startswith('L') or ret.startswith('['): return 'object'
    return 'narrow'


def inv(op, regs, tgt, sig):
    if len(regs) <= 5:
        return '    %s {%s}, L%s;->%s' % (op, ', '.join(regs), tgt, sig)
    return '    %s/range {%s .. %s}, L%s;->%s' % (op, regs[0], regs[-1], tgt, sig)


def emit(cls, sig, target, static):
    name, params, ret = split_sig(sig)
    regs, npar = call_regs(params, static)
    ins = npar + (0 if static else 1)
    acc = 'public static' if static else 'public'
    L = ['.method %s %s' % (acc, sig)]
    if name == '<init>' and target:
        L.append('    .registers %d' % ins)
        L.append(inv('invoke-direct', regs, target.replace('.', '/'), sig))
        L.append('    return-void')
    elif target:
        k = ret_kind(ret)
        need = 0 if k == 'void' else 1
        L.append('    .registers %d' % (ins + need))
        op = 'invoke-static' if static else 'invoke-virtual'
        L.append(inv(op, regs, target.replace('.', '/'), sig))
        if k == 'void':
            L.append('    return-void')
        else:
            suff = {'object': '-object', 'wide': '-wide', 'narrow': ''}[k]
            L.append('    move-result%s v0' % suff)
            L.append('    return%s v0' % suff)
    else:
        k = ret_kind(ret)
        L.append('    .registers %d' % (ins + 1))
        if k == 'void':
            L.append('    return-void')
        elif k == 'wide':
            L.append('    const-wide/16 v0, 0x0')
            L.append('    return-wide v0')
        elif ret == 'Ljava/lang/String;':
            L.append('    const-string v0, ""')
            L.append('    return-object v0')
        elif k == 'object':
            L.append('    const/4 v0, 0x0')
            L.append('    return-object v0')
        else:
            L.append('    const/4 v0, 0x0')
            L.append('    return v0')
    L.append('.end method')
    return '\n'.join(L)


stat = {'fwd': 0, 'def': 0, 'skip': 0, 'files': 0}
plan = {}
for cls, sigs in F.gaps.items():
    base = F.super_of(cls)
    alt = mapped(cls)
    for sig in sigs:
        target = None; static = False
        r = F.lookup(base, sig) if base else None
        if r:
            target, static = r[0], r[1]
        elif alt:
            r2 = F.lookup(alt, sig)
            if r2:
                target, static = r2[0], r2[1]
        plan.setdefault(cls, []).append((sig, target, static))

for cls, items in plan.items():
    path = os.path.join(ROOT, cls.replace('.', '/') + '.smali')
    if not os.path.exists(path):
        print('  !! 桩文件不存在: %s' % cls)
        continue
    src = io.open(path, encoding='utf-8').read()
    add = []
    for sig, target, static in items:
        name = sig[:sig.index('(')]
        if re.search(r'^\s*\.method .*\b%s\(' % re.escape(name), src, re.M):
            stat['skip'] += 1
            continue
        add.append(emit(cls, sig, target, static))
        if target: stat['fwd'] += 1
        else: stat['def'] += 1
    if add:
        stat['files'] += 1
        if WRITE:
            io.open(path, 'w', encoding='utf-8').write(src.rstrip('\n') + '\n\n' + '\n\n'.join(add) + '\n')

print('模式: %s' % ('写入' if WRITE else '试运行'))
print('  转发方法: %d' % stat['fwd'])
print('  默认返回: %d' % stat['def'])
print('  已存在跳过: %d' % stat['skip'])
print('  修改文件: %d' % stat['files'])
