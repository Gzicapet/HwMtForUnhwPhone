#!/system/bin/sh
#
# huawei_abilityshell_stub - customize.sh（安装时执行一次）
#
# 职责：探测本机「可安全劫持的共享库注册点」，把结果写入 files/target.conf。
# 换成别的机型时不必改脚本 —— 探测是自动的。
#
# 背景（为什么能这么做）：
#   鸿蒙壳应用（畅连等）在自己的清单里声明了 uses-library
#   com.huawei.nb.searchmanager。用非华为机时系统不认识这个库，
#   ApplicationInfo.sharedLibraryFiles 不会被填充，于是类加载器里没有我们的 jar。
#   只要让系统「注册」这个库名，PackageManager 就会把对应 jar 填进
#   sharedLibraryFiles，LoadedApk 随之把它加入应用类加载器 —— 无需 Xposed。
#   （实测 .jar 后缀完全可用，旁证：org.apache.http.legacy.jar 被微信等大量应用使用。）
#
#   而注册库名需要一个 /system_ext/etc/permissions/*.xml。我们无法新增文件，
#   只能 bind 顶替一个已存在的 —— 所以必须挑一个「顶掉也没人受影响」的。
#
# 安全判据：
#   目标 XML 声明了库 L → 文件 F。若全系统没有任何应用把 F 列进 usesLibraryFiles
#   （排除目标应用自身），则顶替 F 不会破坏任何应用。
#   Linux/Android 上 shared-library 是唯一引用 F 的途径，所以这个判据是充分的。

SKIPUNZIP=0

BB=/data/adb/magisk/busybox
[ -x "$BB" ] || BB=busybox
ow() { "$BB" "$@" 2>/dev/null; }

ui() { echo "  [abilityshell] $*"; }

CONF="$MODPATH/files/target.conf"
LIBNAME=com.huawei.nb.searchmanager
TGT_PKG=${TGT_PKG:-com.huawei.meetime}
DP=/data/local/tmp/.stub_dp.txt

ui "探测共享库注册点…"

API=$(getprop ro.build.version.sdk)
[ -z "$API" ] && API=0
ui "Android API $API / $(getprop ro.product.cpu.abi)"

# 已知「沿用旧版」的默认候选，按优先级排列。
# audiosphere 在 AOSP/QTI 的 system_ext 里是标准文件，命中率最高。
PREF="audiosphere.xml datachannellib.xml dpmapi.xml qti_libpermissions.xml"

