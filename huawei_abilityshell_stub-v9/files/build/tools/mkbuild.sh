#!/bin/sh
# 从 mjar/o2（桩源码，现役）重建 jar。用法: sh mkbuild.sh
set -e
cd /workspace
smali assemble -a 29 mjar/o2 -o mjar/classes2.dex
rm -rf mk
mkdir mk
cp mjar/classes.dex mjar/classes2.dex mjar/classes3.dex mjar/classes4.dex mk/
cd mk
rm -f /workspace/out_stub.jar
zip -q -X /workspace/out_stub.jar classes.dex classes2.dex classes3.dex classes4.dex
echo "jar: $(ls -l /workspace/out_stub.jar | awk '{print $5}') 字节  md5: $(md5sum /workspace/out_stub.jar | cut -d' ' -f1)"
echo "classes2 类数: $(python3 -c "
import sys; sys.path.insert(0,'/workspace/tools')
from dexparse import Dex
print(len(Dex('/workspace/mjar/classes2.dex').build()[0]))")"
