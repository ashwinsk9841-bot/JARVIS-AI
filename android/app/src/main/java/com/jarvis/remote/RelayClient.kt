package com.jarvis.remote

import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit
import org.json.JSONObject

/**
 * OUTBOUND-ONLY relay companion. Never opens a port, never listens,
 * never needs same-LAN/VPN/port-forward. Dials OUT to the relay, presents
 * the sha-256 hash of a one-time pairing code, and lets the relay route
 * sealed AES-256-GCM frames from the paired laptop. Wire/crypto contract is
 * fixed in the laptop bridge (plugins/remote_bridge.py) and docs/REMOTE.md.
 */
class RelayClient(
    private val app: Context,
    private val crypto: Crypto = Crypto,
    private val scope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.IO),
) {
    companion object {
        const val TAG = "JarvisRemote"
    }

    private val ws = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()

    private var socket: WebSocket? = null
    private var job: Job? = null
    private var onFrame: ((String) -> Unit)? = null

    fun connect(pairCode: String, saltB64: String, hashHex: String,
                onFrame: (String) -> Unit) {
        this.onFrame = onFrame
        val cfg = PairingStore.load(app)
        val url = cfg.relayWs
        val req = Request.Builder().url(url).build()
        socket = RelaySocketListener(pairCode, saltB64, hashHex, onFrame).let {
            ws.newWebSocket(req, it)
        }
        job = scope.launch {
            // Keep the relay outbound session warm; re-dial every loop is handled
            // by the WS client's own lifecycle, this just holds a re-dial timer.
        }
    }

    fun send(text: String) {
        socket?.send(text)
    }

    fun close() {
        socket?.close(1000, "bye")
        job?.cancel()
        scope.cancel()
        ws.dispatcher.executorService.shutdown()
    }

    private inner class RelaySocketListener(
        private val code: String,
        private val salt: String,
        private val hash: String,
        private val cb: (String) -> Unit,
    ) : WebSocketListener() {

        override fun onOpen(ws: WebSocket, response: Response) {
            Log.i(TAG, "ws open -> relay (outbound)")
            val claim = JSONObject()
                .put("type", "pairing_claim")
                .put("hash", hash)
                .put("salt", salt)
                .toString()
            ws.send(claim)
        }

        override fun onMessage(ws: WebSocket, text: String) {
            try {
                val j = JSONObject(text)
                when (j.optString("type")) {
                    "message" -> {
                        val sealed = j.getString("sealed")
                        val plain = crypto.open(code, salt, sealed)
                        cb(plain)
                    }
                    else -> Log.d(TAG, "relay meta: ${j.optString("type")}")
                }
            } catch (t: Throwable) {
                Log.w(TAG, "frame dropped", t)
            }
        }

        override fun onFailure(ws: WebSocket, t: Throwable, r: Response?) {
            Log.w(TAG, "ws failure (will re-dial by caller)", t)
        }
    }
}
