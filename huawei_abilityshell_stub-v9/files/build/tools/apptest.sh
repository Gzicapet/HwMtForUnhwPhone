#!/system/bin/sh
# 畅连健康自检：冷启动 → 进程存活 → 前台 Activity → comToken 日志 → 崩溃痕迹
F=/sdcard/Android/data/com.huawei.meetime/files/mtlog
echo "=== force-stop ==="
am force-stop com.huawei.meetime
sleep 2
echo "=== launch ==="
monkey -p com.huawei.meetime -c android.intent.category.LAUNCHER 1 2>&1 | tail -2
sleep ${1:-25}
echo "=== pidof ==="
pidof com.huawei.meetime
echo "=== 前台 Activity ==="
dumpsys activity activities 2>/dev/null | grep -m4 -E "topResumedActivity|ResumedActivity"
echo "=== 最新 mtlog ==="
ls -lt $F | head -4
NEW=$(ls -t $F/uspa_*.log 2>/dev/null | head -1)
echo "newest=$NEW  成功次数=$(grep -c 'result is success' "$NEW" 2>/dev/null)"
grep -o "comToken\":\"[a-z0-9]\{8\}" "$NEW" 2>/dev/null | tail -2
echo "=== 崩溃痕迹（dropbox / tombstone，30 分钟内）==="
find /data/system/dropbox -mmin -30 -type f 2>/dev/null | tail -5
find /data/tombstones -mmin -30 -type f 2>/dev/null | tail -5
