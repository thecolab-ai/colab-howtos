# The agent's loop: build, install, launch, read the screen

Nobody watches the TV while the agent works. So the agent has to check its own work: build the app, install it, start it, then read the log and the screen to see what happened. Every command here runs from a shell, so the agent can run the whole loop alone, over and over.

The loop, after every change:

1. Build and install: `./deploy.sh release`.
2. Start the app on the screen it changed.
3. Read the log.
4. Read the screen as text, and press keys to check focus.
5. Take one small screenshot of each screen it changed.
6. Commit.

## Steps

1. **Give the agent a deploy script.** It builds, copies the APK to the adb machine and installs it. It prints only compile errors, or the log's last 20 lines if it finds none, so a failed build costs the agent a few lines of context, not hundreds. If the agent runs on the adb machine, drop the `scp` and `ssh` parts.

   ```bash
   #!/usr/bin/env bash
   # deploy.sh [debug|release]: build, copy to the adb machine, install on the TV.
   set -euo pipefail
   kind=${1:-debug}
   . ./env.sh
   task=assembleDebug; [ "$kind" = release ] && task=assembleRelease
   log=$(mktemp); trap 'rm -f "$log"' EXIT
   if ! nice -n 10 ./gradlew --console=plain -q $task >"$log" 2>&1; then
     errs=$(grep -E "^e: |What went wrong" -A3 "$log" || true)
     if [ -n "$errs" ]; then head -30 <<<"$errs"; else echo "Build failed. Last lines:"; tail -20 "$log"; fi
     exit 1
   fi
   apk=app/build/outputs/apk/$kind/app-$kind.apk
   ssh adb-machine 'mkdir -p tv-apk'
   scp -q "$apk" adb-machine:tv-apk/app.apk
   ssh adb-machine 'adb connect 192.168.1.x:5555 >/dev/null; adb -s 192.168.1.x:5555 install -r tv-apk/app.apk'
   ```

   It ends with `Success` when the install worked. A failed build or a failed install makes the script fail, so the agent can't miss it.

2. **Clear the log, then start the app.** Clearing first means the log only shows this run. `-W` waits for the first frame and prints `TotalTime` in ms.

   ```bash
   A="adb -s 192.168.1.x:5555"
   $A logcat -c
   $A shell am start -W -n com.example.tv/.MainActivity
   ```

3. **Read the app's log lines.** `-d` prints the log and stops. `-s TAG:I` shows only your tag.

   ```bash
   $A logcat -d -s MyAppTiming:I
   ```

4. **Read the screen as text.** `uiautomator dump` writes the screen's layout as XML: every text, its bounds, and which node has focus. It works for Compose apps too, because Compose exposes its semantics.

   ```bash
   $A shell uiautomator dump /sdcard/ui.xml
   $A shell cat /sdcard/ui.xml | grep -o 'text="[^"]*"'
   $A shell rm /sdcard/ui.xml
   ```

5. **Press keys on the remote.** Then dump the screen again to see where focus went.

   ```bash
   $A shell input keyevent 22
   ```

   | Key | Code | Used in our run |
   |---|---|---|
   | D-pad Up | 19 | no |
   | D-pad Down | 20 | yes |
   | D-pad Left | 21 | no |
   | D-pad Right | 22 | yes |
   | OK (D-pad centre) | 23 or `KEYCODE_DPAD_CENTER` | yes |
   | Back | 4 | yes |
   | Enter | `KEYCODE_ENTER` | yes |
   | Wake from screensaver | `KEYCODE_WAKEUP` | yes |
   | Home | `KEYCODE_HOME` | no |

6. **Take a screenshot and shrink it.** `exec-out` sends the PNG straight to your computer. A 4K capture is several MB, so scale it before the agent looks at it. This needs Pillow (`pip install pillow`).

   ```bash
   $A exec-out screencap -p > shot.png
   python3 -c "from PIL import Image; Image.open('shot.png').convert('RGB').resize((1280,720)).save('shot-small.png')"
   ```

