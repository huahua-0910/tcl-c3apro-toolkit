package io.github.huahua0910.c3apro.policy;

import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

/** Experimental, local-only Google allowlist. No network, shell or owner auto-enrolment. */
public final class MainActivity extends Activity {
    private static final String[] CORE = {"com.google.android.gsf", "com.google.android.gms",
        "com.android.vending", "com.google.android.youtube.tv"};
    private static final String[] NATIVE = {"com.google.android.apps.mediashell",
        "com.google.android.apps.tv.dreamx", "com.google.android.apps.tv.launcherx",
        "com.google.android.feedback", "com.google.android.katniss", "com.google.android.partnersetup",
        "com.google.android.play.games", "com.google.android.syncadapters.calendar",
        "com.google.android.tungsten.setupwraith", "com.google.android.tv.remote.service",
        "com.google.android.youtube.tvmusic"};
    private DevicePolicyManager policy;
    private ComponentName admin;
    private TextView status;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        policy = (DevicePolicyManager) getSystemService(DEVICE_POLICY_SERVICE);
        admin = new ComponentName(this, LocalAdmin.class);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(48, 24, 48, 24);
        status = new TextView(this);
        status.setTextSize(18);
        page.addView(status);
        Button read = button(page, "读取管理状态", () -> readStatus());
        button(page, "备份并解除四项核心组件隐藏", () -> unhide(CORE));
        button(page, "备份并解除十一项原生组件隐藏", () -> unhide(NATIVE));
        button(page, "恢复本工具保存的原始隐藏状态", () -> restore());
        button(page, "撤销本工具设备所有者身份", () -> revoke());
        ScrollView scroll = new ScrollView(this);
        scroll.addView(page);
        setContentView(scroll);
        readStatus();
        read.requestFocus();
    }

    private Button button(LinearLayout page, String text, Runnable operation) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        page.addView(button, new LinearLayout.LayoutParams(-1, 88));
        button.setOnClickListener(view -> {
            try { operation.run(); }
            catch (Exception error) { status.setText("停止：" + error.getMessage()); }
        });
        return button;
    }

    private void guard() {
        if (!"C3APRO".equals(Build.MODEL) || Build.VERSION.SDK_INT != 34)
            throw new IllegalStateException("仅支持 C3APRO / API 34；停止修改。");
        if (!policy.isDeviceOwnerApp(getPackageName()))
            throw new IllegalStateException("没有设备所有者身份；本工具不会自行获取。");
    }

    private AtomicFile baseline() { return new AtomicFile(new File(getFilesDir(), "hidden-baseline.json")); }

    private JSONObject load() throws Exception {
        if (!baseline().getBaseFile().exists()) return new JSONObject();
        return new JSONObject(new String(baseline().readFully(), StandardCharsets.UTF_8));
    }

    private void persist(JSONObject data) throws Exception {
        AtomicFile file = baseline();
        FileOutputStream stream = file.startWrite();
        try {
            stream.write(data.toString(2).getBytes(StandardCharsets.UTF_8));
            file.finishWrite(stream);
        } catch (Exception error) {
            file.failWrite(stream);
            throw error;
        }
    }

    private void readStatus() {
        status.setText("Google 恢复实验 · 公开源码版\n设备所有者："
            + policy.isDeviceOwnerApp(getPackageName()) + "\n管理员：" + policy.isAdminActive(admin)
            + "\n先阅读 docs/03-google-recovery.md；不会自行取得权限。"
            + "\n卸载或清数据会丢失本工具的隐藏状态备份。");
    }

    private void unhide(String[] packages) {
        JSONObject before = new JSONObject();
        boolean started = false;
        try {
            guard();
            JSONObject original = load();
            for (String name : packages) {
                getPackageManager().getApplicationInfo(name, android.content.pm.PackageManager.MATCH_UNINSTALLED_PACKAGES);
                boolean value = policy.isApplicationHidden(admin, name);
                before.put(name, value);
                if (!original.has(name)) original.put(name, value);
            }
            persist(original); // Immutable first state for each package, before first change.
            started = true;
            for (String name : packages) {
                if (!policy.setApplicationHidden(admin, name, false)
                    || policy.isApplicationHidden(admin, name))
                    throw new IllegalStateException("解除隐藏失败：" + name);
            }
            status.setText("本组 hidden=false 已读回。原始状态已保存。\n仍需 ADB 核对 installed/enabled，之后撤销管理身份。");
        } catch (Exception error) {
            String result = "停止：" + error.getMessage();
            if (started) {
                for (java.util.Iterator<String> keys = before.keys(); keys.hasNext();) {
                    String name = keys.next();
                    try { set(name, before.getBoolean(name)); }
                    catch (Exception failure) { result += "\n回退未完成：" + name; }
                }
            }
            status.setText(result);
        }
    }

    private boolean allowed(String name) {
        for (String item : CORE) if (item.equals(name)) return true;
        for (String item : NATIVE) if (item.equals(name)) return true;
        return false;
    }

    private void set(String name, boolean hidden) {
        if (!allowed(name)) throw new IllegalStateException("非白名单包");
        if (!policy.setApplicationHidden(admin, name, hidden)
            || policy.isApplicationHidden(admin, name) != hidden)
            throw new IllegalStateException("未达到目标状态：" + name);
    }

    private void restore() {
        try {
            guard();
            JSONObject original = load();
            if (original.length() == 0) throw new IllegalStateException("没有已保存基线");
            for (java.util.Iterator<String> keys = original.keys(); keys.hasNext();) {
                String name = keys.next();
                set(name, original.getBoolean(name));
            }
            status.setText("已恢复保存的 hidden 原值；管理身份仍需单独撤销。");
        } catch (Exception error) { status.setText("恢复未完成：" + error.getMessage()); }
    }

    @SuppressWarnings("deprecation")
    private void revoke() {
        // Revocation remains available even if a later firmware update changes the model/API.
        try {
            if (!policy.isDeviceOwnerApp(getPackageName())) { readStatus(); return; }
            policy.clearDeviceOwnerApp(getPackageName());
            status.setText("撤销调用完成；设备所有者：" + policy.isDeviceOwnerApp(getPackageName())
                + "\n管理员：" + policy.isAdminActive(admin)
                + "\n请从 ADB 独立核对所有者、限制、备份服务及原有应用。");
        } catch (Exception error) { status.setText("撤销未完成：" + error.getMessage()); }
    }
}
