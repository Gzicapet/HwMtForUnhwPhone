#!/usr/bin/env python3
"""dex 解析器（从 fix_stubs.py 提取，供分析脚本复用）。"""
import struct

ACC_STATIC = 0x8
ACC_ABSTRACT = 0x400
ACC_NATIVE = 0x100


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


class Dex:
    def __init__(self, path):
        d = open(path, 'rb').read()
        self.d = d
        assert d[:4] == b'dex\n', path
        self.path = path
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
        self.methods = [struct.unpack_from('<HHI', d, self.moff + 8 * i) for i in range(self.msz)]

    def params(self, pa):
        if pa == 0:
            return ''
        d = self.d
        n = struct.unpack_from('<I', d, pa)[0]
        out = []
        o = pa + 4
        for _ in range(n):
            out.append(self.types[struct.unpack_from('<H', d, o)[0]])
            o += 2
        return ''.join(out)

    def sig(self, mi):
        ci, pi, ni = self.methods[mi]
        _, ri, pa = self.protos[pi]
        return self.strings[ni] + '(' + self.params(pa) + ')' + self.types[ri]

    def build(self):
        """-> ({类: {签名: 访问标志}}, {类: 父类名})"""
        d = self.d
        tbl = {}
        sup = {}
        for i in range(self.csz):
            off = self.coff + 32 * i
            cidx, acc, sidx, ifo, src, an, cdata, sv = struct.unpack_from('<IIIIIIII', d, off)
            t = self.types[cidx]
            if not t.startswith('L'):
                continue
            cls = t[1:-1].replace('/', '.')
            if sidx == 0xFFFFFFFF or sidx >= len(self.types):
                sup[cls] = None
            else:
                st = self.types[sidx]
                sup[cls] = st[1:-1].replace('/', '.') if st.startswith('L') else st
            tbl.setdefault(cls, {})
            if cdata == 0:
                continue
            for mi, macc, code, kind in self.parse_cd(cdata):
                tbl.setdefault(cls, {})[self.sig(mi)] = macc
        return tbl, sup

    def parse_cd(self, off):
        d = self.d
        o = off
        sf, o = uleb(d, o)
        inf, o = uleb(d, o)
        dm, o = uleb(d, o)
        vm, o = uleb(d, o)
        for _ in range(sf + inf):
            _, o = uleb(d, o)
            _, o = uleb(d, o)
        out = []
        midx = 0
        for _ in range(dm):
            diff, o = uleb(d, o)
            midx += diff
            acc, o = uleb(d, o)
            code, o = uleb(d, o)
            out.append((midx, acc, code, 'direct'))
        midx = 0
        for _ in range(vm):
            diff, o = uleb(d, o)
            midx += diff
            acc, o = uleb(d, o)
            code, o = uleb(d, o)
            out.append((midx, acc, code, 'virtual'))
        return out
