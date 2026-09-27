# huawei_abilityshell_stub

为**鸿蒙壳 APK**（畅连 `com.huawei.meetime`）补齐非华为机型缺失的华为框架类。

当前版本：**v9** ｜ 模块 id `huawei_abilityshell_stub`
面向分发的安装说明见 **[INSTALL.md](INSTALL.md)**。

---

## 一、要解决的问题

畅连的继承链：

```
com.huawei.meetime.application.HiCallApplication   (APK 内)
 └─ com.huawei.meetime.MainApplication              (APK 内)
     └─ ohos.abilityshell.HarmonyApplication        ← 华为鸿蒙运行时提供，本机没有
```

非华为机上启动即崩。崩溃日志显示 `ClassNotFoundException: HiCallApplication`，
但**真正的断点是父类解析失败** —— `BaseDexClassLoader` 把子异常作为 suppressed
附在末尾，极易误判成「dex 没加载」。排查时务必看 suppressed 链。

## 二、注入机制（已实测确认）

畅连清单声明了 `uses-library com.huawei.nb.searchmanager`。非华为机上系统不认识这个库名，
`ApplicationInfo.sharedLibraryFiles` 是空的，类加载器里自然没有我们的类。

只要让系统**注册**这个库名，PackageManager 就会把它填进 `sharedLibraryFiles`，
`LoadedApk` 随之把该路径加入应用类加载器。模块做两件事，全程只用 bind 挂载：

| 模块内文件 | bind 覆盖到 | 说明 |
|---|---|---|
| `files/target.conf` 指定的 XML | 该 XML 原路径 | 内容改为注册 `com.huawei.nb.searchmanager` |
| `files/huawei_abilityshell_stub.jar` | `target.conf` 指定的 jar 路径 | 桩 jar 本体 |

`target.conf` 由 **`customize.sh` 在安装时自动探测生成**，不写死机型：

- 判据：目标 XML 声明的库 → 文件 F。若全系统没有任何应用把 F 列进
  `usesLibraryFiles`（排除目标应用自身），则顶替 F 不破坏任何应用。
- Linux/Android 上 shared-library 是引用 F 的唯一途径，所以该判据是充分的。
- 本机选中 `audiosphere.xml` / `audiosphere.jar`（QTI 在 AOSP `system_ext` 里的标准文件），
  被顶掉的库名 `com.qualcomm.qti.audiosphere` 全机 0 个应用引用。

### 关键事实：**不需要 LSPosed / Xposed**

早期版本曾依赖一个 LSPosed 模块做 `appendDex`，后来的实验证明那是多余的：

**判定实验**（`pm disable-user` 停用 LSPosed 模块后启动应用）：

| 证据 | 结果 |
|---|---|
| hook 探针文件时间戳 | 停在旧时刻 → hook 未执行 |
| 应用进程 `/proc/<pid>/maps` | **mmap 了 `/system_ext/framework/audiosphere.jar`**（dex 段） |
| 应用日志 | `comToken × 3`、`result is success` |
| 崩溃 | 0 |

即：**Magisk 模块单独就完整可用**。

同时也纠正了另一条早期错误结论 —— 「`LoadedApk.makePaths` 只接受 `.apk` 结尾的共享库」。
反证：`org.apache.http.legacy.jar` 同样是 `.jar`，被微信、淘宝、Chrome 等大量应用正常使用。
`.jar` 完全可用。

### 自动探测本身踩过的三个坑

自动探测是让模块能用在别的机型上的关键，但它自己也踩了坑（均已在 v8 分发型修掉）：

1. **包名提取带方括号**
   `dumpsys package` 的包名行长这样：`Package [com.foo] (hash):`，`$2` 是 `[com.foo]`。
   `gsub(/[\[\]]/, "", pkg)` 在本机 **busybox awk 上不生效**（字符类里的转义处理与
   GNU awk 不同），于是 `pkg != "com.huawei.meetime"` 恒为真 —— 目标应用自身的引用
   没被排除 → `audiosphere.jar` 被误判成「已被占用」，探测跳去顶替别的注册点。
   改法：`gsub(/[^A-Za-z0-9._]/, "", pkg)`，用包名字符集白名单，天然吃掉方括号。

