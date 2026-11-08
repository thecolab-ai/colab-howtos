# Scaffold a Compose for TV app and install it

This is the smallest Android TV app we could make that builds, shows up on the TV's home screen and works with the remote. Give these files to your agent as a starting point, or ask it to write the same thing.

It uses Jetpack Compose with the Compose for TV library (`androidx.tv:tv-material`). That library gives you buttons and cards that show D-pad focus.

## What you need

- Java 17. Any OpenJDK 17 build unpacked in your home folder works.
- The command-line tools and `sdkmanager` from lesson 1.
- Gradle 8.11.1, once, to make the wrapper. Later builds use `./gradlew`.

## Steps

1. **Install the SDK parts the build needs.** (Run by the earlier part of this build, into a project folder.)

   ```bash
   ~/android/cmdline-tools/latest/bin/sdkmanager --sdk_root="$HOME/android" "platforms;android-35" "build-tools;35.0.0"
   ```

2. **Make the project folders.**

   ```bash
   mkdir -p hellotv/app/src/main/java/com/example/hellotv hellotv/app/src/main/res/drawable
   cd hellotv
   ```

3. **Write `settings.gradle.kts`.**

   ```kotlin
   pluginManagement {
       repositories { google(); mavenCentral(); gradlePluginPortal() }
   }
   dependencyResolutionManagement {
       repositories { google(); mavenCentral() }
   }
   rootProject.name = "HelloTV"
   include(":app")
   ```

4. **Write `build.gradle.kts`.**

   ```kotlin
   plugins {
       id("com.android.application") version "8.7.3" apply false
       id("org.jetbrains.kotlin.android") version "2.0.21" apply false
       id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
   }
   ```

5. **Write `gradle.properties`.**

   ```
   android.useAndroidX=true
   org.gradle.jvmargs=-Xmx2g
   ```

6. **Write `app/build.gradle.kts`.** The release build is shrunk and signed with the debug key. That's fine for an app you only sideload to your own TV.

   ```kotlin
   plugins {
       id("com.android.application")
       id("org.jetbrains.kotlin.android")
       id("org.jetbrains.kotlin.plugin.compose")
   }
   
   android {
       namespace = "com.example.hellotv"
       compileSdk = 35
       defaultConfig {
           applicationId = "com.example.hellotv"
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

7. **Write `app/src/main/AndroidManifest.xml`.** `LEANBACK_LAUNCHER` puts the app on the TV's home screen. `android:banner` is the tile it shows there. Touchscreen is marked not required, because a TV has none.

   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <manifest xmlns:android="http://schemas.android.com/apk/res/android">
       <uses-feature android:name="android.software.leanback" android:required="false" />
       <uses-feature android:name="android.hardware.touchscreen" android:required="false" />
   
       <application
           android:banner="@drawable/banner"
           android:label="Hello TV"
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

8. **Write `app/src/main/res/drawable/banner.xml`.** A plain coloured tile for now.

   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <!-- The 320x180 dp tile the TV launcher shows. Swap for a PNG with your app's name on it. -->
   <shape xmlns:android="http://schemas.android.com/apk/res/android">
       <solid android:color="#0B3D4C" />
       <size android:width="320dp" android:height="180dp" />
   </shape>
   ```

9. **Write `app/src/main/java/com/example/hellotv/MainActivity.kt`.** Three buttons you move between with the remote. It logs a timestamp when the screen is ready. Lesson 6 builds on that.

   ```kotlin
   package com.example.hellotv
   
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
   import androidx.compose.ui.Modifier
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
                       Row(Modifier.padding(48.dp), horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                           listOf("One", "Two", "Three").forEach { label ->
                               Button(onClick = { Log.i("HelloTvTiming", "click $label uptime=${SystemClock.uptimeMillis()}") }) {
                                   Text(label)
                               }
                           }
                       }
                       LaunchedEffect(Unit) { Log.i("HelloTvTiming", "ready uptime=${SystemClock.uptimeMillis()}") }
                   }
               }
           }
       }
   }
   ```

10. **Point the build at your SDK and make the wrapper.**

    ```bash
    echo "sdk.dir=$HOME/android" > local.properties
    gradle wrapper --gradle-version 8.11.1
    ```

11. **Build.**

    ```bash
    ./gradlew assembleRelease
    ```

    The APK is `app/build/outputs/apk/release/app-release.apk`, about 0.8 MB.

12. **Check the TV will list it.** `aapt2` comes with the build tools.

    ```bash
    ~/android/build-tools/35.0.0/aapt2 dump badging app/build/outputs/apk/release/app-release.apk | grep leanback
    ```

    You should see a `leanback-launchable-activity` line.

13. **Install and start it.** (untested with this scaffold. The same two commands were run many times with Kev TV.)

    ```bash
    adb -s 192.168.1.x:5555 install -r app/build/outputs/apk/release/app-release.apk
    adb -s 192.168.1.x:5555 shell am start -n com.example.hellotv/.MainActivity
    ```

## Gotchas

- Keep the same signing key for every build. `adb install -r` refuses an APK signed with a different key. The only way round that is to uninstall, which deletes the app's data.
- An app with no `android:banner` still installs. Some launchers then show a blank tile. (untested)
- Compose for TV's `Button` and `Card` show D-pad focus for you. Plain Compose `clickable` shows little or no focus on a TV, so use the `tv-material` components.
- The build may print `Warning: SDK processing. This version only understands SDK XML versions up to 3`. It's harmless. The build still finishes.
- Builds use a lot of memory. On a shared machine, cap them. We used `nice -n 10 systemd-run --user --scope -q -p MemoryMax=16G ./gradlew assembleRelease`.

## Notes

Tested on 8 Nov 2026 on Linux with Temurin JDK 17.0.21, Gradle 8.11.1, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, Compose BOM 2024.12.01 and tv-material 1.0.0.

- Steps 2 to 12 were run as written, twice: once during the build, and again from this lesson's text while writing it. Both gave a release APK of about 0.8 MB with a `leanback-launchable-activity` line.
- Step 1 was run with the same `sdkmanager` command, into a project folder instead of `~/android`.
- Step 13 was not run with this scaffold. We didn't want a test app on a TV other people use. The same commands were run many times with Kev TV.

## Links

- [Compose for TV](https://developer.android.com/training/tv/playback/compose)
- [Get started with TV apps (manifest, banner, leanback)](https://developer.android.com/training/tv/get-started/create)
- [Gradle wrapper](https://docs.gradle.org/current/userguide/gradle_wrapper.html)
