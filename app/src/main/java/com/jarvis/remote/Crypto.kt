package com.jarvis.remote

import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec

/**
 * E2E crypto for the JARVIS Android companion.
 *
 * Contract MUST match the laptop half exactly (plugins/remote_bridge.py):
 *   key   = PBKDF2-HMAC-SHA256(pairing_code, salt, 200000 iters, 32 bytes)
 *   seal  = AES-256-GCM, 12-byte random nonce, 128-bit tag, empty AAD
 *   frame = {"type": "pairing_hash"|"pairing_claim"|"message", ...} JSON
 *   wire  = base64url no-padding for {cipher, nonce, salt}
 * The relay only ever sees the sha-256 HASH of the code and the ciphertext.
 */
object Crypto {
    private const val ITERS = 200_000
    private const val KEY_BYTES = 32
    private const val NONCE_BYTES = 12
    private const val TAG_BITS = 128
    private const val SALT_BYTES = 16

    fun sha256Hex(s: String): String =
        MessageDigest.getInstance("SHA-256").digest(s.toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it) }

    fun randomSalt(): String =
        Base64.encodeToString(ByteArray(SALT_BYTES).also { SecureRandom().nextBytes(it) },
            Base64.URL_SAFE or Base64.NO_WRAP or Base64.NO_PADDING)

    private fun deriveKey(code: String, saltB64: String): SecretKeySpec {
        val salt = Base64.decode(saltB64, Base64.URL_SAFE)
        val spec = PBEKeySpec(code.toCharArray(), salt, ITERS, KEY_BYTES * 8)
        val derived = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
            .generateSecret(spec).encoded
        return SecretKeySpec(derived, "AES")
    }

    /** Encrypt plaintext for the paired laptop. Returns b64url {cipher|nonce|salt}. */
    fun seal(code: String, saltB64: String, plaintext: String): String {
        val key = deriveKey(code, saltB64)
        val nonce = ByteArray(NONCE_BYTES).also { SecureRandom().nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key, GCMParameterSpec(TAG_BITS, nonce))
        val ct = cipher.doFinal(plaintext.toByteArray(Charsets.UTF_8))
        val payload = ByteArray(NONCE_BYTES + ct.size)
        System.arraycopy(nonce, 0, payload, 0, NONCE_BYTES)
        System.arraycopy(ct, 0, payload, NONCE_BYTES, ct.size)
        val out = android.util.Base64.encodeToString(payload, Base64.URL_SAFE or Base64.NO_PADDING)
        return out; // b64url( nonce || AES-GCM-NO-PADDING ct )
    }

    /** Decrypt a {salt, sealed} frame from the laptop. */
    fun open(code: String, saltB64: String, sealedB64: String): String {
        val key = deriveKey(code, saltB64)
        val raw = Base64.decode(sealedB64, Base64.URL_SAFE)
        val nonce = raw.copyOfRange(0, NONCE_BYTES)
        val ct = raw.copyOfRange(NONCE_BYTES, raw.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(TAG_BITS, nonce))
        return String(cipher.doFinal(ct), Charsets.UTF_8)
    }
}