2. **属性跨行就解析不到**
   有些 XML 把 `name=` 和 `file=` 写在两行（我们自己的生成格式正是如此）。
   只按单行做 sed 会拿到空的 `file` → 误判不可用。
   改法：先 `tr '\n' ' '` 压成一行，再 `grep -o '<library[^>]*>' | head -1` 取标签。

3. **多库 XML 绝对不能动**
   `vendor.qti.ims.rcsservice.xml` 一个文件声明了 **14 个**库，替换后另外 13 个会一起消失。
   改法：只接受 `grep -c '<library' == 1` 的文件。

另外一条环境坑：**`/data/adb` 在 Linux 工具环境里访问会挂起**（不是简单报错），
改模块文件必须走 Android 侧 shell，否则命令会静默超时。

### 目标必须选 `/system_ext`

`mountify` 会对 `/system/etc` 做 overlayfs，且其挂载发生在 `service.sh`(late_start)，
会遮蔽 `post-fs-data` 阶段的 bind；而 PackageManager 只在启动时读一次权限 XML，
晚挂载等于无效。`/system_ext` 不在 mountify overlay 范围内。

---

## 三、jar 构成与两条必须记住的规则

jar 内有 4 个 dex（**共 4765 个类**），全部为 **dex 版本 039（Android 9+ 可加载）**：

| 条目 | 类数 | 内容 |
|---|---|---|
| `classes.dex` | 1 | `android.util.HiLog` 同签名 no-op 桩 |
| `classes2.dex` | 285 | 手写桩（`ohos/abilityshell` 骨架 + 缺失的华为类） |
| `classes3.dex` | 2408 | Mate40 鸿蒙 4.3 固件 `hwEmui.jar` **原版 dex 字节** |
| `classes4.dex` | 2071 | 固件 `hwframework.jar` 的 smali 重汇编产物（BuildEx 已按官方规范补齐） |

### 规则一：类按 dex 顺序解析，先定义者胜出

`classes.dex → classes2.dex → classes3.dex → classes4.dex`。
**放在前面的手写桩会静默压制后面的固件真类**，真类沦为死代码。
`classes2` 的 285 个桩里 **129 个**与 `classes3/classes4` 的真类重名。

两个已修的实际危害：

- ✅ **`BuildEx`**：桩的 `getUDID()` 返回 `""` → 拿不到 comToken
- ✅ **`NoExtAPIException`**：桩 `extends Object`，真类 `extends RuntimeException`
  → 固件真类 `MSimTelephonyManager` 被 ART 以
  `NoExtAPIException not instanceof Throwable` **整体 VerifyError 拒绝**

### 规则二：绝不重汇编华为真类再合并成一个 dex

**不能**用 smali 把真实华为类重新汇编、再合并成单个 dex —— ART 会拒绝加载
（`Direct/virtual method N ... not in expected list`）。
必须保留**原版 dex 字节**，以 jar 内多 dex 条目的形式组织。

---

## 四、v8 的实质改动：BuildEx 补成符合官方规范的实现

### 为什么这是「官方扩展点」

华为《HMS Core (APK) Preloading Guide → Unique Device ID》是写给**第三方 OEM** 的，
明确要求 OEM 在框架里实现：

| 项 | 值 |
|---|---|
| 类 | `com.huawei.android.os.BuildEx` |
| 方法 | `String getUDID()`（static） |
| 权限 | `com.huawei.permission.sec.ACCESS_UDID`（signature\|privileged） |
| 返回 | 64 位十六进制字符串，异常时返回空串 |

即「非华为设备上跑 HMS」是官方支持场景。

### 固件真类的两个硬伤

```java
static { EMUI_SDK_INT = SystemProperties.getInt("ro.build.hw_emui_api_level", 0); }

public static String getUDID() {
    IBinder b = ServiceManager.getService("device_identifiers");   // ← 本机无此服务
    IDeviceIdentifiersPolicyService s = IDeviceIdentifiersPolicyService$Stub.asInterface(b);
    return s.getUDID();                                            // ← b 为 null → NPE
}
```

1. `<clinit>` 读 `android.os.Build.FINGERPRINTEX` —— 华为在 framework 里加的**私有字段**，
   非华为 ROM 没有 → `NoSuchFieldError`，**整个类初始化失败**。
   （这正是当初写手写桩的原因，桩因此遮蔽了真类。）
