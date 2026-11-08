# Scaffold a Compose for TV app in Kotlin

This is the smallest Android TV app we could make that builds, shows up on the TV's home screen and works with the remote. Give these files to the agent as its starting point, or ask it to write the same thing. Either way, check that the four TV parts are there:

- **The leanback launcher intent** (`LEANBACK_LAUNCHER`). Without it the app doesn't show on the TV's home screen.
- **A banner** (`android:banner`). The 320x180 dp tile the home screen shows.
- **No touch required.** A TV has no touchscreen, so the manifest marks it not required.
- **D-pad focus.** Compose for TV (`androidx.tv:tv-material`) gives you buttons and cards that show focus. One of them asks for focus at start, so OK works straight away.

## What you need

- The toolchain from lesson 4, with `env.sh` loaded.

## Steps

1. **Make the folders.** Run this in the project folder from lesson 2.

   ```bash
   mkdir -p app/src/main/java/com/example/tv app/src/main/res/drawable
   ```

2. **Write `settings.gradle.kts`.**

   ```kotlin
   pluginManagement {
       repositories { google(); mavenCentral(); gradlePluginPortal() }
   }
   dependencyResolutionManagement {
       repositories { google(); mavenCentral() }
   }
   rootProject.name = "TvApp"
   include(":app")
   ```

3. **Write `build.gradle.kts`.**

   ```kotlin
   plugins {
       id("com.android.application") version "8.7.3" apply false
       id("org.jetbrains.kotlin.android") version "2.0.21" apply false
       id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
   }
   ```

4. **Write `gradle.properties`.**

   ```
   android.useAndroidX=true
   org.gradle.jvmargs=-Xmx2g
   ```

5. **Write `app/build.gradle.kts`.** The release build is shrunk and signed with the debug key. That's fine for an app you only sideload to your own TV.

   ```kotlin
   plugins {
       id("com.android.application")
       id("org.jetbrains.kotlin.android")
       id("org.jetbrains.kotlin.plugin.compose")
   }

   android {
       namespace = "com.example.tv"
       compileSdk = 35
       defaultConfig {
           applicationId = "com.example.tv"
           minSdk = 26
           targetSdk = 35
           versionCode = 1
           versionName = "0.1"
       }
       buildTypes {
           release {
               isMinifyEnabled = true
               proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
               // Sideload only: the debug key lets `adb install -r` work without a keystore.
               signingConfig = signingConfigs.getByName("debug")
           }
       }
       compileOptions {
           sourceCompatibility = JavaVersion.VERSION_17
           targetCompatibility = JavaVersion.VERSION_17
       }
       kotlinOptions { jvmTarget = "17" }
       buildFeatures { compose = true }
   }

   dependencies {
       implementation(platform("androidx.compose:compose-bom:2024.12.01"))
       implementation("androidx.activity:activity-compose:1.9.3")
       implementation("androidx.compose.foundation:foundation")
       implementation("androidx.tv:tv-material:1.0.0")
   }
   ```

6. **Write `app/src/main/AndroidManifest.xml`.**

   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <manifest xmlns:android="http://schemas.android.com/apk/res/android">
       <uses-feature android:name="android.software.leanback" android:required="false" />
       <uses-feature android:name="android.hardware.touchscreen" android:required="false" />

       <application
           android:banner="@drawable/banner"
           android:label="TV App"
           android:theme="@android:style/Theme.DeviceDefault.NoActionBar">
           <activity android:name=".MainActivity" android:exported="true">
               <intent-filter>
                   <action android:name="android.intent.action.MAIN" />
                   <category android:name="android.intent.category.LEANBACK_LAUNCHER" />
               </intent-filter>
           </activity>
       </application>
   </manifest>
   ```

7. **Write `app/src/main/res/drawable/banner.xml`.** A plain coloured tile for now.

   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <!-- The 320x180 dp tile the TV launcher shows. Swap for a PNG with your app's name on it. -->
   <shape xmlns:android="http://schemas.android.com/apk/res/android">
       <solid android:color="#0B3D4C" />
       <size android:width="320dp" android:height="180dp" />
   </shape>
   ```

