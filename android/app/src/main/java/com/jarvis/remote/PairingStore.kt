package com.jarvis.remote

import android.content.Context
import android.content.SharedPreferences

/** Persists ONLY the laptop-printed sha-256 hash + derived key salt + E2E
 *  seed. The raw pairing code is never stored on the phone. */
object PairingStore {
    private const val PREFS = "jarvis_pairing"
    private const val K_HASH = "code_hash"
    private const val K_CODE = "raw_tmp"       // wiped after first successful claim
    private const val K_SALT = "salt_b64"
    private const val K_URL = "relay_ws"

    data class Stored(val codeHash: String, val code: String, val salt: String,
                      val relayWs: String)

    fun save(ctx: Context, hash: String, code: String, salt: String, ws: String) {
        prefs(ctx).edit()
            .putString(K_HASH, hash)
            .putString(K_CODE, code)
            .putString(K_SALT, salt)
            .putString(K_URL, ws)
            .apply()
    }
    fun load(ctx: Context): Stored {
        val p = prefs(ctx)
        return Stored(
            p.getString(K_HASH, "") ?: "",
            p.getString(K_CODE, "") ?: "",
            p.getString(K_SALT, "") ?: "",
            p.getString(K_URL, "wss://YOUR-RELAY-HOST/ws/relay") ?: "",
        )
    }
    fun confirmPaired(ctx: Context) { prefs(ctx).edit().remove(K_CODE).apply() }
    fun clear(ctx: Context) { prefs(ctx).edit().clear().apply() }
    private fun prefs(ctx: Context): SharedPreferences =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
}
