# 畅连（com.huawei.meetime）在其他品牌手机上运行 — 安装说明

让华为「畅连」在非华为设备上启动并完成注册。作者本机实测环境：**ZTE 机型 / Android 16**。

---

## 前置条件

| 项 | 要求 |
|---|---|
| Root | Magisk / KernelSU / ReSukiSU / APatch 任一（需支持模块） |
| Android | **9 及以上**（jar 内 dex 版本 039；目标应用自身 minSdk=28） |
| 畅连 APK | 需自行准备（华为官方包，`minSdk=28`） |
| LSPosed | **不需要**（早期版本曾依赖，现已证实多余） |

> 关于 Android 版本的说明：本模块不含任何系统分区写操作，也不依赖具体 ROM。
> 但 jar 里的 dex 是 039 格式，Android 9 以下无法加载。作者仅在 Android 16 上实测过；
> Android 9–15 是按 ART 的 dex 版本规则推断的兼容范围，未逐一验证。

---

## 安装

1. **装模块**：把 `huawei_abilityshell_stub-v8.zip` 刷入 Root 管理器（Magisk：模块 → 从本地安装；KernelSU/ReSukiSU：模块 → 安装）。
2. **装畅连**：安装你手上的畅连 APK（若尚未安装）。
3. **重启**：模块在 `post-fs-data` 阶段挂载，必须重启生效。

安装时 `customize.sh` 会自动探测本机「可安全顶替的共享库注册点」并打印结果。

---

## 装完怎么验证

### 1. 看挂载是否生效

```sh
# 应输出模块内 jar 的 md5
md5sum /system_ext/framework/audiosphere.jar
# 权限表里应出现我们注册的库名
grep searchmanager /system_ext/etc/permissions/audiosphere.xml
```

### 2. 看模块日志

```sh
cat /data/adb/huawei_abilityshell_stub.log
```

正常应能看到 `prechecks ok` / `mount XML ok` / `mount JAR ok` / `VERIFY ... ok`。

### 3. 看应用是否认到了这个库（最关键）

```sh
dumpsys package com.huawei.meetime | grep -A1 usesLibraryFiles
```

出现 `/system_ext/framework/audiosphere.jar` 就说明系统已把它填进应用的共享库列表，
类加载器会加载它 —— **这是本方案起作用的直接证据**。

### 4. 启动应用

从桌面图标启动（**不要**用 `am start`：畅连主 Activity 要求
`huawei.android.permission.HW_SIGNATURE_OR_SYSTEM`，命令行会被拒；
系统 Launcher 是 platform 签名所以放行）。也可用：

```sh
monkey -p com.huawei.meetime -c android.intent.category.LAUNCHER 1
```

能进到引导页/绑定手机号页即为成功。

### 5. 应用自己的日志（比 logcat 有用得多）

```sh
ls /sdcard/Android/data/com.huawei.meetime/files/mtlog/
```

成功标志：

```
{"desc":"result is success","data":{"comToken":"..."}}
HwVoipMgrCallBack: onGetComToken
CallManager: updateEcdhEncryptInfo for comtoken updated.
```

---

## 原理（为什么这样可以）

畅连的继承链：

```
com.huawei.meetime.application.HiCallApplication   (APK 内)
 └─ com.huawei.meetime.MainApplication              (APK 内)
     └─ ohos.abilityshell.HarmonyApplication        ← 华为鸿蒙运行时提供，非华为机没有
```

它声明了 `uses-library com.huawei.nb.searchmanager`。非华为机上系统不认识这个库名，
`ApplicationInfo.sharedLibraryFiles` 空着，类加载器里自然没有这些华为类。

模块做两件事，都只用 bind 挂载：

1. 顶替一个**没被任何应用使用**的 `/system_ext/etc/permissions/*.xml`，
   改为注册 `com.huawei.nb.searchmanager`，指向一个已存在的 framework jar 路径；
2. 把内含 4765 个华为类的桩 jar 挂到那个 jar 路径上。

于是 PackageManager 把该路径填进应用共享库列表 → 应用类加载器加载它 → 类可见。

**顺带一提**：`.jar` 后缀完全可以（不必是 `.apk`）。旁证：`org.apache.http.legacy.jar`
同样是 `.jar`，被微信、淘宝、Chrome 等大量应用正常使用。

---

## 排错

| 症状 | 原因 / 处理 |
|---|---|
| 启动即崩，日志 `ClassNotFoundException: HiCallApplication` | 看**末尾的 suppressed 异常**，真因是父类 `HarmonyApplication` 解析失败。说明挂载没生效 |
| `grep searchmanager /system_ext/etc/permissions/audiosphere.xml` 无输出 | 挂载失败。查 `/data/adb/huawei_abilityshell_stub.log` |
| 装完日志说 `FATAL target xml absent` | 本机没有该文件（不同 ROM 布局不同）。重装模块让 `customize.sh` 重新探测 |
| `dumpsys` 里 usesLibraryFiles 为空 | 缺 `<uses-library>` 声明或库名不匹配。确认畅连是官方原版 |
| `logcat -d` 恒为 0 行 | 本机被设过 `log.tag=S` 静默全局日志。先 `setprop log.tag V` |
| 想看应用私有目录却只看到 2 个条目 | root shell 与应用不在同一 mount namespace。用 `nsenter -t 1 -m sh -c '...'` |

---

## 卸载 / 回滚

模块**不写入任何分区真实文件**，全部是 bind 挂载。

- 正常卸载：在管理器里删掉模块 → 重启；
- 想立刻失效不重启：`touch /data/adb/skip_abilityshell_stub`（临时禁用），或
  `umount -l /system_ext/framework/audiosphere.jar`；
- 开机卡住/无限重启：按住**音量下**进 KernelSU 安全模式，删掉本模块目录。

---

## 已知限制

1. **仍需服务端实名**：应用能跑起来并拿到 comToken，但畅连要求补身份证号才能完成验证。
   这是服务端合规要求，客户端无 bug，需账号持有人提供。
2. **568 个华为私有类型无定义**（如 `android.telephony.SmsInterceptionListener`）。
   目前主路径不触及，但新代码路径可能 `NoClassDefFoundError`。
3. **构成本质是「华为固件类的搬运」**，类来自 Mate40 鸿蒙 4.3 固件，非华为官方支持场景。
