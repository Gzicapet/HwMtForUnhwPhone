.class Lcom/eta/meetimefix/Hook$7;
.super Lde/robv/android/xposed/XC_MethodHook;
.source "Hook.java"


# instance fields
.field final synthetic this$0:Lcom/eta/meetimefix/Hook;


# direct methods
.method constructor <init>(Lcom/eta/meetimefix/Hook;)V
    .registers 2

    iput-object p1, p0, Lcom/eta/meetimefix/Hook$7;->this$0:Lcom/eta/meetimefix/Hook;

    invoke-direct {p0}, Lde/robv/android/xposed/XC_MethodHook;-><init>()V

    return-void
.end method


# virtual methods
.method public beforeHookedMethod(Lde/robv/android/xposed/XC_MethodHook$MethodHookParam;)V
    .registers 4

    # TelephonyUtil.getUdid() / getUnEncryptUdid() 的第一道门是：
    #   ContextCompat.checkSelfPermission(ctx,
    #       "com.huawei.permission.sec.ACCESS_UDID") == 0
    # 官方规范里该权限保护级为 signature|privileged，只有华为预装的
    # 特权应用能拿到；本机 PMS 甚至不认识这个权限（pm grant 报
    # Unknown permission），因此恒为 DENIED，getUdid() 直接返回空串。
    # 本机不可能满足 signature 匹配，也没有 privileged 安装位，
    # 所以在应用进程内把这道检查放行 —— 我们提供的 UDID 本就是合成值，
    # 放行不泄露任何真实硬件标识。
    iget-object v0, p1, Lde/robv/android/xposed/XC_MethodHook$MethodHookParam;->args:[Ljava/lang/Object;

    const/4 v1, 0x1

    aget-object v0, v0, v1

    const-string v1, "com.huawei.permission.sec.ACCESS_UDID"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_1e

    const/4 v0, 0x0

    invoke-static {v0}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v0

    invoke-virtual {p1, v0}, Lde/robv/android/xposed/XC_MethodHook$MethodHookParam;->setResult(Ljava/lang/Object;)V

    const-string v0, "perm_hook_fired.txt"

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->mark(Ljava/lang/String;)V

    :cond_1e
    return-void
.end method
