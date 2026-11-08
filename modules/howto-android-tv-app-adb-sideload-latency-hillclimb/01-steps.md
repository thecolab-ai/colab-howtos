# Have a coding agent build an Android TV app in Kotlin, sideload it over ADB, and hill-climb it

## What it does

Give a coding agent such as Claude Code or Codex a written brief, a headless Android toolchain and ADB access to a real TV. It builds a Kotlin app with Jetpack Compose for TV, installs it over the network, reads the screen to check its own work, and then improves one measured number in a loop.

You don't write the app. You write the brief and the rules, set up the tools, and steer. The agent writes the code, builds it, installs it, starts it, and reads the log and the screen layout to see what happened. When the app works, you give it one number to improve. It changes one thing at a time and keeps only what measurably helps.

The lessons:

1. The method in short (this lesson).
2. Write the brief, and steer the agent with a file.
3. Rules for a shared TV.
4. Give the agent a toolchain it can run headless.
5. Turn on network debugging and connect with ADB.
6. Scaffold a Compose for TV app in Kotlin.
7. The agent's loop: build, install, launch, read the screen.
8. Measure a number on the real TV.
9. Hill-climb the number.
10. Example run: what the agent built and what went wrong.
11. Optional: if your app talks to a server, Tailscale and pairing over ADB.

The lessons use one example: an always-on dashboard app. All the numbers come from our run on an Nvidia Shield TV with Android 11.

## What you need

- An Android TV device: Nvidia Shield, Google TV Streamer, Chromecast with Google TV, or a TV with Android TV built in.
- A computer on the same network as the TV. It runs `adb`.
- A coding agent that can run shell commands, such as Claude Code or Codex.
- About 2.5 GB of disk for the JDK, the Android SDK parts and the Gradle cache. You don't need Android Studio or admin rights.

![The setup: the agent builds the app, one home machine runs adb and talks to the TV](./assets/diagram-setup.png)

The agent can run on any computer. Pick one machine on the TV's network to run adb, and send every install and every measurement through it. In our run the agent built on a separate server and reached that machine over SSH.

## Steps

This is the short version. Each step points to the lesson with the detail.

1. Turn on network debugging on the TV and note its address, for example `192.168.1.x:5555` (lesson 5). (untested)
2. Install JDK 17, the Android command-line tools and Platform-Tools into one folder (lesson 4).

   ```bash
   sdkmanager --sdk_root="$HOME/android" "platform-tools" "platforms;android-35" "build-tools;35.0.0"
   ```

3. Connect to the TV. Accept the prompt on the TV the first time (lesson 5). (untested: the prompt. Ours was already accepted, so only `adb connect` ran.)

   ```bash
   adb connect 192.168.1.x:5555
   ```

4. Make a project folder with the agent's working files (lesson 2). (untested)

   ```bash
   mkdir tv-app && cd tv-app && touch BRIEF.md FACTS.md PROGRESS.md STEER.md
   ```

5. Fill in `BRIEF.md` from the template in lesson 2. Paste in the rules from lesson 3. (untested)
6. Start your agent in the folder and give it this prompt: "Read BRIEF.md and do it. Log to PROGRESS.md. Re-read STEER.md at every checkpoint." (untested)
7. Let it scaffold, build, install and check the app on the TV (lessons 6 and 7). Read `PROGRESS.md` while it works. Write a note at the top of `STEER.md` to change its course.
8. When the app works, give it one number to improve and the measuring rules (lessons 8 and 9).
9. Review the commits and the results file. Turn network debugging off when you're done (lesson 5). (untested: turning network debugging off)

## Gotchas

- **Measure on the real TV.** In our run the TV had animations turned off in its developer settings. The app looked frozen on the TV, at about 1 frame a second. An emulator would not have shown that (lesson 10).
- **Give the app a demo mode** with made-up data and public test content. Then every screenshot and measurement is safe to share and the same from run to run.
- **One adb machine.** Two adb servers connected to the same TV bump each other off.
- **`adb install -r` keeps the app's data. `adb uninstall` deletes it.** Never uninstall an app the agent didn't install.
- **A missing number is not a fast number.** In our run a dead test stream made one build look faster than it was (lesson 9).
- **Noise is bigger than most changes.** Two builds of the same code, minutes apart, differed by 3 to 4 times on some streams (lesson 9).

## Notes

Status of this module: `draft`.

Run on 8 Nov 2026, on Linux, with Temurin JDK 17.0.21, Android command-line tools 22.0, Platform-Tools 37.0.1, Gradle 8.11.1, Android Gradle Plugin 8.7.3 and Kotlin 2.0.21. The TV was an Nvidia Shield TV on Android 11 (API 30), over network debugging on port 5555. The agent was Claude Code, running unattended for several hours.

What was run:

- The toolchain install, the build, `adb connect`, `adb install -r`, launching, logcat, screenshots, reading the screen layout, the measuring script and three baseline builds.
- The steer file: the agent re-read it at checkpoints and changed course several times.

What was not run, and why:

- The TV menus for developer options and network debugging, and the first prompt on the TV (step 3). They were already set up when the run started.
- Turning network debugging off (step 9).
- Pairing a Google TV device. We had none.
- Any keep-or-revert hill-climb round. The run was stopped after the baselines so the app could go live.
- Steps 4, 5 and 6 as written. In our run the brief was the agent's first prompt, not a file. `FACTS.md`, `PROGRESS.md` and `STEER.md` were used as described.
- Each lesson lists its own tested and untested steps.

The idea comes from the 2026-W45 recap. Jake shared that an agent took his app's stream switch time on a Google TV Streamer from 1.85 s to 0.84 s overnight.

## Links

- [Android Debug Bridge (adb)](https://developer.android.com/tools/adb)
- [Android Studio downloads (command line tools)](https://developer.android.com/studio#command-line-tools-only)
- [Compose for TV](https://developer.android.com/training/tv/playback/compose)
- [Android TV developer guides](https://developer.android.com/training/tv)
- [Run apps on a hardware device](https://developer.android.com/studio/run/device)
