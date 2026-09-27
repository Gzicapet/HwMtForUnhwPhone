.class public Lcom/x/V8;
.super Ljava/lang/Object;
.source "V8.java"


# 独立校验台：只依赖 jar 自身（不加载任何 Xposed 模块），
# 验证 com.huawei.android.os.BuildEx 是否是「合格的 OEM 实现」。
# 运行：CLASSPATH=<harness>.jar:<audiosphere>.jar app_process /system/bin com.x.V8

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method


# 打印 "label=value"
.method private static p(Ljava/lang/String;Ljava/lang/Object;)V
    .registers 4
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v1, " = "
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    sget-object v1, Ljava/lang/System;->out:Ljava/io/PrintStream;
    invoke-virtual {v1, v0}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
    return-void
.end method


# 反射调静态无参方法
.method private static c(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Object;
    .registers 6
    const/4 v0, 0x0
    new-array v1, v0, [Ljava/lang/Class;
    invoke-virtual {p0, p1, v1}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;
    move-result-object v2
    new-array v1, v0, [Ljava/lang/Object;
    const/4 v3, 0x0
    invoke-virtual {v2, v3, v1}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;
    move-result-object v2
    return-object v2
.end method


# 反射读静态字段
.method private static f(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Object;
    .registers 4
    invoke-virtual {p0, p1}, Ljava/lang/Class;->getField(Ljava/lang/String;)Ljava/lang/reflect/Field;
    move-result-object v0
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;
    move-result-object v0
    return-object v0
.end method


.method public static main([Ljava/lang/String;)V
    .registers 6

    const-string v0, "HARNESS-BEGIN"
    const/4 v1, 0x0
    invoke-static {v0, v1}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V

    :try_start_0
    const-string v0, "com.huawei.android.os.BuildEx"
    invoke-static {v0}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;
    move-result-object v2

    const-string v0, "findClass BuildEx"
    invoke-static {v0, v2}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V

    const-string v3, "getUDID"
    invoke-static {v2, v3}, Lcom/x/V8;->c(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v4
    invoke-static {v3, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V

    const-string v3, "getHarmonyUDID"
    invoke-static {v2, v3}, Lcom/x/V8;->c(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v4
    invoke-static {v3, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V

    const-string v3, "getSecondaryUDID"
    invoke-static {v2, v3}, Lcom/x/V8;->c(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v4
    invoke-static {v3, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    goto :goto_a

    :catchall_0
    move-exception v4
    const-string v0, "ERR-BuildEx"
    invoke-static {v0, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V

    :goto_a
    :try_start_1
    const-string v0, "com.huawei.android.os.BuildEx$VERSION"
    invoke-static {v0}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;
    move-result-object v2

    const-string v3, "EMUI_SDK_INT"
    invoke-static {v2, v3}, Lcom/x/V8;->f(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v4
    invoke-static {v3, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V

    const-string v3, "EMUI_SUB_SDK_INT"
    invoke-static {v2, v3}, Lcom/x/V8;->f(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v4
    invoke-static {v3, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_1

    goto :goto_b

    :catchall_1
    move-exception v4
    const-string v0, "ERR-VERSION"
    invoke-static {v0, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V

    :goto_b
    :try_start_2
    const-string v0, "com.huawei.android.os.BuildEx$VERSION_CODES"
    invoke-static {v0}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;
    move-result-object v2

    const-string v3, "HARMONY_4_3"
    invoke-static {v2, v3}, Lcom/x/V8;->f(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v4
    invoke-static {v3, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V
    :try_end_2
    .catchall {:try_start_2 .. :try_end_2} :catchall_2

    goto :goto_c

    :catchall_2
    move-exception v4
    const-string v0, "ERR-VERSION_CODES"
    invoke-static {v0, v4}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V

    :goto_c
    const-string v0, "HARNESS-DONE"
    const/4 v1, 0x0
    invoke-static {v0, v1}, Lcom/x/V8;->p(Ljava/lang/String;Ljava/lang/Object;)V
    return-void
.end method