8. **Write `app/src/main/java/com/example/tv/MainActivity.kt`.** Three buttons you move between with the remote. The first one takes focus at start. The app logs a timestamp when the screen is ready, and one per click. The agent reads these with logcat (lesson 7).

   ```kotlin
   package com.example.tv

   import android.os.Bundle
   import android.os.SystemClock
   import android.util.Log
   import androidx.activity.ComponentActivity
   import androidx.activity.compose.setContent
   import androidx.compose.foundation.layout.Arrangement
   import androidx.compose.foundation.layout.Row
   import androidx.compose.foundation.layout.fillMaxSize
   import androidx.compose.foundation.layout.padding
   import androidx.compose.runtime.LaunchedEffect
   import androidx.compose.runtime.remember
   import androidx.compose.ui.Modifier
   import androidx.compose.ui.focus.FocusRequester
   import androidx.compose.ui.focus.focusRequester
   import androidx.compose.ui.unit.dp
   import androidx.tv.material3.Button
   import androidx.tv.material3.MaterialTheme
   import androidx.tv.material3.Surface
   import androidx.tv.material3.Text

   class MainActivity : ComponentActivity() {
       override fun onCreate(savedInstanceState: Bundle?) {
           super.onCreate(savedInstanceState)
           setContent {
               MaterialTheme {
                   Surface(Modifier.fillMaxSize()) {
                       val first = remember { FocusRequester() }
                       Row(Modifier.padding(48.dp), horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                           listOf("One", "Two", "Three").forEachIndexed { i, label ->
                               Button(
                                   onClick = { Log.i("MyAppTiming", "click $label uptime=${SystemClock.uptimeMillis()}") },
                                   modifier = if (i == 0) Modifier.focusRequester(first) else Modifier,
                               ) {
                                   Text(label)
                               }
                           }
                       }
                       LaunchedEffect(Unit) {
                           first.requestFocus()
                           Log.i("MyAppTiming", "ready uptime=${SystemClock.uptimeMillis()}")
                       }
                   }
               }
           }
       }
   }
   ```

9. **Point the build at your SDK and make the Gradle wrapper.**

   ```bash
   echo "sdk.dir=$ANDROID_HOME" > local.properties
   gradle wrapper --gradle-version 8.11.1
   ```

10. **Build.**

    ```bash
    ./gradlew assembleRelease
    ```

    The APK is `app/build/outputs/apk/release/app-release.apk`, under 1 MB.

11. **Check the TV will list it.** `aapt2` comes with the build tools.

    ```bash
    "$ANDROID_HOME/build-tools/35.0.0/aapt2" dump badging app/build/outputs/apk/release/app-release.apk | grep leanback
    ```

    You should see a `leanback-launchable-activity` line.

12. **Install and start it.** (untested with this scaffold. The same two commands were run many times with our example app.)

    ```bash
    adb -s 192.168.1.x:5555 install -r app/build/outputs/apk/release/app-release.apk
    adb -s 192.168.1.x:5555 shell am start -n com.example.tv/.MainActivity
    ```

13. **Commit.** First write a `.gitignore`, so the toolchain, the build output and the downloads stay out of git. From here on, the agent makes one commit per change. (untested)

    ```bash
    printf '%s\n' /tools/ /sdk/ /gradle-home/ /local.properties build/ .gradle/ .kotlin/ '*.apk' '*.zip' '*.tar.gz' > .gitignore
    git init -q && git add -A && git commit -qm "Scaffold a Compose for TV app"
    ```

## Gotchas

- Keep the same signing key for every build. `adb install -r` refuses an APK signed with a different key. The only way round that is to uninstall, which deletes the app's data.
- An app with no `android:banner` still installs. Some launchers then show a blank tile. (untested)
- Compose for TV's `Button` and `Card` show D-pad focus for you. Plain Compose `clickable` shows little or no focus on a TV, so use the `tv-material` components.
- Write the `.gitignore` before the first commit. Without it, `git add -A` picks up the JDK, the SDK, the Gradle cache, the build output and the downloaded archives.
- `gradle wrapper` checks its download URL first. When we re-ran this lesson, that check failed with `response code (504)` from the Gradle server. `gradle wrapper --gradle-version 8.11.1 --no-validate-url` skips the check, and the build then worked.
- The build may print `Warning: SDK processing. This version only understands SDK XML versions up to 3`. It's harmless.

## Notes

Steps 1 to 11 were run as written on 8 Nov 2026 on Linux, with Temurin JDK 17.0.21, Gradle 8.11.1, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, Compose BOM 2024.12.01 and tv-material 1.0.0. The release APK was 822 KB, with package `com.example.tv` and a `leanback-launchable-activity` line. Step 9 needed `--no-validate-url` that time (see Gotchas). An earlier version of this scaffold, with another package name and no start-up focus, was built twice the same day with the plain step 9.

Step 12 was not run with this scaffold. We didn't want a test app on a TV other people use. The same commands were run many times with our example app. Step 13 is plain git and was not run on the scaffold. We only checked its ignore list in an empty test folder, with dummy files in the same places: only the project files were committed. The start-up focus (the `FocusRequester`) builds, but we have not seen it on a TV.

## Links

- [Compose for TV](https://developer.android.com/training/tv/playback/compose)
- [Get started with TV apps (manifest, banner, leanback)](https://developer.android.com/training/tv/get-started/create)
- [Focus in Compose](https://developer.android.com/develop/ui/compose/touch-input/focus)
- [Gradle wrapper](https://docs.gradle.org/current/userguide/gradle_wrapper.html)
