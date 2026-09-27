import io

F = '/workspace/mfx2/src/com/eta/meetimefix/Hook.smali'
s = io.open(F, encoding='utf-8').read()

anchor = '    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseNetworkState(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V'
assert anchor in s, 'anchor missing'

add = '\n\n    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseUdidPermission(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V\n\n    invoke-direct {p0, p1}, Lcom/eta/meetimefix/Hook;->neutraliseUdid(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V'

if 'neutraliseUdidPermission' not in s:
    s = s.replace(anchor, anchor + add, 1)

# 默认参数版 findAndHookMethod（无参）用于 getUDID
def method(name, cls, mth, cb, params_smali, mark):
    return '''
.method private ''' + name + '''(Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;)V
    .registers 8

    :try_start_0
    const-string v0, "''' + cls + '''"

    iget-object p1, p1, Lde/robv/android/xposed/callbacks/XC_LoadPackage$LoadPackageParam;->classLoader:Ljava/lang/ClassLoader;

    const-string v1, "''' + mth + '''"

    new-instance v2, Lcom/eta/meetimefix/''' + cb + ''';

    invoke-direct {v2, p0}, Lcom/eta/meetimefix/''' + cb + ''';-><init>(Lcom/eta/meetimefix/Hook;)V

''' + params_smali + '''
    invoke-static {v0, p1, v1, v3}, Lde/robv/android/xposed/XposedHelpers;->findAndHookMethod(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/lang/String;[Ljava/lang/Object;)Lde/robv/android/xposed/XC_MethodHook$Unhook;

    const-string v0, "''' + mark + '''"

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

# getUDID —— 静态无参
p_udid = '''    const/4 v3, 0x1

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    aput-object v2, v3, v4
'''

# ContextCompat.checkSelfPermission(Context, String)
p_perm = '''    const/4 v3, 0x3

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    const-class v5, Landroid/content/Context;

    aput-object v5, v3, v4

    const/4 v4, 0x1

    const-class v5, Ljava/lang/String;

    aput-object v5, v3, v4

    const/4 v4, 0x2

    aput-object v2, v3, v4
'''

if 'private neutraliseUdid' not in s.split('# virtual methods')[0]:
    body = method('neutraliseUdidPermission', 'androidx.core.content.ContextCompat',
                  'checkSelfPermission', 'Hook$7', p_perm, 'perm_hook_installed.txt')
    body += method('neutraliseUdid', 'com.huawei.android.os.BuildEx',
                   'getUDID', 'Hook$6', p_udid, 'udid_hook_installed.txt')
    i = s.index('# virtual methods')
    s = s[:i] + body.lstrip('\n') + s[i:]

io.open(F, 'w', encoding='utf-8').write(s)
print('  patched: 方法数 %d' % s.count('.method '))