2. `getUDID` 查华为私有服务 `device_identifiers`，本机不存在；且方法**只 catch
   `RemoteException`**，`getService` 返回 null 导致的 NPE 直接炸掉调用方。

### v8 的做法（`files/build/tools/opt_buildex.py`）

- `FINGERPRINTEX` → 退化为 AOSP 的 `FINGERPRINT`（语义等价）
- `getUDID` / `getHarmonyUDID` / `getSecondaryUDID` → 返回确定性常量
  （`sha256("meetime-port:320144232091:eta")`，重启不变）
- 同时删掉 `classes2` 里遮蔽它的手写桩，让真类接管

校验台输出：

```
getUDID          = 64ae149753ceae0688b24bcb64664b1cb6c5c92c93f4bfd18f393dfaa4f736d1
getHarmonyUDID   = 同值
getSecondaryUDID = 同值
EMUI_SDK_INT = 0    EMUI_SUB_SDK_INT = 22    HARMONY_4_3 = 35
```

---

## 五、负结果：不要试图删掉与真类重名的手写桩

**结论：这条路已试过，失败，因此 v8 保留全部 285 个桩。**

| 版本 | 策略 | 校验台结果 | 应用实测 |
|---|---|---|---|
| v9 | 删 125 个重名桩 | 不可加载类 **283 → 257**，净修好 26 个 | **崩溃**：`ImmersionStyle` → `NoClassDefFoundError: android.hwcontrol.HwWidgetFactory` |
| v10 | 收紧判据后删 79 个 | 定义集不变 | **崩溃**：`HwSmsInterceptionListenerEmui` → `android.telephony.SmsInterceptionListener` |

### 根因：可加载 ≠ 可用

`ImmersionStyle` **能** `Class.forName` 成功，所以「类加载校验台」抓不到它；
但它的**方法体**引用了 `android.hwcontrol.HwWidgetFactory`（华为私有的 `android.*` 包），
一执行就 `NoClassDefFoundError`。ART 的校验允许「软失败」类型引用延迟到首次执行才解析，
因此**类级可加载性完全不足以判定桩能不能删**。

### 已建立但仍不充分的判据（`files/build/tools/judge_shadow.py`）

对每个重名类，看其真类**代码**直接引用了什么（需剔除 `.annotation` 块 —— 注解类型缺失不影响
运行时，否则多留 20+ 个桩；也不能用传递闭包 —— 实测 2141/4635 个类都能连到缺失类型）：

- 真类代码直接引用不可解析类型 → 留桩
- 真类声明 `native` 方法 → 留桩（首次调用才炸）
- 真类依赖华为私有 `.so` → 留桩

判据覆盖了 `ImmersionStyle`、`AudioManagerEx` 等 50 个类，**但 v10 仍崩在判据之外**：
缺失类型是**应用自己的类**（`HwSmsInterceptionListenerEmui`）引入的，而非固件真类。
静态判据无法覆盖「应用调用链 + 真类行为变化」的组合。

**判定标准的真实下限**是：改动后必须真机启动应用并跑过关键路径。
收益（26 个类）小于风险（应用崩溃），故维持现状。

---

## 六、桩 jar 的多层缺陷（写手写桩的踩坑史）

早期「桩装上了却完全没作用」，逐层剥出 6 类独立缺陷。这些坑对任何
「手写 smali 桩」的场景都成立：

1. **`<init>` 必须带 `constructor` 关键字**
   写成 `.method public <init>()V` 会被编进 `virtual_methods`，而 DEX 规定
   `<init>` 必须在 `direct_methods` → ART 的 `DexFile::Verify()` **整体拒绝该 dex**，
   症状是「所有类都不存在」（最隐蔽，208 个类受影响）。
2. **返回指令必须匹配返回类型**
   对象用 `return-object`、long/double 用 `return-wide`。一律发 `return` 会在运行时
   `VerifyError`（273 处）。
3. **static / 实例属性必须与调用方一致**
   判据只能来自应用 dex 里真实的 `invoke-*` 类型（`dexdump -d`，注意分隔符是 `.` 和 `:`，
   **不是 `->`**）。共纠正 216 个方法。
