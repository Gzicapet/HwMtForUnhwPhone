#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桩 vs 固件真类 的取舍判据（严格版）

判据：真类在**代码**中直接引用了任何不可解析类型 → 保留桩；
      否则丢桩，让真类胜出（语义更正确）。

关键细节：
  · 必须剔除 .annotation 块 —— 注解类型缺失不影响运行时，否则会把
    大量只用 @HwSystemApi 标记的真类误判为不可用（实测会多留 20+ 个桩）
  · 必须剔除 .local 调试信息（不参与解析）
  · 只看一跳直接引用：实测传递性判据太保守（2141/4635 个类都能连到缺失类型），
    等价于不优化；而实际崩溃形态就是方法体直接引用
"""
import io, os, re, sys
from collections import defaultdict

WS='/workspace'; MJ=os.path.join(WS,'mjar')
DIRS=['o1','o2','o3','o4']
TYPE_RE=re.compile(r'L[0-9a-zA-Z_$/]+;')
ANN_RE=re.compile(r'^[ \t]*\.annotation\b.*?^[ \t]*\.end annotation', re.S|re.M)
norm=lambda d: d[1:-1].replace('/','.')

def collect(root):
    out=set()
    for dp,_,fs in os.walk(root):
        for f in fs:
            if f.endswith('.smali'):
                out.add(os.path.relpath(os.path.join(dp,f),root)[:-6].replace('/','.'))
    return out

def code_refs(path):
    txt=io.open(path,encoding='utf-8',errors='replace').read()
    txt=ANN_RE.sub('', txt)                       # 去掉注解块
    txt=re.sub(r'^[ \t]*\.local\b.*$','',txt,flags=re.M)   # 去掉调试信息
    return {norm(x) for x in TYPE_RE.findall(txt)}

bad=set()
for line in io.open(os.path.join(WS,'badres.txt'),encoding='utf-8',errors='replace'):
    if line.startswith('FAIL '): bad.add(line[5:].split(' :')[0].strip())

in_dex=defaultdict(set)
for i,d in enumerate(DIRS,1):
    root=os.path.join(MJ,d)
    if os.path.isdir(root):
        for c in collect(root): in_dex[c].add(i)

stubs=collect(os.path.join(MJ,'o2'))
keep=[]; drop=[]
for cls in sorted(stubs):
    real = 3 if 3 in in_dex.get(cls,()) else (4 if 4 in in_dex.get(cls,()) else None)
    if real is None:
        keep.append((cls,'固件无此类')); continue
    f=os.path.join(MJ,DIRS[real-1],cls.replace('.','/')+'.smali')
    hit=code_refs(f) & bad
    if hit: keep.append((cls,'真类代码引用缺失: '+', '.join(sorted(hit)[:3])))
    else:   drop.append(cls)

print('  o2 桩总数                      : %d' % len(stubs))
print('  与固件真类重名                 : %d' % len([c for c in stubs if in_dex[c] & {3,4}]))
print('  ★ 保留桩                       : %d' % len(keep))
print('     └ 固件无此类                : %d' % len([1 for _,r in keep if r=='固件无此类']))
print('     └ 真类代码引用缺失类型      : %d' % len([1 for _,r in keep if r!='固件无此类']))
print('  ★ 丢弃桩（真类代码干净）      : %d' % len(drop))
print()
print('  ── 因真类引用缺失而保留的桩 ──')
for c,r in keep:
    if r!='固件无此类': print('    %-58s %s' % (c, r))
print()
print('  ── 丢弃清单（真类胜出）──')
for c in drop: print('    %s' % c)
io.open('keep_stubs.txt','w',encoding='utf-8').write('\n'.join(c for c,_ in keep)+'\n')
io.open('drop_stubs.txt','w',encoding='utf-8').write('\n'.join(drop)+'\n')
