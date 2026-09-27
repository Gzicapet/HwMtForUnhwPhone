import re, os, subprocess, sys

SRC = '/workspace/hwemui_smali/android/util/HiLog.smali'
OUT = '/workspace/hi_stub_smali/android/util/HiLog.smali'
os.makedirs(os.path.dirname(OUT), exist_ok=True)

lines = open(SRC, encoding='utf-8').read().split('\n')

fields = [l for l in lines if l.startswith('.field')]
methods = [l for l in lines if l.startswith('.method')]

SIZE = {'Z': 1, 'B': 1, 'S': 1, 'C': 1, 'I': 1, 'F': 1, 'J': 2, 'D': 2}


def parse_sig(m):
    # .method <flags> name(params)ret
    m = m.strip()
    m = re.sub(r'^\s*\.method\s+', '', m)
    m = re.sub(r'\s+blacklist\s+', ' ', m)
    m = re.sub(r'\s+greylist\S*\s+', ' ', m)
    m = re.sub(r'\s+whitelist\s+', ' ', m)
    b = m.rfind(')')
    head, ret = m[:b + 1], m[b + 1:]
    return head, ret


def param_words(params, is_static):
    n = 0 if is_static else 1
    i = 0
    while i < len(params):
        c = params[i]
        if c == '[':
            while params[i] == '[':
                i += 1
            i += 1
            n += 1
            continue
        if c == 'L':
            j = params.index(';', i)
            i = j + 1
            n += 1
            continue
        n += SIZE.get(c, 1)
        i += 1
    return n


out = []
out.append('.class public final Landroid/util/HiLog;')
out.append('.super Ljava/lang/Object;')
out.append('.source "HiLog.java"')
out.append('')
out.append('# static fields')
out.extend(fields)
out.append('')
out.append('# direct methods')

generated = 0
for mline in methods:
    head, ret = parse_sig(mline)
    name_part = head[head.find('('):]
    pre = head[:head.find('(')].strip()
    name = pre.split()[-1]
    params = name_part[1:-1]
    if name == '<clinit>':
        continue
    if name == '<init>':
        out.append('.method private constructor blacklist <init>()V')
        out.append('    .registers 1')
        out.append('    invoke-direct {p0}, Ljava/lang/Object;-><init>()V')
        out.append('    return-void')
        out.append('.end method')
        out.append('')
        generated += 1
        continue
    is_static = 'static' in pre.split()
    pw = param_words(params, is_static)
    regs = pw + 1
    flags = 'public static'
    if 'varargs' in mline:
        flags += ' varargs'
    flags += ' blacklist'
    out.append('.method %s %s%s' % (flags, name, name_part + ret))
    out.append('    .registers %d' % regs)
    if ret == 'V':
        out.append('    return-void')
    else:
        out.append('    const/4 v0, 0x0')
        if ret in ('J', 'D'):
            out.append('    const/4 v1, 0x0')
            out.append('    return-wide v0')
        elif ret == 'Z' or ret == 'I' or ret in ('B', 'S', 'C'):
            out.append('    return v0')
        else:
            out.append('    return-object v0')
    out.append('.end method')
    out.append('')
    generated += 1

open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
print('  生成 %s  字段 %d  方法 %d' % (OUT, len(fields), generated))

r = subprocess.run(['smali', 'assemble', '-a', '34', '/workspace/hi_stub_smali', '-o', '/workspace/hilog_stub.dex'],
                   capture_output=True, text=True)
print('  assemble rc=%d %s' % (r.returncode, (r.stderr or r.stdout or '').strip()[:300]))
print('  dex: %d 字节' % os.path.getsize('/workspace/hilog_stub.dex'))