4. **返回 String 必须返回非 null**
   应用会对返回值调 `.isEmpty()` → 直接 NPE。64 个方法返回 `""`，4 个 static String 字段初始化 `""`。
5. **父类不能猜**
   10 个 `*Ex` 包装类被误判继承 `final` 类或接口 → 类加载即失败
   （`ConfigurationEx`/`CountryListenerEx`/`PowerManagerEx`/`ServiceManagerEx`/
   `UserHandleEx`/`StorageVolumeEx`/`SettingsEx`/`DisconnectCauseEx`/`WindowManagerEx`/
   `InputMethodManagerEx`）。这些本就是静态工具包装类，一律 `.super Ljava/lang/Object;`。
6. **static 工厂方法必须返回实例**
   返回 null 会让调用方在 `invoke` 时以「null receiver」NPE 崩掉，堆栈只显示
   `java.lang.reflect.Method.invoke`，看不出是哪一类。
   23 个（`getInstance`/`getDefault`/`create` 等）已改为 `new-instance`。

**额外一条（与第五节同源）**：`NoExtAPIException` 这类异常桩必须
`extends RuntimeException/Exception`，否则任何在方法体里 `throw` 它的固件真类
都会被 ART 整体拒绝。

---

## 七、验证工具链

改动**必须**过校验台，不能靠「应用不崩」当唯一判据。

### 1. ART 静态校验（快速排除）

```bash
D=/apex/com.android.art/bin/dex2oat
$D --dex-file=<jar|dex> --oat-file=/data/local/tmp/t.oat \
   --instruction-set=arm64 --compiler-filter=verify
echo "exit=$?"   # 0 = ART 接受；非 0 = dex 被整体拒绝
```

> **通过 ≠ 运行时通过**：`--compiler-filter=verify` 比运行时宽松，
> 第六节第 2 类缺陷就是它放过、运行时才拒绝的。

### 2. 定点校验台 `tools/V8.smali`

只依赖 jar 自身（不加载 Xposed），反射打印 `BuildEx` 关键面：

```bash
CLASSPATH=/data/local/tmp/fuck_andes/v8.jar:/data/local/tmp/fuck_andes/<目标>.jar \
  app_process /system/bin com.x.V8
```

### 3. 全量枚举台 `tools/All.smali`

逐行读类名清单、逐个 `Class.forName`，一次枚举出**全部**不可加载类：

```bash
CLASSPATH=<校验台>:<目标 jar> app_process /system/bin com.x.All
```

- 输入 = jar 的 **class 表** → 测「jar 内定义的类能不能加载」（v8：283/4635 失败）
- 输入 = jar 的 **type 表** → 测「jar 引用的类型能不能解析」（2042 个外部引用 → 568 个不可解析）

注意：`baksmali list classes` 列的是**定义**，`baksmali list types` 才是**引用**，不能混用。
`list classes` 输出的是**类型描述符**（`Lcom/foo/Bar;`），要剥掉首 `L`、尾 `;`、`/`→`.`。

### 4. 应用侧实测（唯一的下限判据）

```bash
/sdcard/Android/data/com.huawei.meetime/files/mtlog/
    uspa_*.log        CaasKit 原生层，含 comToken 的 REST 结果
    hidscalog/        注册流程
```

成功标志：

```
{"desc":"result is success","data":{"comToken":"..."}}
HwVoipMgrCallBack: onGetComToken
CallManager: updateEcdhEncryptInfo for comtoken updated.
```

---

## 八、排查要点（血泪）

1. **`log.tag=S` 会静默全局日志**，`logcat -d` 恒为 0 行。先 `setprop log.tag V`。
2. **`am start` 启动畅连会被拒**（主 Activity 要求
   `huawei.android.permission.HW_SIGNATURE_OR_SYSTEM`），只能用桌面图标或
   `monkey -p com.huawei.meetime -c android.intent.category.LAUNCHER 1`。
