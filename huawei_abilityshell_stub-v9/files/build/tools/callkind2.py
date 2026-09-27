#!/usr/bin/env python3
"""精确统计应用 dex 对某方法的调用指令（按指令边界解码，避免字节模式误报）。

用法: callkind2.py <类名> <方法签名> [dex 目录]
输出: 每个 dex 的命中共几处、指令种类、所在类/方法。
"""
import struct, sys, glob, os

UNUSED = -1
L = [1] * 256
for op, ln in {0x02: 2, 0x03: 3, 0x05: 2, 0x06: 3, 0x08: 2, 0x09: 3,
               0x13: 2, 0x14: 3, 0x15: 2, 0x16: 2, 0x17: 3, 0x18: 5, 0x19: 2,
               0x1a: 2, 0x1b: 3, 0x1c: 2, 0x1f: 2, 0x20: 2, 0x22: 2, 0x23: 2,
               0x24: 3, 0x25: 3, 0x26: 3, 0x29: 2, 0x2a: 3, 0x2b: 3, 0x2c: 3}.items():
    L[op] = ln
for op in range(0x2d, 0x3e):
    L[op] = 2
for op in range(0x44, 0x6e):
    L[op] = 2
for op in range(0x6e, 0x73):
    L[op] = 3
for op in range(0x74, 0x79):
    L[op] = 3
for op in range(0x90, 0xe3):
    L[op] = 2
for op in (0xfa, 0xfb):
    L[op] = 4
for op in (0xfc, 0xfd):
    L[op] = 3
for op in (0xfe, 0xff):
    L[op] = 2
for op in (0x3e, 0x3f, 0x40, 0x41, 0x42, 0x43, 0x73, 0x79, 0x7a):
    L[op] = UNUSED
INV = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super', 0x70: 'invoke-direct',
       0x71: 'invoke-static', 0x72: 'invoke-interface',
       0x74: 'invoke-virtual/range', 0x75: 'invoke-super/range',
       0x76: 'invoke-direct/range', 0x77: 'invoke-static/range',
       0x78: 'invoke-interface/range'}


def uleb(d, o):
    r = 0
    s = 0
    while True:
        b = d[o]
        o += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80):
            break
        s += 7
    return r, o


class D:
    def __init__(self, path):
        self.path = path
        self.d = d = open(path, 'rb').read()
        self.ssz, self.soff = struct.unpack_from('<II', d, 0x38)
        self.tsz, self.toff = struct.unpack_from('<II', d, 0x40)
        self.psz, self.poff = struct.unpack_from('<II', d, 0x48)
        self.msz, self.moff = struct.unpack_from('<II', d, 0x58)
        self.csz, self.coff = struct.unpack_from('<II', d, 0x60)
        self.strings = []
        for i in range(self.ssz):
            o = struct.unpack_from('<I', d, self.soff + 4 * i)[0]
            _, o = uleb(d, o)
            e = d.index(b'\x00', o)
            self.strings.append(d[o:e].decode('utf-8', 'replace'))
        self.types = [self.strings[struct.unpack_from('<I', d, self.toff + 4 * i)[0]]
                      for i in range(self.tsz)]
        self.protos = [struct.unpack_from('<III', d, self.poff + 12 * i) for i in range(self.psz)]

    def mstr(self, i):
        ci, pi, ni = struct.unpack_from('<HHI', self.d, self.moff + 8 * i)
        _, ri, pa = self.protos[pi]
        params = ''
        if pa:
            n = struct.unpack_from('<I', self.d, pa)[0]
            o = pa + 4
            for _ in range(n):
                params += self.types[struct.unpack_from('<H', self.d, o)[0]]
                o += 2
        return self.types[ci], self.strings[ni] + '(' + params + ')' + self.types[ri]

    def classes(self):
        """-> (类名, [(方法名签名, code_off)])"""
        d = self.d
        for i in range(self.csz):
            off = self.coff + 32 * i
            cidx, acc, sidx, ifo, src, an, cdata, sv = struct.unpack_from('<IIIIIIII', d, off)
            t = self.types[cidx]
            if not t.startswith('L'):
                continue
            cls = t[1:-1].replace('/', '.')
            ms = []
            if cdata:
                o = cdata
                sf, o = uleb(d, o)
                inf, o = uleb(d, o)
                dm, o = uleb(d, o)
                vm, o = uleb(d, o)
                for _ in range(sf + inf):
                    _, o = uleb(d, o)
                    _, o = uleb(d, o)
                for _ in range(dm + vm):
                    di, o = uleb(d, o)
                    ai, o = uleb(d, o)
                    co, o = uleb(d, o)
                    ms.append(ai)
            yield cls, ms

    def invokes_in(self, code_off, want_idx):
        """返回 [(指令种类, 目标 index)] —— 在一条方法体内按指令边界解码。"""
        d = self.d
        rsz, isz, osz, tsz = struct.unpack_from('<HHHH', d, code_off)
        insz, = struct.unpack_from('<I', d, code_off + 12)
        base = code_off + 16
        out = []
        i = 0
        while i < insz:
            u = struct.unpack_from('<H', d, base + 2 * i)[0]
            op = u & 0xff
            if u == 0:
                i += 1
                continue
            if op == 0x00 and u != 0:      # payload 伪指令
                kind = u >> 8
                if kind in (1, 2):          # packed-switch / sparse-switch
                    sz = struct.unpack_from('<H', d, base + 2 * i + 2)[0]
                    i += 2 + sz * 4
                elif kind == 3:             # fill-array-data
                    ew = struct.unpack_from('<H', d, base + 2 * i + 2)[0] & 0xff
                    sz, = struct.unpack_from('<I', d, base + 2 * i + 4)
                    i += 4 + ((sz * ew + 1) // 2)
                else:
                    break
                continue
            ln = L[op]
            if ln == UNUSED:
                break
            if op in INV:
                if op <= 0x72:
                    idx = struct.unpack_from('<H', d, base + 2 * i + 4)[0]
                else:
                    idx = struct.unpack_from('<H', d, base + 2 * i + 2)[0]
                if idx == want_idx:
                    out.append(INV[op])
            i += ln
        return out


cls = sys.argv[1].replace('.', '/')
if not cls.startswith('L'):
    cls = 'L' + cls + ';'
sig = sys.argv[2]
dirs = sys.argv[3] if len(sys.argv) > 3 else '/workspace/meetime_dex'
total = {}
detail = []
for f in sorted(glob.glob(os.path.join(dirs, '*.dex'))):
    dx = D(f)
    idxs = [i for i in range(dx.msz) if dx.mstr(i) == (cls, sig)]
    if not idxs:
        continue
    for c, ms in dx.classes():
        for m in ms:
            h = dx.invokes_in(m, idxs[0])
            if h:
                mname = dx.mstr(m)[1]
                detail.append((os.path.basename(f), c, mname, h))
                for k in h:
                    total[k] = total.get(k, 0) + 1
print('目标: %s->%s' % (sys.argv[1], sig))
for d_, c_, m_, h_ in detail:
    print('   %-18s %s.%s  %s' % (d_, c_, m_, h_))
print('合计: %s' % (total if total else '未找到调用'))
