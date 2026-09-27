#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
固化：可复现地重建最终产物 huawei_abilityshell_stub.jar（v8，实测稳定版）。

产物构成（4 个 dex，靠前者胜出）：
  classes.dex   1 类     android.util.HiLog 同签名 no-op 桩
  classes2.dex  283 类   手写桩（保留全部与固件真类重名者，见「负结果」）
  classes3.dex  2408 类  Mate40 hwEmui.jar 原版 dex 字节
  classes4.dex  2071 类  Mate40 hwframework.jar 原版 dex 字节（BuildEx 已按官方规范补齐）

相对 v4.0 的唯一实质改动：BuildEx 不再是手写桩，而是**按华为官方预装指南补齐的真类**：
  · <clinit> 里 android.os.Build.FINGERPRINTEX（华为私有字段）退化为 FINGERPRINT
    —— 否则非华为机 NoSuchFieldError，整个类初始化失败（这正是当初写桩的原因）
  · getUDID / getHarmonyUDID / getSecondaryUDID 返回确定性常量
    —— 原实现查华为私有服务 device_identifiers（本机不存在）且只 catch RemoteException，
       会以 NPE 炸掉调用方
  规范要求：static String getUDID()，返回 64 位十六进制，权限
  com.huawei.permission.sec.ACCESS_UDID（signature|privileged）。

负结果（重要）：曾尝试「删掉与固件真类重名的手写桩，让真类胜出」（v9/v10），
虽然能把 283 个不可加载类降到 257、并修好 26 个 telephony 类，
但会把应用打崩 —— 真类的方法体引用了本机不存在的华为私有类型，
类能加载、一执行就 NoClassDefFoundError（ImmersionStyle→HwWidgetFactory、
HwSmsInterceptionListenerEmui→android.telephony.SmsInterceptionListener）。
静态判据（含一跳可达性 + native + .so 检查）仍不足以事前判定，故**维持保留全部桩**。
"""

import io
import os
import shutil
import subprocess
import sys

WS = '/workspace'
MJ = os.path.join(WS, 'mjar')
BASE_SRC = os.path.join(WS, 'o2base', 'src')     # 从 v8 jar 还原的 285 个桩
OUT_O2 = os.path.join(MJ, 'o2')
EXPECT_MD5 = '44fcedd7871d6845a3b946061456af37'
EXPECT_SIZE = 2470306

# v8 中不再需要的桩：真类已按官方规范补齐
DROP_STUBS = [
    'com.huawei.android.os.BuildEx',
    'com.huawei.android.os.BuildEx$VERSION',
]


def main():
    if not os.path.isdir(BASE_SRC):
        raise SystemExit('缺少 %s' % BASE_SRC)

    if os.path.isdir(OUT_O2):
        shutil.rmtree(OUT_O2)
    os.makedirs(OUT_O2)

    n = 0
    for dp, _, fs in os.walk(BASE_SRC):
        for f in fs:
            if not f.endswith('.smali'):
                continue
            rel = os.path.relpath(os.path.join(dp, f), BASE_SRC)
            cls = rel[:-6].replace('/', '.')
            if cls in DROP_STUBS:
                continue
            dst = os.path.join(OUT_O2, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(dp, f), dst)
            n += 1
    print('  o2 桩: %d 个（已剔除 %s）' % (n, ', '.join(DROP_STUBS)))

    # 重组 jar
    p = subprocess.run(['smali', 'assemble', '-a', '34', OUT_O2, '-o',
                        os.path.join(MJ, 'classes2.dex')],
                       capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout, p.stderr)
        raise SystemExit('classes2.dex 汇编失败')

    stage = os.path.join(WS, 'jfinal')
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    os.makedirs(stage)
    for d in ('classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex'):
        shutil.copy(os.path.join(MJ, d), stage)

    jar = os.path.join(WS, 'huawei_abilityshell_stub.jar')
    if os.path.exists(jar):
        os.remove(jar)
    subprocess.run(['zip', '-q', '-X', jar] +
                   ['classes.dex', 'classes2.dex', 'classes3.dex', 'classes4.dex'],
                   cwd=stage, check=True)

    size = os.path.getsize(jar)
    md5 = subprocess.run(['md5sum', jar], capture_output=True, text=True)\
        .stdout.split()[0]
    print('  产物: %s' % jar)
    print('  大小: %d 字节（期望 %d）%s' % (size, EXPECT_SIZE,
                                       'OK' if size == EXPECT_SIZE else '不一致'))
    print('  md5 : %s（期望 %s）%s' % (md5, EXPECT_MD5,
                                     'OK' if md5 == EXPECT_MD5 else '不一致'))
    return 0 if md5 == EXPECT_MD5 else 1


if __name__ == '__main__':
    sys.exit(main())