3. **root shell 与 init 不在同一 mount namespace**
   （`mnt:[4026535370]` vs `mnt:[4026532585]`）。后果：
   - 在 shell 里重跑 `post-fs-data.sh` **不影响应用所见**；
   - **但原位覆盖模块文件（同 inode）会立即透过 bind 生效**，无需重启 ——
     这让迭代从「每次重启」变成「秒级」；
   - 判断应用实际看到的内容：读 `/proc/1/root/system_ext/framework/audiosphere.jar`。
4. **应用私有数据目录在 root shell 的命名空间里被隐藏**（`/data/data` 只剩 2 个条目）。
   用 init 的视角看：`nsenter -t 1 -m sh -c 'ls -la /data/user/0/com.huawei.meetime'`。
5. **`/workspace`（Linux 工具环境）与 Android 的 `/data/local/tmp/fuck_andes` 是同一目录**，
   两边路径混用是常见低级错误。
6. 应用崩溃会弹 `com.fankes.apperrorstracking`（AppErrorsTracking）对话框，
   点「错误详情」可看到异常类型/抛出类/方法/堆栈，比 logcat 更快。
7. **`dumpsys package` 的输出里夹杂全局 shared-library 注册表**，
   直接 `grep <库名>` 会误判成「某应用引用了它」。要判断某应用真正声明了什么，
   必须看它自己那段的 `usesLibraryFiles:`（值在标签**下一行**）。

---

## 九、构建与固化

```
files/build/
├── hwframework_orig.dex              Mate40 hwframework 原始 dex（classes4 的源）
├── hilog_stub.dex                    classes.dex 的源（HiLog no-op，1884B）
├── HiLog.smali / gen_hilog_stub.py   HiLog 桩源码与生成器
├── patch_udid.py / patch_network.py / patch_phoneaccount.py
├── hook/                             ★历史遗留：早期 LSPosed 模块源码，现已非必需
│   └── Hook.smali  Hook$6.smali  Hook$7.smali
└── tools/
    ├── opt_buildex.py     按官方规范补齐 BuildEx（v8 核心改动）
    ├── build_final.py     可复现重建 jar
    ├── judge_shadow.py    桩/真类取舍判据（见第五节）
    ├── build_v10.py       去遮蔽实验的构建脚本
    ├── analyze_shadow.py  影子类与可达性分析
    └── V8.smali All.smali 校验台源码
```

### 运行时依赖只有一个文件

`files/huawei_abilityshell_stub.jar`（2470335 字节，
md5 `c83765a83cdc79a79a1e1830604c376c`）。
`post-fs-data.sh` 内置该指纹自检，不一致只告警不阻断，便于自行重建。

### 重新构建（含降 dex 版本）

```bash
# 汇编桩与真类：-a 29 产出 dex 039（Android 9+ 通用）
smali assemble -a 29 mjar/o2 -o mjar/classes2.dex     # 285 桩
smali assemble -a 29 mjar/o4 -o mjar/classes4.dex     # 2071 真类（含 BuildEx 补丁）
smali assemble -a 29 hilogsm -o mjar/classes.dex      # 1 类 HiLog
# classes3.dex 为固件原版字节，已是 039，直接沿用
cd jfinal && zip -q -X /workspace/huawei_abilityshell_stub.jar \
    classes.dex classes2.dex classes3.dex classes4.dex
```

> `-a` 决定 dex 版本：API 24–27→037，28→038，29–30→039，31+→040。
> 高版本 ART 能加载低版本 dex，反之不行 —— 所以取 29 可覆盖 Android 9 及以上。

### 可复现性说明（诚实记录）

`tools/build_final.py` 能从 `mjar/o2` + `classes3/classes4` 重建出**类集与语义完全一致**
的 jar（校验台输出逐项相同）。但**字节不保证一致**：`sources` 中间经过 `baksmali` 反汇编 →
重新汇编的往返，dex 内部布局（字符串顺序/调试信息）会有差异。要字节级复现，
必须保留原始的 smali 树，而不是往返产物。

---

## 十、回滚

全部改动都是 **bind 挂载**，不写入任何分区真实文件。

- 删除模块目录，或创建 `/data/adb/skip_abilityshell_stub`，重启即完全复原；
- 立刻失效不重启：`umount -l /system_ext/framework/audiosphere.jar`；
- 无限重启时：开机按住**音量下**进入 KernelSU 安全模式，删掉本模块。

日志：`/data/adb/huawei_abilityshell_stub.log`

