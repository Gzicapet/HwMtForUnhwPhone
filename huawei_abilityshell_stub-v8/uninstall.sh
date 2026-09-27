#!/system/bin/sh
#
# huawei_abilityshell_stub - uninstall.sh
#
# 卸载时清理。注意：本模块的所有改动都是 bind 挂载，重启后自动消失，
# 所以这里的 umount 只是让「不重启也立刻复原」更彻底，非必需。

LOG=/data/adb/huawei_abilityshell_stub.log

# 解除挂载（路径可能被做过绑定，逐个尝试）
for t in \
    /system_ext/etc/permissions/audiosphere.xml \
    /system_ext/framework/audiosphere.jar
do
    [ -f "$t" ] && umount -l "$t" 2>/dev/null
done

# 只删本模块自己生成的文件，不碰用户数据
rm -f /data/adb/huawei_abilityshell_stub.log 2>/dev/null
rm -f /data/local/tmp/.stub_dp.txt /data/local/tmp/.stub_dp.txt.used 2>/dev/null

exit 0