7. **Give the app test hooks.** The agent can't hold a remote, so let it jump straight to a screen. Our example app reads intent extras: `--ez demo true` starts demo mode, and `--ei page 3` shows page 3 and holds it.

   ```bash
   $A shell am start -n com.example.tv/.MainActivity --ez demo true --ei page 3
   ```

   Make the activity `singleTask` (`android:launchMode="singleTask"` in the manifest) and read the extras in both `onCreate` and `onNewIntent`. Then a second `am start` reaches the running app instead of starting a new copy. `am start` then prints "Activity not started, intent has been delivered to currently running top-most instance". That is expected.

   ```kotlin
   override fun onNewIntent(intent: Intent) {
       super.onNewIntent(intent)
       handleTestExtras(intent)
   }

   private fun handleTestExtras(intent: Intent) {
       if (intent.getBooleanExtra("demo", false)) demo.value = true
       intent.getIntExtra("page", -1).takeIf { it >= 0 }?.let { page.value = it }
   }
   ```

   Here `demo` and `page` are `mutableStateOf` values the app's UI reads. Our app's hook is longer, but works the same way.

8. **Check frames and memory on the real TV early.** These two commands found the biggest problems in our run (lesson 10).

   ```bash
   $A shell dumpsys gfxinfo com.example.tv reset
   sleep 30
   $A shell dumpsys gfxinfo com.example.tv
   $A shell dumpsys meminfo com.example.tv
   ```

   `gfxinfo` prints the frames drawn and the share that were janky since the reset. `meminfo` prints the app's memory, with `TOTAL PSS` near the bottom.

9. **Commit the change** once the loop passes. One change per commit.

## A prompt for the loop

Put this in the brief, or in a steer note:

```markdown
After every change: run ./deploy.sh release. Start the app on the screen you
changed. Read logcat for our tag and dump the screen with uiautomator. Press
D-pad keys and dump again to check focus moves where it should. Take one
1280x720 screenshot per changed screen, in demo mode only. If all is well,
commit with a message that says why. Log what you checked in PROGRESS.md.
```

## Gotchas

- **Measure on release builds.** Debug builds are slower, and their numbers don't carry over.
- **Tapping a Compose button by its text did nothing for us.** The text node's bounds cover only the label, not the button. Give screens a key path instead: focus plus OK or Enter.
- **D-pad Down does not move focus out of a Compose `BasicTextField`.** Use Enter, or give the field a keyboard action such as `ImeAction.Go`.
- **The dump only shows what Compose exposes.** Text you draw yourself on a `Canvas` won't be there. Give such parts a `contentDescription`.
- **`logcat -c` clears the TV's whole log.** That's fine on your own TV.
- **Delete the dump file.** `/sdcard/ui.xml` stays on the TV until you remove it.
- **A paused or sleeping screen draws no frames.** Wake the TV before you measure (lesson 3).

## Notes

Run on 8 Nov 2026 against an Nvidia Shield TV on Android 11, from a Linux adb machine on the same network. Steps 1 to 6 and 8 were run many times, by the agent through its scripts and by hand. The key codes marked "no" in the table were not used. Our deploy script also capped the build's memory (lesson 4). After review we changed the script in three ways that have not run against a TV: it fails when the install fails (the run's version piped the install through `tail -1`, which hid the error), it handles a failed build with no matching error lines, and it makes the `tv-apk` folder on the adb machine. We checked those paths with stub `gradlew`, `scp` and `ssh` commands. The `handleTestExtras` code in step 7 is a short sketch of the hook our app used. We compiled it in the lesson 6 scaffold, but it hasn't run on a TV in this form. The loop prompt is a summary of how the agent worked, not the exact words.

## Links

- [adb shell commands: am, input, screencap](https://developer.android.com/tools/adb#shellcommands)
- [Logcat command-line tool](https://developer.android.com/tools/logcat)
- [UI Automator](https://developer.android.com/training/testing/other-components/ui-automator)
- [Inspect GPU rendering speed (gfxinfo)](https://developer.android.com/topic/performance/rendering/inspect-gpu-rendering)
- [dumpsys meminfo](https://developer.android.com/tools/dumpsys#meminfo)
- [Semantics in Compose](https://developer.android.com/develop/ui/compose/accessibility/semantics)
