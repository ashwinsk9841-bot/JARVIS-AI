package com.jarvis.remote

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat

/** JARVIS Remote — phone half of the secure laptop <-> phone link.
 *
 * The phone NEVER opens an inbound port or dials in; it dials OUT to the relay
 * (see RelayService), presents only the sha-256 HASH of the pairing code, and
 * routes E2E-sealed frames once the laptop claims the pair.
 */
class MainActivity : ComponentActivity() {

    private val status = mutableStateOf("Not paired. Ask the laptop: enable remote bridge")
    private val busy = mutableStateOf(false)
    private var code = ""

    private val permLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
            runPermissionChecks()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        runPermissionChecks()
        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) {
                    Column(
                        Modifier.fillMaxSize().padding(24.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text("JARVIS Remote", style = MaterialTheme.typography.headlineMedium)
                        Text(status.value)
                        OutlinedTextField(
                            value = code, onValueChange = { code = it.uppercase().trim() },
                            label = { Text("Pairing code") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                        Button(
                            onClick = { pair() }, enabled = !busy.value,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text(if (busy.value) "Pairing…" else "Pair this phone") }
                        TextButton(onClick = { PairingStore.clear(this@MainActivity) }) {
                            Text("Forget pairing")
                        }
                    }
                }
            }
        }
    }

    private fun pairingPrefs() = getSharedPreferences("jarvis_pairing", MODE_PRIVATE)

    private fun pair() {
        if (code.length < 8) {
            status.value = "The laptop shows an 8+ character pairing code."
            return
        }
        busy.value = true
        status.value = "Pairing as ${code.length} chars… (only a hash leaves this phone)"
        
        val salt = Crypto.randomSalt()
        val hash = Crypto.sha256Hex(code + salt)
        val defaultWsUrl = "wss://YOUR-RELAY-HOST/ws/relay" // Can customize as needed
        PairingStore.save(this, hash, code, salt, defaultWsUrl)

        RelayService.start(this)
        Toast.makeText(this, "Pairing started", Toast.LENGTH_SHORT).show()
        status.value = "Pairing started. Watch for the laptop to accept it."
        busy.value = false
    }

    private fun runPermissionChecks() {
        val want = mutableListOf(
            Manifest.permission.POST_NOTIFICATIONS,
            Manifest.permission.READ_SMS,
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_CALL_LOG,
            Manifest.permission.READ_CONTACTS,
            Manifest.permission.CAMERA,
            Manifest.permission.VIBRATE,
        )
        if (Build.VERSION.SDK_INT >= 33) want += Manifest.permission.READ_PHONE_NUMBERS
        val missing = want.distinct()
            .filter { ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED }
            .toTypedArray()
        if (missing.isNotEmpty()) permLauncher.launch(missing)
    }
}
