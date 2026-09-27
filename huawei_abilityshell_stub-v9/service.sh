#!/system/bin/sh
#
# huawei_abilityshell_stub - late_start service
#
# 补齐「华为设备上本来就有的特权」，非华为机上需要手动授予。
# 这些都是华为 ROM 给预装畅连的默认待遇，本机没有对应白名单，只能逐条 grant。
#
MODDIR=${0%/*}
LOG=/data/adb/huawei_abilityshell_stub.log
PKG=com.huawei.meetime

log() { echo "[$(date '+%m-%d %H:%M:%S')] svc: $*" >>"$LOG"; }

if [ -f "$MODDIR/disable" ] || [ -f /data/adb/skip_abilityshell_stub ]; then
    exit 0
fi

# 等系统就绪
for i in $(seq 1 60); do
    [ "$(getprop sys.boot_completed)" = "1" ] && break
    sleep 2
done
sleep 10

# 包是否还在
pm path $PKG >/dev/null 2>&1 || { log "$PKG not installed, skip"; exit 0; }

log "granting privileged permissions to $PKG"

# WRITE_SETTINGS 走 appop 才真正生效
appops set $PKG WRITE_SETTINGS allow 2>/dev/null && log "  appops WRITE_SETTINGS allow"

n=0
for perm in \
    android.permission.WRITE_SECURE_SETTINGS \
    android.permission.WRITE_SETTINGS \
    android.permission.READ_PRIVILEGED_PHONE_STATE \
    android.permission.MODIFY_PHONE_STATE \
    android.permission.CONTROL_INCALL_EXPERIENCE \
    android.permission.INTERACT_ACROSS_USERS \
    android.permission.START_ACTIVITIES_FROM_BACKGROUND \
    android.permission.DEVICE_POWER \
    android.permission.MANAGE_OWN_CALLS \
    android.permission.CALL_PHONE \
    android.permission.ANSWER_PHONE_CALLS \
    android.permission.READ_PHONE_NUMBERS \
    android.permission.READ_PHONE_STATE \
    android.permission.POST_NOTIFICATIONS \
    android.permission.SYSTEM_ALERT_WINDOW \
    android.permission.READ_CONTACTS \
    android.permission.WRITE_CONTACTS \
    android.permission.CAMERA \
    android.permission.RECORD_AUDIO \
    android.permission.ACCESS_FINE_LOCATION \
    android.permission.ACCESS_COARSE_LOCATION \
    android.permission.ACCESS_BACKGROUND_LOCATION \
    android.permission.READ_EXTERNAL_STORAGE \
    android.permission.WRITE_EXTERNAL_STORAGE \
    android.permission.READ_MEDIA_AUDIO \
    android.permission.READ_MEDIA_IMAGES \
    android.permission.READ_MEDIA_VIDEO \
    android.permission.BLUETOOTH_CONNECT \
    ; do
    if pm grant $PKG "$perm" >/dev/null 2>&1; then
        n=$((n+1))
    fi
done
log "  granted $n permissions"

# 权限状态自检
dumpsys package $PKG 2>/dev/null | grep -q "WRITE_SECURE_SETTINGS: granted=true" \
    && log "VERIFY WRITE_SECURE_SETTINGS ok" || log "VERIFY WRITE_SECURE_SETTINGS NOT set"
log "done"
