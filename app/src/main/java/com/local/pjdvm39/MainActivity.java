package com.local.pjdvm39;

import android.app.Activity;
import android.os.Bundle;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicInteger;

public final class MainActivity extends Activity implements SurfaceHolder.Callback {
    private TextView reportView;
    private SurfaceView surfaceView;
    private final ExecutorService renderExecutor = Executors.newSingleThreadExecutor();
    private final AtomicInteger surfaceGeneration = new AtomicInteger(0);
    private volatile boolean activityDestroyed = false;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        TextView heading = new TextView(this);
        heading.setText("PJDV M39 · Vulkan Surface Smoke Test\nExpected: a dark blue clear color if presentation succeeds.");
        heading.setPadding(20, 18, 20, 14);
        root.addView(heading, new LinearLayout.LayoutParams(-1, -2));

        surfaceView = new SurfaceView(this);
        surfaceView.getHolder().addCallback(this);
        root.addView(surfaceView, new LinearLayout.LayoutParams(-1, 0, 2.0f));

        reportView = new TextView(this);
        reportView.setText(nativeGetReport() + "\nWaiting for SurfaceView...\n");
        reportView.setTextIsSelectable(true);
        reportView.setPadding(20, 16, 20, 24);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(reportView);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 3.0f));
        setContentView(root);
    }

    @Override public void surfaceCreated(SurfaceHolder holder) { }

    @Override public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        if (width <= 0 || height <= 0 || !holder.getSurface().isValid() || activityDestroyed) return;
        final int generation = surfaceGeneration.incrementAndGet();
        // Own a Surface wrapper for the queued task; the holder may invalidate its
        // original Surface before this task reaches the single-thread executor.
        final Surface surface = new Surface(holder.getSurface());
        final int frameWidth = width;
        final int frameHeight = height;
        try {
            renderExecutor.execute(() -> {
                try {
                    if (activityDestroyed || generation != surfaceGeneration.get() || !surface.isValid()) return;
                    // Vulkan creation, queue waits and teardown can block; never run them on the UI thread.
                    final String result = nativeRenderFrame(surface, frameWidth, frameHeight);
                    runOnUiThread(() -> {
                        if (!activityDestroyed && generation == surfaceGeneration.get()
                                && surfaceView != null && surfaceView.getHolder().getSurface().isValid()) {
                            reportView.setText(nativeGetReport() + "\n--- Vulkan surface clear/present test ---\n" + result);
                        }
                    });
                } finally {
                    surface.release();
                }
            });
        } catch (RejectedExecutionException ignored) {
            surface.release();
            // Activity is shutting down; no further native work should be scheduled.
        }
    }

    @Override public void surfaceDestroyed(SurfaceHolder holder) {
        // Invalidate results from any in-flight frame; the native layer holds its own ANativeWindow ref.
        surfaceGeneration.incrementAndGet();
    }

    @Override protected void onDestroy() {
        activityDestroyed = true;
        surfaceGeneration.incrementAndGet();
        renderExecutor.shutdownNow();
        super.onDestroy();
    }

    private static native String nativeGetReport();
    private static native String nativeRenderFrame(Surface surface, int width, int height);
    static { System.loadLibrary("pjdvm39_port"); }
}
