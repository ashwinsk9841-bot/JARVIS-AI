package com.jarvis.remote

import android.app.*
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

/**
 * Foreground service that OWNS the outbound relay socket. Nothing on the
 * phone ever listens; this dials OUT to the relay, presents the sha-256 hash
 * of the pairing code, and forwards E2E-sealed frames to the laptop.
 */
class RelayService : Service() {

    private var client: RelayClient? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForegroundCompat()
        if (intent?.action == "STOP") { stopSelf(); return START_NOT_STICKY }
        ensureClient()
        return START_STICKY
    }

    private fun ensureClient() {
        if (client != null) return
        val cfg = PairingStore.load(this)
        if (cfg.codeHash.isEmpty()) { stopSelf(); return }
        client = RelayClient(this).also { 
            it.connect(cfg.code, cfg.salt, cfg.codeHash) { plain ->
                // handle incoming frame
            }
        }
    }

    private fun startForegroundCompat() {
        val ch = NotificationChannel("jarvis_relay", "JARVIS Remote link",
            NotificationManager.IMPORTANCE_LOW).also {
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager)
                .createNotificationChannel(it)
        }
        val n = NotificationCompat.Builder(this, "jarvis_relay")
            .setSmallIcon(R.drawable.ic_relay)
            .setContentTitle("JARVIS Remote")
            .setContentText("Relay link connected — dialing outbound")
            .setOngoing(true)
            .build()
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(FG, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(FG, n)
        }
    }

    override fun onDestroy() { client?.close(); client = null; super.onDestroy() }

    companion object {
        private const val FG = 8901
        fun start(ctx: Context) {
            val i = Intent(ctx, RelayService::class.java)
            ctx.startForegroundService(i)
        }
        fun stop(ctx: Context) {
            ctx.startService(Intent(ctx, RelayService::class.java).setAction("STOP"))
        }
    }
}
