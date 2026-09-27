#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建 huawei_abilityshell_stub.jar（v10）—— 最终版

规则
----
jar 内 4 个 dex，类按顺序解析、先定义者胜出：
  classes.dex  →  classes2.dex  →  classes3.dex  →  classes4.dex
因此 classes2 里与固件真类重名的手写桩会**静默压制真类**。

v9 的教训：只看「类能否 Class.forName 成功」不够。
com.huawei.android.immersion.ImmersionStyle 加载成功，但方法体引用
android.hwcontrol.HwWidgetFactory（非华为机不存在），一执行就 NoClassDefFoundError
把应用打崩。所以判据必须看真类的**代码**引用了什么。

最终判据（judge_shadow.py 产出 keep_stubs.txt / drop_stubs.txt）：
  · 真类代码直接引用不可解析类型        → 保留桩
  · 真类声明 native 方法                → 保留桩（首次调用才会炸，校验台抓不到）
  · 真类依赖华为私有 .so                → 保留桩
  · 其余                               → 丢桩，让真类胜出（语义更正确）
  · 固件里根本没有的类                  → 保留桩（必须）

结果：285 个桩 → 保留 206（156 固件无此类 + 50 有风险）、丢弃 79。
实测不可加载类由 283 降到 …（见 README 验证记录），应用引用的类型中不可加载类为 0。
"""

import io
import os
import shutil
import sys

WS = '/workspace'
BASE_SRC = os.path.join(WS, 'o2base', 'src')      # 从 audiosphere_v8.jar 还原的 285 个桩
KEEP = os.path.join(WS, 'keep_stubs.txt')
OUT = os.path.join(WS, 'mjar', 'o2')


def main():
    if not os.path.isdir(BASE_SRC):
        raise SystemExit('缺少 %s' % BASE_SRC)
    keep = {l.strip() for l in io.open(KEEP, encoding='utf-8') if l.strip()}
    print('  keep 清单: %d 个' % len(keep))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    n = 0
    for cls in sorted(keep):
        src = os.path.join(BASE_SRC, cls.replace('.', '/') + '.smali')
        if not os.path.exists(src):
            print('  ! 缺源文件: %s' % cls)
            continue
        dst = os.path.join(OUT, cls.replace('.', '/') + '.smali')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
        n += 1
    print('  已写出 %d 个桩到 %s' % (n, OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
