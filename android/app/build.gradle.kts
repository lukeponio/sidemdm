import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Release signing comes from keystore.properties (git-ignored) or environment variables,
// never from the repository (NFR-02, NFR-09). See docs/release.md.
val signingProps = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}
fun signingValue(key: String, env: String): String? =
    signingProps.getProperty(key) ?: System.getenv(env)

android {
    namespace = "com.example.personalprofile"
    compileSdk = 36

    defaultConfig {
        // Must match PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME in the QR payload.
        applicationId = "com.example.personalprofile"
        minSdk = 36
        targetSdk = 36
        versionCode = 2
        versionName = "1.0.1"
    }

    signingConfigs {
        create("release") {
            val storePath = signingValue("storeFile", "DPC_KEYSTORE")
            if (storePath != null) {
                storeFile = file(storePath)
                storePassword = signingValue("storePassword", "DPC_KEYSTORE_PASSWORD")
                keyAlias = signingValue("keyAlias", "DPC_KEY_ALIAS")
                keyPassword = signingValue("keyPassword", "DPC_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    // Keep the APK byte-for-byte reproducible from the same sources and key.
    dependenciesInfo {
        includeInApk = false
        includeInBundle = false
    }
}

kotlin {
    jvmToolchain(17)
}

dependencies {
    // No AndroidX, analytics or other runtime libraries (NFR-06).
    testImplementation("junit:junit:4.13.2")
}