# ── 1) 收集「已被真实使用的库文件」，排除目标应用自身 ──
#     dumpsys package 的分段结构：  Package [xxx] (…):  …  usesLibraryFiles: <换行> /path
dumpsys package >"$DP" 2>/dev/null
if [ -s "$DP" ]; then
    "$BB" awk -v self="$TGT_PKG" '
        /^  Package \[/ { pkg = $2; gsub(/[^A-Za-z0-9._]/, "", pkg) }
        /usesLibraryFiles:/ {
            if ((getline nxt) > 0) {
                sub(/^[ \t]+/, "", nxt)
                if (nxt ~ /^\// && pkg != self) print nxt
            }
        }
    ' "$DP" | sort -u >"$DP.used"
    ui "已被占用的库文件: $(wc -l <"$DP.used" 2>/dev/null | tr -d ' ') 个"
else
    : >"$DP.used"
    ui "警告：dumpsys 不可用，跳过占用检查（将退回默认候选）"
fi

# ── 2) 遍历候选 XML ──
pick_xml=''
pick_jar=''
pick_name=''

scan_dir() {
    dir="$1"
    [ -d "$dir" ] || return 0
    # 先按偏好顺序试，再扫其余
    for base in $PREF; do
        [ -f "$dir/$base" ] && try_one "$dir/$base" && return 0
    done
    for f in "$dir"/*.xml; do
        [ -f "$f" ] || continue
        case " $PREF " in *" $(basename "$f") "*) continue ;; esac
        try_one "$f" && return 0
    done
    return 1
}

try_one() {
    f="$1"
    # 缺陷1修复：只接受**单 library** 的 XML。
    #   我们替换后其余库声明都会消失，多库文件（如 vendor.qti.ims.rcsservice.xml
    #   有 14 个库）绝不能动。
    [ "$(grep -c '<library' "$f" 2>/dev/null)" = "1" ] || return 1
    # 缺陷2修复：属性可能跨行（我们自己的生成格式就是跨行的），先压成一行再抓标签。
    tag=$(tr '\n' ' ' <"$f" 2>/dev/null | grep -o '<library[^>]*>' | head -1)
    [ -n "$tag" ] || return 1
    nm=$(echo "$tag" | sed -n 's/.*name="\([^"]*\)".*/\1/p')
    fl=$(echo "$tag" | sed -n 's/.*file="\([^"]*\)".*/\1/p')
    [ -n "$fl" ] || return 1
    # 源文件必须真实存在（bind 需要目标存在）
    [ -f "$fl" ] || return 1
    # 不能已被任何别的应用使用
    if grep -qxF "$fl" "$DP.used" 2>/dev/null; then
        return 1
    fi
    pick_xml="$f"; pick_jar="$fl"; pick_name="$nm"
    return 0
}

scan_dir /system_ext/etc/permissions || scan_dir /system/etc/permissions

# ── 3) 兜底：偏好候选里第一个存在的（即使占用检查没跑成）──
if [ -z "$pick_xml" ]; then
    for d in /system_ext/etc/permissions /system/etc/permissions; do
        if [ -f "$d/audiosphere.xml" ] && [ -f /system_ext/framework/audiosphere.jar ]; then
            pick_xml="$d/audiosphere.xml"
            pick_jar=/system_ext/framework/audiosphere.jar
            pick_name=com.qualcomm.qti.audiosphere
            ui "警告：未找到空闲注册点，退回 audiosphere（可能影响引用它的应用）"
            break
        fi
    done
fi

# ── 4) 落盘 ──
if [ -n "$pick_xml" ]; then
    {
        echo "# 由 customize.sh 自动探测生成 $(date '+%Y-%m-%d %H:%M:%S')"
        echo "# 顶替的注册点（原库名：$pick_name）"
        echo "TGT_XML=$pick_xml"
        echo "TGT_JAR=$pick_jar"
        echo "LIBNAME=$LIBNAME"
    } >"$CONF"
    ui "选定注册点: $pick_xml"
    ui "     原库名: $pick_name"
    ui "     挂载 jar: $pick_jar"
else
    ui "错误：本机找不到可用的共享库注册点，模块将不会生效。"
    ui "     请把上面输出反馈给作者。"
    # 仍写一份默认值，便于手工改
    {
        echo "TGT_XML=/system_ext/etc/permissions/audiosphere.xml"
        echo "TGT_JAR=/system_ext/framework/audiosphere.jar"
        echo "LIBNAME=$LIBNAME"
    } >"$CONF"
fi

# ── 5) 运行时依赖自检 ──
JAR="$MODPATH/files/huawei_abilityshell_stub.jar"
if [ -f "$JAR" ]; then
    ui "桩包: $(wc -c <"$JAR" | tr -d ' ') 字节, $(grep -oa 'classes[0-9]*\.dex' "$JAR" | sort -u | wc -l | tr -d ' ') 个 dex"
else
    ui "错误：files/huawei_abilityshell_stub.jar 缺失"
fi

if command -v pm >/dev/null 2>&1; then
    if pm path "$TGT_PKG" >/dev/null 2>&1; then
        ui "目标应用 $TGT_PKG 已安装 ✓"
    else
        ui "提示：目标应用 $TGT_PKG 尚未安装，请先安装畅连 APK"
    fi
fi

ui "安装完成，重启后生效。"
