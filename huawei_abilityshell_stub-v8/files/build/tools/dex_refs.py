#!/usr/bin/env python3
"""从 dex 的 method_ids 表提取「被引用到的」目标类方法，与手写桩对比。
用法: dex_refs.py <桩目录> <dex文件...>
"""
import struct, sys, os, re, glob

def uleb128(d, o):
    r = 0; s = 0
    while True:
        b = d[o]; o += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, o

def read_dex(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'dex\n', path
    ssz, soff = struct.unpack_from('<II', d, 0x38)
    tsz, toff = struct.unpack_from('<II', d, 0x40)
    psz, poff = struct.unpack_from('<II', d, 0x48)
    msz, moff = struct.unpack_from('<II', d, 0x58)

    strings = []
    for i in range(ssz):
        o = struct.unpack_from('<I', d, soff + 4 * i)[0]
        _, o = uleb128(d, o)
        e = d.index(b'\x00', o)
        strings.append(d[o:e].decode('utf-8', 'replace'))

    types = [strings[struct.unpack_from('<I', d, toff + 4 * i)[0]] for i in range(tsz)]

    protos = []
    for i in range(psz):
        si, ri, pa = struct.unpack_from('<III', d, poff + 12 * i)
        protos.append((si, ri, pa))

    def params_desc(pa):
        if pa == 0: return ''
        n = struct.unpack_from('<I', d, pa)[0]
        off = pa + 4
        out = []
        for _ in range(n):
            idx = struct.unpack_from('<H', d, off)[0]; off += 2
            out.append(types[idx])
        return ''.join(out)

    refs = {}
    for i in range(msz):
        ci, pi, ni = struct.unpack_from('<HHI', d, moff + 8 * i)
        cls = types[ci]
        if cls.startswith('L') and cls.endswith(';'):
            cls = cls[1:-1].replace('/', '.')
        _, ri, pa = protos[pi]
        sig = strings[ni] + '(' + params_desc(pa).replace('/', '/') + ')' + types[ri]
        refs.setdefault(cls, set()).add(sig)
    return refs

def stub_methods(root):
    """桩目录 -> {类名(点): set(方法签名)}"""
    out = {}
    for dp, _, fs in os.walk(root):
        for fn in fs:
            if not fn.endswith('.smali'): continue
            p = os.path.join(dp, fn)
            cls = os.path.relpath(p, root)[:-6].replace('/', '.')
            ms = set()
            for line in open(p, encoding='utf-8', errors='ignore'):
                s = line.strip()
                if s.startswith('.method'):
                    ms.add(s.split()[-1])
            out[cls] = ms
    return out

stub_root = sys.argv[1]
dexes = sys.argv[2:]
merged = {}
for dx in dexes:
    r = read_dex(dx)
    for k, v in r.items():
        merged.setdefault(k, set()).update(v)

stubs = stub_methods(stub_root)
common = [c for c in merged if c in stubs]
print(f"═══ 应用引用了 {len(common)} 个「有手写桩」的类 ═══\n")
bad = []
for c in sorted(common):
    ref = merged[c]; st = stubs[c]
    miss = sorted(ref - st)
    if miss: bad.append((c, miss, len(ref), len(st)))
bad.sort(key=lambda x: -len(x[1]))
for c, miss, nr, ns in bad:
    print(f"★ {c}   应用用到 {nr} 个方法，桩有 {ns} 个，缺 {len(miss)} 个")
    for m in miss: print(f"      · {m}")
print(f"\n═══ {len(bad)} 个类存在「应用会调用但桩没有」的方法 ═══")
print(f"═══ 这些就是必然 NoSuchMethodError 的位置 ═══")
