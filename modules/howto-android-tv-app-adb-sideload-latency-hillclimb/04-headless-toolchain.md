# Give the agent a toolchain it can run headless

The agent can't click through Android Studio. It needs tools it can run from a shell: a JDK, the Android command-line tools with `sdkmanager`, Platform-Tools for `adb`, and Gradle. Put them all in the project folder. Then nothing needs admin rights, and deleting the folder removes everything.

The layout we used:

```
tv-app/
  tools/        JDK 17 and Gradle
  sdk/          Android SDK: cmdline-tools, platform-tools, platforms, build-tools
  gradle-home/  Gradle's cache
  env.sh        sets the paths; the agent sources it before every build
```

## Steps

Run these in the project folder. The commands are for Linux on x64. On macOS use the macOS downloads, and `shasum -a 256` instead of `sha256sum`.

1. Download the Temurin JDK 17 `.tar.gz` for your OS from Adoptium (link below). Check it against the SHA-256 listed next to the download.

   ```bash
   sha256sum OpenJDK17U-jdk_x64_linux_hotspot_*.tar.gz
   ```

2. Unpack it into `tools/`.

   ```bash
   mkdir -p tools && tar -xzf OpenJDK17U-jdk_x64_linux_hotspot_*.tar.gz -C tools
   ```

3. Download **Command line tools only** from the Android Studio download page. Check it against the SHA-256 on that page.

   ```bash
   sha256sum commandlinetools-linux-*_latest.zip
   ```

4. Unpack it to `sdk/cmdline-tools/latest`. `sdkmanager` expects that exact path.

   ```bash
   mkdir -p sdk/cmdline-tools
   unzip -q commandlinetools-linux-*_latest.zip -d sdk/cmdline-tools
   mv sdk/cmdline-tools/cmdline-tools sdk/cmdline-tools/latest
   ```

5. Download Gradle 8.11.1 (the `-bin.zip`) and check it against the SHA-256 Gradle publishes for it. Unpack it into `tools/`.

   ```bash
   sha256sum gradle-8.11.1-bin.zip
   unzip -q gradle-8.11.1-bin.zip -d tools
   ```

6. Write `env.sh` with absolute paths. Change `/home/you/tv-app` to your folder and the JDK folder name to the one you unpacked.

   ```bash
   export JAVA_HOME=/home/you/tv-app/tools/jdk-17.0.21+9
   export ANDROID_HOME=/home/you/tv-app/sdk
   export ANDROID_SDK_ROOT=$ANDROID_HOME
   export GRADLE_USER_HOME=/home/you/tv-app/gradle-home
   export PATH=$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:/home/you/tv-app/tools/gradle-8.11.1/bin:$PATH
   # Linux only: lets `systemd-run --user` (step 11) reach your user session from a non-login shell.
   export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
   export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}
   ```

7. Load it.

   ```bash
   . ./env.sh
   ```

8. Accept the SDK licences. Read them first if you haven't before. (untested as written: our licences were accepted, but the command was not logged)

   ```bash
   sdkmanager --sdk_root="$ANDROID_HOME" --licenses
   ```

9. Install Platform-Tools, one Android platform and the build tools. `sdkmanager` checks each download against Google's checksums.

   ```bash
   sdkmanager --sdk_root="$ANDROID_HOME" "platform-tools" "platforms;android-35" "build-tools;35.0.0"
   ```

10. Check `adb` works. (untested as written)

    ```bash
    adb version
    ```

11. On a shared Linux machine, cap the build's memory and priority. Give the agent this exact build command.

    ```bash
    nice -n 10 systemd-run --user --scope -q -p MemoryMax=16G ./gradlew assembleRelease
    ```

## Gotchas

- Source `env.sh` in every new shell. An agent's shell often starts fresh for each command, so put `. ./env.sh &&` in front of build commands, or in the agent's build script.
- If `systemd-run --user` says `Failed to connect to bus`, the shell has no `XDG_RUNTIME_DIR` or `DBUS_SESSION_BUS_ADDRESS`. An agent's shell is often not a login shell, so it lacks them. The last two lines of `env.sh` set them. `/run/user/<your uid>` only exists while you have a session on the machine, or with lingering on (`loginctl enable-linger`).
- The first build downloads plugins and libraries from Google's Maven and Maven Central. The agent needs internet for that. Later builds use the cache in `gradle-home/`.
- Skip the emulator. We installed an Android TV emulator image, then dropped it and measured on the real TV. The emulator and its system images took about 4.7 GB.
- The build may print `Warning: SDK processing. This version only understands SDK XML versions up to 3`. It's harmless.
- No `sudo`. If a step seems to need it, the tool is going in the wrong place.

## Notes

Run on 8 Nov 2026 on Linux x64, by the agent, in its own folder. Temurin JDK 17.0.21, command-line tools 22.0, Platform-Tools 37.0.1, Gradle 8.11.1. The JDK, the command-line tools and Gradle were each checked against their published SHA-256 before unpacking. Steps 1 to 7, 9 and 11 match what ran, apart from file and folder names and the two session-bus lines in `env.sh`. Those were added after review. We checked them on Linux with systemd 255: from a shell without them, `systemd-run --user --scope -q true` failed with `Failed to connect to bus`, and with them it worked. We have not run a full build with this exact `env.sh`. Steps 8 and 10 are marked untested because their commands were not logged.

Sizes after a few days of builds: the SDK 635 MB, the JDK plus Gradle 464 MB, and the Gradle cache 1.4 GB.

## Links

- [Eclipse Temurin downloads (Adoptium)](https://adoptium.net/temurin/releases/)
- [Android Studio downloads (command line tools)](https://developer.android.com/studio#command-line-tools-only)
- [sdkmanager](https://developer.android.com/tools/sdkmanager)
- [SDK Platform-Tools release notes](https://developer.android.com/tools/releases/platform-tools)
- [Gradle releases and checksums](https://gradle.org/release-checksums/)
- [systemd-run](https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html)