---

## 十一、当前进度

应用已能：实例化 `HiCallApplication` → 跑完 `Application.onCreate` → 启动后台服务 →
打开数据库 → 进入前台 → CaasKit 原生层初始化（`CallManager` / `MediaManager` /
`RtkEngine` / `RtcEngine`）→ 拿到 comToken → 推进到绑定手机号页。

### 剩余阻塞

服务端**实名合规**：畅连要求补身份证号才能提交验证（客户端无 bug）。
华为账号预填了姓名，身份证号必须由账号持有人提供。
另有一处 `getOwnDevices` 的 `accountId` 为空，可能是实名之后的下一关。

### 已知未处理

- `android.telephony.SmsInterceptionListener` 等 568 个华为私有类型在 jar 里无定义。
  目前不影响主路径，但任何触及这些类型的新代码路径都会 `NoClassDefFoundError`。
  补桩需要先确认调用方是否真的会执行到。
- `classes2` 的 129 个重名桩仍压制固件真类（第五节已论证：暂不动）。

---

## 十二、v9：运行时缺方法收敛（2026-09-27）

### 起因：v8 遗留的「29 个类有应用会调用但桩没有的方法」是**判据错了**

v8 的清单来自 `tools/dex_refs.py`，它拿「应用 dex 的 method_ids」减去「**桩文件自身**声明的方法」。
但 ART 的 `invoke-*` 解析是**沿运行时类的父类链**查的（ArtMethod::ResolveMethod），
桩文件里没有 ≠ 解析不到。典型例子：

| 类 | 表面「缺」 | 实际 |
|---|---|---|
| `huawei.android.widget.EditText` | 34 个 | 桩 `.super Landroid/widget/EditText;` → `setHint/setText/setFilters…` 全在 `TextView` 链上，**0 风险** |
| `huawei.android.widget.ListView` | 12 个 | 同上（父类 `android.widget.ListView`） |
| `com.huawei.android.app.ActivityManagerEx` | 1 个 | 真类/父类链可解析 |

判据必须按**运行时胜出定义**走：`classes2.dex`(桩) 先于 `classes3/4.dex`(固件真类)，
同名真类被遮蔽、**不进父类链**，所以不能拿真类的方法来「兜底」。
`tools/gapanalyze.py` 按 `stub → fw3 → fw4 → framework/core → java.lang.Object`
取该名字的**定义者**再沿 `.super` 上溯，结论：

```
全部 99 个「缺失」中，可解析 92，真缺陷 7（分属 6 个类）
```

### 7 个真缺陷与 v9 的处理

| 类 | 缺失方法 | 处理 | 依据 |
|---|---|---|---|
| `com.huawei.android.os.ServiceManagerEx` | `getService` / `checkService`(static) | **删桩** | 真类 4 方法，`linkcheck` 0 缺失类型 / 0 解析不到的方法 |
| `com.huawei.android.telephony.DisconnectCauseEx` | `toString(I)`(static) | **删桩** | 真类 2 方法 + 19 常量，0 缺失 |
| `com.huawei.android.telephony.PhoneStateListenerEx` | `<init>(I)V` | **删桩** | 真类 16 方法（`PhoneStateListener.<init>(Integer)` 在本机存在），0 缺失 |
| `com.huawei.android.location.CountryDetectorEx` | `<init>(Context)V` | **重写桩** | 该名字**无固件真类**；且原桩 `.super Landroid/location/CountryDetector;` 在 Android 16 **已被删除** → 类根本加载不了（唯一的父类链断裂桩）。改为 `.super Ljava/lang/Object;` + 保存 Context 的空实现 |
| `com.huawei.android.view.inputmethod.InputMethodManagerEx` | `getInstance()`(static) | **补转发** | 真类存在但方法体引用 `com.huawei.android.inputmethod.HwInputMethodManager` 等 3 个本机没有的私有类型 → 不能删桩；改补 `invoke-static Landroid/view/inputmethod/InputMethodManager;->getInstance()` |
| `com.huawei.android.content.res.ConfigurationEx` | `<init>(Configuration)V` | **补构造** | 无真类。调用点 `ConfigurationEmui.isSimpleModeOn()` 会传 `null`（`ActivityManagerEx.getConfiguration()` 返回 null），构造里**不能解引用参数**；`getSimpleuiMode()` 返回 0 → 判定「非简易模式」，`getExtraConfigTheme()` 返回 0 → themeId=0 |

