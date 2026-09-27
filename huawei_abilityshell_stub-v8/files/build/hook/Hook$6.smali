.class Lcom/eta/meetimefix/Hook$6;
.super Lde/robv/android/xposed/XC_MethodHook;
.source "Hook.java"


# instance fields
.field final synthetic this$0:Lcom/eta/meetimefix/Hook;


# direct methods
.method constructor <init>(Lcom/eta/meetimefix/Hook;)V
    .registers 2

    iput-object p1, p0, Lcom/eta/meetimefix/Hook$6;->this$0:Lcom/eta/meetimefix/Hook;

    invoke-direct {p0}, Lde/robv/android/xposed/XC_MethodHook;-><init>()V

    return-void
.end method


# virtual methods
.method public beforeHookedMethod(Lde/robv/android/xposed/XC_MethodHook$MethodHookParam;)V
    .registers 3

    # 华为官方 OEM 预装指南（HMS Core Preloading Guide - Unique Device ID）规定：
    #   com.huawei.android.os.BuildEx.getUDID() 返回 64 位十六进制设备唯一标识，
    #   由 OEM 预先写入设备；异常时返回空串。
    # 本机固件自带的实现是去查华为私有系统服务 device_identifiers
    # （IDeviceIdentifiersPolicyService.getUDID()），ZTE 上没有该服务，
    # 所以被替换成了返回 null 的桩 —— 这正是「device id is empty →
    # getComToken requestPara is invalid → GET COMTOKEN FAIL」的根源。
    # 这里按官方格式补一个稳定值：sha256("meetime-port:320144232091:eta")，
    # 即 boot serial 320144232091 的确定性派生，重启不变。
    const-string v0, "64ae149753ceae0688b24bcb64664b1cb6c5c92c93f4bfd18f393dfaa4f736d1"

    invoke-virtual {p1, v0}, Lde/robv/android/xposed/XC_MethodHook$MethodHookParam;->setResult(Ljava/lang/Object;)V

    const-string v0, "udid_hook_fired.txt"

    invoke-static {v0}, Lcom/eta/meetimefix/Hook;->mark(Ljava/lang/String;)V

    return-void
.end method
