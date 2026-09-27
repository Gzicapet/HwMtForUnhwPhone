.class public Lcom/eta/meetimefix/Hook;
.super Ljava/lang/Object;
.source "Hook.java"

# interfaces
.implements Lde/robv/android/xposed/IXposedHookLoadPackage;


# static fields
.field private static final PKG:Ljava/lang/String; = "com.huawei.meetime"

.field private static final PROBE:Ljava/lang/String; = "/data/user/0/com.huawei.meetime/meetimefix_probe.txt"

.field private static final RINGTONE_CLS:Ljava/lang/String; = "com.huawei.meetime.ringtone.RingtoneHelper"

.field private static final RINGTONE_MTH:Ljava/lang/String; = "cleanRingtoneStorage"

.field private static final STUB_JAR:Ljava/lang/String; = "/system_ext/framework/audiosphere.jar"


# direct methods
.method public constructor <init>()V
    .registers 1

    .line 31
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method static synthetic access$000(Ljava/lang/ClassLoader;Ljava/lang/String;)V
    .registers 2

    .line 31
    invoke-static {p0, p1}, Lcom/eta/meetimefix/Hook;->appendDex(Ljava/lang/ClassLoader;Ljava/lang/String;)V

    return-void
.end method

.method private static appendDex(Ljava/lang/ClassLoader;Ljava/lang/String;)V
    .registers 7

    .line 81
    if-nez p0, :cond_3

    .line 82
    return-void

    .line 87
    :cond_3
    :try_start_3
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v0

    const-string v1, "addDexPath"

    const/4 v2, 0x1

    new-array v2, v2, [Ljava/lang/Class;

    const-class v3, Ljava/lang/String;

    const/4 v4, 0x0

    aput-object v3, v2, v4

    invoke-virtual {v0, v1, v2}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v0

    const-string v1, "/system_ext/framework/audiosphere.jar"

    filled-new-array {v1}, [Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, p0, v1}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    .line 88
    new-instance p0, Ljava/lang/StringBuilder;

    invoke-direct {p0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v0, "[meetimefix] stub jar appended ("

    invoke-virtual {p0, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    const-string v0, ")"

    invoke-virtual {p0, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    invoke-static {p0}, Lde/robv/android/xposed/XposedBridge;->log(Ljava/lang/String;)V
    :try_end_3a
    .catchall {:try_start_3 .. :try_end_3a} :catchall_3b

    .line 91
    goto :goto_5c

    .line 89
    :catchall_3b
    move-exception p0

    .line 90
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "[meetimefix] addDexPath failed ("

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    const-string v0, "): "

    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    invoke-static {p0}, Lde/robv/android/xposed/XposedBridge;->log(Ljava/lang/String;)V

    .line 92
    :goto_5c
    return-void
.end method

.method private injectStubJar(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 4

    .line 63
    iget-object v0, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    const-string v1, "direct"

    invoke-static {v0, v1}, Lcom/eta/meetimefix/Hook;->appendDex(Ljava/lang/ClassLoader;Ljava/lang/String;)V

    .line 67
    :try_start_7
    const-string v0, "android.app.LoadedApk"

    iget-object p1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    invoke-static {v0, p1}, Lde/robv/android/xposed/XposedHelpers;->findClass(Ljava/lang/String;Ljava/lang/ClassLoader;)Ljava/lang/Class;

    move-result-object p1

    .line 69
    const-string v0, "createClassLoader"

    new-instance v1, Lcom/eta/meetimefix/Hook$1;

    invoke-direct {v1, p0}, Lcom/eta/meetimefix/Hook$1;-><init>(Lcom/eta/meetimefix/Hook;)V

    invoke-static {p1, v0, v1}, Lde/robv/android/xposed/XposedBridge;->hookAllMethods(Ljava/lang/Class;Ljava/lang/String;Lde/robv/android/xposed/XC_MethodHook;)Ljava/util/Set;
    :try_end_19
    .catchall {:try_start_7 .. :try_end_19} :catchall_1a

    .line 77
    goto :goto_31

    .line 75
    :catchall_1a
    move-exception p1

    .line 76
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "[meetimefix] classloader hook failed: "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-static {p1}, Lde/robv/android/xposed/XposedBridge;->log(Ljava/lang/String;)V

    .line 78
    :goto_31
    return-void
.end method

.method private neutraliseRingtoneWrite(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 5

    .line 97
    :try_start_0
    const-string v0, "com.huawei.meetime.ringtone.RingtoneHelper"

    iget-object p1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    const-string v1, "cleanRingtoneStorage"

    new-instance v2, Lcom/eta/meetimefix/Hook$2;

    invoke-direct {v2, p0}, Lcom/eta/meetimefix/Hook$2;-><init>(Lcom/eta/meetimefix/Hook;)V

    filled-new-array {v2}, [Ljava/lang/Object;

    move-result-object v2

    invoke-static {v0, p1, v1, v2}, Lde/robv/android/xposed/XposedHelpers;->findAndHookMethod(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/lang/String;[Ljava/lang/Object;)Lde/robv/android/xposed/XC_MethodHook$Unhook;

    .line 104
    const-string p1, "[meetimefix] hooked com.huawei.meetime.ringtone.RingtoneHelper.cleanRingtoneStorage"

    invoke-static {p1}, Lde/robv/android/xposed/XposedBridge;->log(Ljava/lang/String;)V
    :try_end_17
    .catchall {:try_start_0 .. :try_end_17} :catchall_18

    .line 107
    goto :goto_2f

    .line 105
    :catchall_18
    move-exception p1

    .line 106
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "[meetimefix] ringtone hook failed: "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-static {p1}, Lde/robv/android/xposed/XposedBridge;->log(Ljava/lang/String;)V

    .line 108
    :goto_2f
    return-void
.end method


.method private neutraliseSimRead(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 8

    :try_start_0
    const-string v0, "com.huawei.meetime.login.SimUtils"

    iget-object p1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    const-string v1, "getSimCardNumber"

    new-instance v2, Lcom/eta/meetimefix/Hook$3;

    invoke-direct {v2, p0}, Lcom/eta/meetimefix/Hook$3;-><init>(Lcom/eta/meetimefix/Hook;)V

    const/4 v3, 0x2

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    const-class v5, Landroid/content/Context;

    aput-object v5, v3, v4

    const/4 v4, 0x1

    aput-object v2, v3, v4

    invoke-static {v0, p1, v1, v3}, Lde/robv/android/xposed/XposedHelpers;->findAndHookMethod(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/lang/String;[Ljava/lang/Object;)Lde/robv/android/xposed/XC_MethodHook$Unhook;

    const-string v0, "[meetimefix] hooked getSimCardNumber"

    invoke-static {v0}, Lde/robv/android/xposed/XposedBridge;->log(Ljava/lang/String;)V

    const-string v0, "sim_hook_installed.txt"

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->mark(Ljava/lang/String;)V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    goto :goto_0

    :catchall_0
    move-exception v0

    invoke-static {v0}, Lde/robv/android/xposed/XposedBridge;->log(Ljava/lang/Throwable;)V

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->markErr(Ljava/lang/Throwable;)V

    :goto_0
    return-void
.end method


.method public static mark(Ljava/lang/String;)V
    .registers 3
    :try_start_0
    new-instance v0, Ljava/io/File;
    const-string v1, "/data/user/0/com.huawei.meetime/"
    invoke-direct {v0, v1}, Ljava/io/File;-><init>(Ljava/lang/String;)V
    new-instance v1, Ljava/io/File;
    invoke-direct {v1, v0, p0}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
    invoke-virtual {v1}, Ljava/io/File;->createNewFile()Z
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0
    goto :goto_0
    :catchall_0
    move-exception v0
    :goto_0
    return-void
.end method


.method public static markErr(Ljava/lang/Throwable;)V
    .registers 5
    :try_start_0
    new-instance v0, Ljava/io/StringWriter;
    invoke-direct {v0}, Ljava/io/StringWriter;-><init>()V
    new-instance v1, Ljava/io/PrintWriter;
    invoke-direct {v1, v0}, Ljava/io/PrintWriter;-><init>(Ljava/io/Writer;)V
    invoke-virtual {p0, v1}, Ljava/lang/Throwable;->printStackTrace(Ljava/io/PrintWriter;)V
    invoke-virtual {v1}, Ljava/io/PrintWriter;->flush()V
    new-instance v1, Ljava/io/FileOutputStream;
    const-string v2, "/data/user/0/com.huawei.meetime/sim_hook_error.txt"
    invoke-direct {v1, v2}, Ljava/io/FileOutputStream;-><init>(Ljava/lang/String;)V
    invoke-virtual {v0}, Ljava/io/StringWriter;->toString()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v0}, Ljava/lang/String;->getBytes()[B
    move-result-object v0
    invoke-virtual {v1, v0}, Ljava/io/FileOutputStream;->write([B)V
    invoke-virtual {v1}, Ljava/io/FileOutputStream;->close()V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0
    goto :goto_0
    :catchall_0
    move-exception v0
    :goto_0
    return-void
.end method


.method private neutralisePhoneAccount(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 8

    :try_start_0
    const-string v0, "android.telecom.TelecomManager"

    iget-object p1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    const-string v1, "getPhoneAccount"

    new-instance v2, Lcom/eta/meetimefix/Hook$4;

    invoke-direct {v2, p0}, Lcom/eta/meetimefix/Hook$4;-><init>(Lcom/eta/meetimefix/Hook;)V

    const/4 v3, 0x2

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    const-class v5, Landroid/telecom/PhoneAccountHandle;

    aput-object v5, v3, v4

    const/4 v4, 0x1

    aput-object v2, v3, v4

    invoke-static {v0, p1, v1, v3}, Lde/robv/android/xposed/XposedHelpers;->findAndHookMethod(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/lang/String;[Ljava/lang/Object;)Lde/robv/android/xposed/XC_MethodHook$Unhook;

    const-string v0, "tc_hook_installed.txt"

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->mark(Ljava/lang/String;)V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    goto :goto_0

    :catchall_0
    move-exception v0

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->markErr(Ljava/lang/Throwable;)V

    :goto_0
    return-void
.end method


.method private neutraliseNetworkState(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 8

    :try_start_0
    const-string v0, "com.huawei.base.utils.NetworkStatusManager"

    iget-object p1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    const-string v1, "isNetworkAvailable"

    new-instance v2, Lcom/eta/meetimefix/Hook$5;

    invoke-direct {v2, p0}, Lcom/eta/meetimefix/Hook$5;-><init>(Lcom/eta/meetimefix/Hook;)V

    const/4 v3, 0x1

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    aput-object v2, v3, v4

    invoke-static {v0, p1, v1, v3}, Lde/robv/android/xposed/XposedHelpers;->findAndHookMethod(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/lang/String;[Ljava/lang/Object;)Lde/robv/android/xposed/XC_MethodHook$Unhook;

    const-string v0, "net_hook_installed.txt"

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->mark(Ljava/lang/String;)V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    goto :goto_0

    :catchall_0
    move-exception v0

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->markErr(Ljava/lang/Throwable;)V

    :goto_0
    return-void
.end method


.method private neutraliseUdidPermission(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 8

    :try_start_0
    const-string v0, "androidx.core.content.ContextCompat"

    iget-object p1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    const-string v1, "checkSelfPermission"

    new-instance v2, Lcom/eta/meetimefix/Hook$7;

    invoke-direct {v2, p0}, Lcom/eta/meetimefix/Hook$7;-><init>(Lcom/eta/meetimefix/Hook;)V

    const/4 v3, 0x3

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    const-class v5, Landroid/content/Context;

    aput-object v5, v3, v4

    const/4 v4, 0x1

    const-class v5, Ljava/lang/String;

    aput-object v5, v3, v4

    const/4 v4, 0x2

    aput-object v2, v3, v4

    invoke-static {v0, p1, v1, v3}, Lde/robv/android/xposed/XposedHelpers;->findAndHookMethod(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/lang/String;[Ljava/lang/Object;)Lde/robv/android/xposed/XC_MethodHook$Unhook;

    const-string v0, "perm_hook_installed.txt"

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->mark(Ljava/lang/String;)V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    goto :goto_0

    :catchall_0
    move-exception v0

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->markErr(Ljava/lang/Throwable;)V

    :goto_0
    return-void
.end method



.method private neutraliseUdid(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 8

    :try_start_0
    const-string v0, "com.huawei.android.os.BuildEx"

    iget-object p1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    const-string v1, "getUDID"

    new-instance v2, Lcom/eta/meetimefix/Hook$6;

    invoke-direct {v2, p0}, Lcom/eta/meetimefix/Hook$6;-><init>(Lcom/eta/meetimefix/Hook;)V

    const/4 v3, 0x1

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    aput-object v2, v3, v4

    invoke-static {v0, p1, v1, v3}, Lde/robv/android/xposed/XposedHelpers;->findAndHookMethod(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/lang/String;[Ljava/lang/Object;)Lde/robv/android/xposed/XC_MethodHook$Unhook;

    const-string v0, "udid_hook_installed.txt"

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->mark(Ljava/lang/String;)V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    goto :goto_0

    :catchall_0
    move-exception v0

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->markErr(Ljava/lang/Throwable;)V

    :goto_0
    return-void
.end method


# virtual methods
.method public handleLoadPackage(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 4
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Throwable;
        }
    .end annotation

    .line 41
    if-eqz p1, :cond_26

    const-string v0, "com.huawei.meetime"

    iget-object v1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->packageName:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_d

    goto :goto_26

    .line 48
    :cond_d
    :try_start_d
    new-instance v0, Ljava/io/File;

    const-string v1, "/data/user/0/com.huawei.meetime/meetimefix_probe.txt"

    invoke-direct {v0, v1}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    .line 49
    invoke-virtual {v0}, Ljava/io/File;->exists()Z

    move-result v1

    if-nez v1, :cond_1d

    .line 50
    invoke-virtual {v0}, Ljava/io/File;->createNewFile()Z
    :try_end_1d
    .catchall {:try_start_d .. :try_end_1d} :catchall_1e

    .line 54
    :cond_1d
    goto :goto_1f

    .line 52
    :catchall_1e
    move-exception v0

    .line 56
    :goto_1f
    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->injectStubJar(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V

    .line 57
    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseRingtoneWrite(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V

    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseSimRead(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V

    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutralisePhoneAccount(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V

    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseNetworkState(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V

    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseUdidPermission(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V

    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseUdid(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V

    .line 58
    return-void

    .line 42
    :cond_26
    :goto_26
    return-void
.end method
