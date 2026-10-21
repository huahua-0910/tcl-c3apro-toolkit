package io.github.huahua0910.c3apro.settings;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

/** Permission-free links to the settings activities already present on this TV. */
public final class MainActivity extends Activity {
    private static final String SYSTEM_SETTINGS_PACKAGE = "com.android.tv.settings";

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setGravity(Gravity.CENTER_VERTICAL);
        page.setPadding(dp(64), dp(24), dp(64), dp(24));
        page.setBackgroundColor(Color.rgb(14, 21, 29));

        TextView title = new TextView(this);
        title.setText("设置与调试");
        title.setTextColor(Color.WHITE);
        title.setTextSize(29);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        page.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("用遥控器选择要打开的系统页面");
        subtitle.setTextColor(Color.rgb(169, 184, 198));
        subtitle.setTextSize(15);
        LinearLayout.LayoutParams subtitleParams = new LinearLayout.LayoutParams(-1, -2);
        subtitleParams.setMargins(0, dp(8), 0, dp(18));
        page.addView(subtitle, subtitleParams);

        Button developer = addButton(page, "开发者选项", Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS, 100);
        addButton(page, "系统设置", Settings.ACTION_SETTINGS, 101);
        addButton(page, "网络与互联网", Settings.ACTION_WIFI_SETTINGS, 102);
        addButton(page, "关于设备", Settings.ACTION_DEVICE_INFO_SETTINGS, 103);

        TextView footer = new TextView(this);
        footer.setText("打开系统原生页面 · 返回键回到此处");
        footer.setTextColor(Color.rgb(137, 154, 170));
        footer.setTextSize(13);
        LinearLayout.LayoutParams footerParams = new LinearLayout.LayoutParams(-1, -2);
        footerParams.setMargins(0, dp(12), 0, 0);
        page.addView(footer, footerParams);
        setContentView(page);
        if (savedInstanceState == null) developer.requestFocus();
    }

    private Button addButton(LinearLayout page, String title, final String action, int id) {
        Button button = new Button(this);
        button.setId(id);
        button.setText(title);
        button.setTextSize(20);
        button.setTextColor(Color.WHITE);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        button.setPadding(dp(22), 0, dp(22), 0);
        button.setMinHeight(0);
        button.setMinimumHeight(0);
        button.setFocusable(true);
        button.setBackground(buttonBackground());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(dp(660), dp(54));
        params.setMargins(0, 0, 0, dp(9));
        page.addView(button, params);
        button.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View view) {
                Intent intent = new Intent(action).setPackage(SYSTEM_SETTINGS_PACKAGE);
                try {
                    startActivity(intent);
                } catch (ActivityNotFoundException | SecurityException ex) {
                    Toast.makeText(MainActivity.this, "当前系统未开放这个入口，请使用原系统设置。", Toast.LENGTH_LONG).show();
                }
            }
        });
        return button;
    }

    private StateListDrawable buttonBackground() {
        StateListDrawable states = new StateListDrawable();
        states.addState(new int[]{android.R.attr.state_focused}, background(0xFF215369, 0xFF7BDCF1));
        states.addState(new int[]{android.R.attr.state_pressed}, background(0xFF215369, 0xFF7BDCF1));
        states.addState(new int[]{}, background(0xFF202D3A, 0xFF344556));
        return states;
    }

    private GradientDrawable background(int fill, int stroke) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(10));
        drawable.setStroke(dp(2), stroke);
        return drawable;
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
}
