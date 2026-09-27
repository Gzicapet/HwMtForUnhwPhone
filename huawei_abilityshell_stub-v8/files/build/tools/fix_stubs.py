#!/usr/bin/env python3
"""为桩补齐缺失方法：super 链上有同签名 -> 转发；没有 -> 返回默认值。"""
import struct, glob, re

def uleb(d, o):
    r = 0; s = 0
    while True:
        b = d[o]; o += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, o

class Dex:
    def __init__(self, path):
        d = open(path, 'rb').read(); self.d = d
        self.ssz, self.soff = struct.unpack_from('<II', d, 0x38)
        self.tsz, self.toff = struct.unpack_from('<II', d, 0x40)
        self.psz, self.poff = struct.unpack_from('<II', d, 0x48)
        self.msz, self.moff = struct.unpack_from('<II', d, 0x58)
        self.csz, self.coff = struct.unpack_from('<II', d, 0x60)
        self.strings = []
        for i in range(self.ssz):
            o = struct.unpack_from('<I', d, self.soff + 4 * i)[0]
            _, o = uleb(d, o); e = d.index(b'\x00', o)
            self.strings.append(d[o:e].decode('utf-8', 'replace'))
        self.types = [self.strings[struct.unpack_from('<I', d, self.toff + 4 * i)[0]] for i in range(self.tsz)]
        self.protos = [struct.unpack_from('<III', d, self.poff + 12 * i) for i in range(self.psz)]
        self.methods = [struct.unpack_from('<HHI', d, self.moff + 8 * i) for i in range(self.msz)]

    def params(self, pa):
        if pa == 0: return ''
        d = self.d; n = struct.unpack_from('<I', d, pa)[0]; out = []; o = pa + 4
        for _ in range(n):
            out.append(self.types[struct.unpack_from('<H', d, o)[0]]); o += 2
        return ''.join(out)

    def sig(self, mi):
        ci, pi, ni = self.methods[mi]
        _, ri, pa = self.protos[pi]
        return self.strings[ni] + '(' + self.params(pa) + ')' + self.types[ri]

    def build(self):
        d = self.d; tbl = {}; sup = {}
        for i in range(self.csz):
            off = self.coff + 32 * i
            cidx, acc, sidx, ifo, src, an, cdata, sv = struct.unpack_from('<IIIIIIII', d, off)
            t = self.types[cidx]
            if not t.startswith('L'): continue
            cls = t[1:-1].replace('/', '.')
            if sidx == 0xFFFFFFFF or sidx >= len(self.types):
                sup[cls] = None
            else:
                st = self.types[sidx]
                sup[cls] = st[1:-1].replace('/', '.') if st.startswith('L') else st
            if cdata == 0: continue
            for mi, macc, code, kind in self.parse_cd(cdata):
                tbl.setdefault(cls, {})[self.sig(mi)] = (macc, kind)
        return tbl, sup

    def parse_cd(self, off):
        d = self.d; o = off
        sf, o = uleb(d, o); inf, o = uleb(d, o)
        dm, o = uleb(d, o); vm, o = uleb(d, o)
        for _ in range(sf + inf):
            _, o = uleb(d, o); _, o = uleb(d, o)
        out = []; midx = 0
        for _ in range(dm):
            diff, o = uleb(d, o); midx += diff
            acc, o = uleb(d, o); code, o = uleb(d, o)
            out.append((midx, acc, code, 'direct'))
        midx = 0
        for _ in range(vm):
            diff, o = uleb(d, o); midx += diff
            acc, o = uleb(d, o); code, o = uleb(d, o)
            out.append((midx, acc, code, 'virtual'))
        return out

ACC_STATIC = 0x8
fw = {}; fw_sup = {}
for f in sorted(glob.glob('/workspace/fw/*.dex') + glob.glob('/workspace/fw2/*/*.dex')):
    dx = Dex(f); t, s = dx.build()
    for k, v in t.items(): fw.setdefault(k, {}).update(v)
    for k, v in s.items(): fw_sup.setdefault(k, v)
print("framework 类表: %d 个类" % len(fw))

gaps = {}; cur = None
for line in open('/tmp/refs.txt', encoding='utf-8'):
    m = re.match(r'^\u2605 (\S+)\s', line)
    if m:
        cur = m.group(1); gaps[cur] = []
    elif cur and line.strip().startswith('\u00b7'):
        gaps[cur].append(line.strip()[1:].strip())
print("待补齐类: %d 个，方法合计 %d" % (len(gaps), sum(len(v) for v in gaps.values())))

def lookup(cls, sig):
    seen = set(); c = cls
    while c and c not in seen:
        seen.add(c)
        if c in fw and sig in fw[c]:
            acc, kind = fw[c][sig]
            return (c, bool(acc & ACC_STATIC))
        c = fw_sup.get(c)
    return None

def super_of(cls):
    path = "mjar/o2/%s.smali" % cls.replace('.', '/')
    try:
        for line in open(path, encoding='utf-8'):
            if line.startswith('.super'):
                t = line.split()[-1].strip()
                if t.startswith('L') and t.endswith(';'):
                    return t[1:-1].replace('/', '.')
    except IOError:
        pass
    return None

report = []
for cls, sigs in gaps.items():
    base = super_of(cls)
    if not base:
        print("  !! 无法确定 super: %s" % cls)
    for sig in sigs:
        r = lookup(base if base else cls, sig)
        if r: report.append((cls, sig, 'FWD', r[0], 'static' if r[1] else 'virtual'))
        else: report.append((cls, sig, 'NEW', None, None))

fwd = [r for r in report if r[2] == 'FWD']
new = [r for r in report if r[2] == 'NEW']
print("\n可转发给 AOSP 父类: %d" % len(fwd))
print("父类也没有(需默认返回): %d\n" % len(new))
print("--- 可转发样本 ---")
for r in fwd[:10]: print("  %s.%s  ->  %s [%s]" % (r[0], r[1], r[3], r[4]))
print("\n--- 需默认返回 ---")
for r in new[:30]: print("  %s.%s" % (r[0], r[1]))
