#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按华为官方《HMS Core Preloading Guide → Unique Device ID》规范，
把 jar 内的 BuildEx 补成合格的 OEM 实现。

规范要点：
  类     com.huawei.android.os.BuildEx
  方法   static String getUDID()
  权限   com.huawei.permission.sec.ACCESS_UDID  (signature|privileged)
  返回   64 位十六进制字符串；异常时返回空串

原状（缺陷）：
  classes2.dex 里的手写桩 BuildEx.getUDID() 返回 ""，
  且 BuildEx$VERSION 缺 EMUI_SUB_SDK_INT、无 <clinit>；
  它按 dex 顺序遮蔽了 classes4.dex 里那份固件真类（真类成死代码）。
  真类的 getUDID/getHarmonyUDID/getSecondaryUDID 会去查华为私有服务
  device_identifiers（ZTE 上不存在）→ 远端拿不到 service → NPE，
  只因只 catch 了 RemoteException。

本脚本：
  1. 删掉 classes2 的桩（BuildEx / BuildEx$VERSION），让真类接管；
  2. 把真类三个 UDID 取值方法改成直接返回同一常量（sha256 派生，重启不变）。
"""

import io
import os
import re
import sys

UDID = '64ae149753ceae0688b24bcb64664b1cb6c5c92c93f4bfd18f393dfaa4f736d1'
ROOT = '/workspace/mjar'

STUB_DIR = os.path.join(ROOT, 'o2', 'com', 'huawei', 'android', 'os')
REAL = os.path.join(ROOT, 'o4', 'com', 'huawei', 'android', 'os', 'BuildEx.smali')

METHODS = ['getUDID', 'getHarmonyUDID', 'getSecondaryUDID']


def replace_method(src, name, body):
    pat = re.compile(
        r'\.method [^\n]*\b' + name + r'\(\)Ljava/lang/String;\n.*?\n\.end method\n',
        re.S)
    new, n = pat.subn(body, src)
    if n != 1:
        raise SystemExit('  !! %s 匹配到 %d 处（期望 1）' % (name, n))
    return new


def main():
    # ---- 1. 删除遮蔽真类的桩 ----
    removed = []
    for f in ('BuildEx.smali', 'BuildEx$VERSION.smali'):
        p = os.path.join(STUB_DIR, f)
        if os.path.exists(p):
            os.remove(p)
            removed.append(f)
    # 桩目录若已空则一并清理
    if os.path.isdir(STUB_DIR) and not os.listdir(STUB_DIR):
        os.rmdir(STUB_DIR)
        removed.append('(空目录 com/huawei/android/os)')
    print('  删除桩: %s' % (', '.join(removed) if removed else '无'))

    # ---- 2. 把真类的 UDID 取值方法改为返回规范常量 ----
    src = io.open(REAL, encoding='utf-8').read()
    for m in METHODS:
        if m in src.split('.end method')[0] and False:
            pass
        body = (
            '.method public static whitelist ' + m + '()Ljava/lang/String;\n'
            '    .registers 1\n'
            '\n'
            '    # OEM 实现：返回 64 位十六进制设备唯一标识（官方预装指南要求）。\n'
            '    # 原实现查华为私有服务 device_identifiers，非华为机型上不存在，\n'
            '    # 且只 catch RemoteException，会以 NPE 形式炸掉调用方。\n'
            '    # 取值 = sha256("meetime-port:320144232091:eta")，确定性、重启不变。\n'
            '    const-string v0, "' + UDID + '"\n'
            '\n'
            '    return-object v0\n'
            '.end method\n'
        )
        src = replace_method(src, m, body)
        print('  改写真类 %s() -> 常量' % m)

    io.open(REAL, 'w', encoding='utf-8').write(src)
    print('  真类方法面: %s' % ' '.join(
        re.findall(r'\.method[^\n]*?(\w+)\(', src)))


if __name__ == '__main__':
    sys.exit(main())
