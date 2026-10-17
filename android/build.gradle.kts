// JARVIS Remote — root Gradle build (Android project).
// Tune the AGP/versions once via gradle/libs.versions.toml — not here.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
}
