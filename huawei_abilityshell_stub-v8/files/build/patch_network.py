import io

F = '/workspace/mfx2/src/com/eta/meetimefix/Hook.smali'
s = io.open(F, encoding='utf-8').read()

anchor = '    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutralisePhoneAccount(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V'
assert anchor in s, 'anchor not found'
if 'neutraliseNetworkState' not in s:
    s = s.replace(anchor, anchor + '\n\n    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseNetworkState(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V', 1)

method = '''
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


'''

if 'neutraliseNetworkState(Lde/robv' not in s.split('# virtual methods')[0]:
    i = s.index('# virtual methods')
    s = s[:i] + method.lstrip('\n') + s[i:]

io.open(F, 'w', encoding='utf-8').write(s)
print('  Hook.smali patched; 方法数 %d' % s.count('.method '))