结果：**真缺陷 7 → 0**，jar 由 2470295 B（285 桩）变为 2470241 B（282 桩），
md5 `0c292d83f9d2a0411a5a279819d718f2`。

### 删桩前必须过的判据（新增 `tools/linkcheck.py`）

v9/v10 删桩崩在「真类能加载、一执行 NoClassDefFoundError」。
`linkcheck.py` 补上那一步：对真类的**方法体**逐条检查
① 引用的类型在应用类加载器里是否都能解析（app dex + jar + boot classpath）；
② `invoke-*` 的目标方法沿父类链是否真的存在。
两个计数都为 0 才允许删桩 —— 本机三个候选全部为 0，实测删除后应用正常，
与 v9/v10 那批「真类引用 HwWidgetFactory / SmsInterceptionListener」的类形成对照。

### 每步真机验证（工具的判据，不是感觉）

`tools/apptest.sh`（Android 侧，root）：

```bash
sh /data/local/tmp/fuck_andes/apptest.sh 28
```

判据四项全绿才保留改动：

1. `dex2oat --compiler-filter=verify` 退出码 0（dex 未被整体拒绝）；
2. 冷启动后 `pidof com.huawei.meetime` 非空、`dumpsys activity` 里前台/栈中出现
   `com.huawei.meetime/.login.HiCallBindPhoneNumberActivity`；
3. `/sdcard/Android/data/com.huawei.meetime/files/mtlog/uspa_*.log` **出现新文件**且
   `result is success` > 0（comToken 拿到）；
4. `/data/system/dropbox` 无新的 `data_app_crash`。

部署技巧（沿用 v8）：**原位覆盖**模块里的 jar（`cat new > files/huawei_abilityshell_stub.jar`，
同 inode）会立刻透过 bind 生效，无需重启；改完看
`md5sum /proc/1/root/system_ext/framework/audiosphere.jar` 确认应用真看到新内容。

### 仍然保留、未处理

- `classes2` 里与固件真类**重名且无缺方法**的 126 个桩继续保留（删它们只会引入风险，无收益）。
- 568 个应用引用不到的华为私有类型（`android.telephony.SmsInterceptionListener` 等）仍未补，
  新增代码路径仍可能 NoClassDefFoundError；补桩前需先证明该路径会被执行。
- `com.alibaba.fastjson.JSONObject`、`com.squareup.okhttp.MediaType`、
  `com.huawei.wisesecurity.ucs.credential.Credential` 的 `toString()` 曾被列为「缺失」，
  实际解析到 `java.lang.Object.toString()`，属假警报；其中 fastjson/okhttp 桩全是默认返回，
  说明应用这些引用并未在执行路径上（应用自带 fastjson2）。

### 复现命令

```bash
# 1) 缺方法判据
python3 tools/dex_refs.py mjar/o2 meetime_dex/*.dex > /tmp/refs.txt   # 应用引用了什么
python3 tools/gapanalyze.py                                          # 哪些真的解析不到
# 2) 删桩前的真类可链接性
python3 tools/linkcheck.py com.huawei.android.os.ServiceManagerEx ... # 0 缺失才可删
# 3) 改完重建（Assemble → 组 jar）
sh mkbuild.sh                                                        # 产出 out_stub.jar
# 4) 部署 + 真机验证（Android 侧）
cat out_stub.jar > /data/adb/modules/huawei_abilityshell_stub/files/huawei_abilityshell_stub.jar
sh /data/local/tmp/fuck_andes/apptest.sh 28
```

> 另：`tools/callkind2.py <类> <签名>` 按指令边界解码应用 dex，报出该方法是
> `invoke-static` 还是 `invoke-virtual` —— 猜错会得到 IncompatibleClassChangeError
> 而不是 NoSuchMethodError，补桩前值得先查（本次 `InputMethodManagerEx.getInstance()`
> 实证为 `invoke-static`，位于 `com.huawei.meetime.vendor.emui.view.InputMethodManagerEmui`）。
