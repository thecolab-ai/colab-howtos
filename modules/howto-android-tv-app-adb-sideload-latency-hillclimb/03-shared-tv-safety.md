# Rules for a shared TV

A TV in a shared room belongs to everyone who uses it. An agent with ADB can install apps, change settings and take screenshots. So set the rules before it starts, and put them in the brief.

## Rules to paste into the brief

```markdown
## TV rules
1. Only touch our app (com.example.tv). Install it with `adb install -r`.
   Never uninstall, disable or update any other app, including the launcher.
2. Never change a setting on the TV, developer settings included.
   If a setting gets in the way, fix it inside our app.
3. Before each measuring run, check which app is in front. If it is not
   our app, the home screen or the screensaver, someone is using the TV:
   wait 10 minutes and check again. If the check prints nothing, wait too.
4. Waking the TV from its screensaver is fine (KEYCODE_WAKEUP).
5. At the end, put back anything our app saved for testing, then press
   Home. Only do this if the TV is still free. Do it on exit too.
6. Screenshots and measurements use demo mode only. Scale screenshots
   to 1280x720 before reading them.
7. Every adb command goes through one machine.
8. APKs go in one folder on that machine. Delete it when the project ends.
```

## Why each rule

1. **Your app only.** `adb install -r` replaces your app and keeps its data. `adb uninstall` deletes data. Other apps belong to other people.
2. **No settings.** Our TV had animations turned off in its developer settings. Our app looked frozen. The agent fixed it inside the app, and the TV's setting stayed as it was (lesson 10).
3. **Check who's watching.** This is the check our run used. Android 11 and 12 print `mResumedActivity`. Android 13 and later print `topResumedActivity` instead, so match both.

   ```bash
   adb -s 192.168.1.x:5555 shell dumpsys activity activities | grep -m1 -E "topResumedActivity|mResumedActivity"
   ```

   An empty result means "can't tell", so treat it as "someone might be watching". A TV that is asleep can print nothing here. The script then waits, which is the safe side. Wake the TV with the remote if you want the run to go on.

4. **Waking is fine.** `KEYCODE_WAKEUP` ends the screensaver. It changes no settings.

   ```bash
   adb -s 192.168.1.x:5555 shell input keyevent KEYCODE_WAKEUP
   ```

5. **Leave it how you found it.** Test runs often change something the app saves, such as how long each page shows. Set it back, then go to the home screen. (untested)

   ```bash
   adb -s 192.168.1.x:5555 shell input keyevent KEYCODE_HOME
   ```

   Check the TV is still free first. If someone started watching during the run, pressing Home throws them out. Lesson 9's script runs this clean-up from a `trap`, so it also happens when the run stops early.

6. **Demo data only.** A real dashboard shows calendars, messages and video. A screenshot of it is private data. Demo mode with made-up data is safe to capture and share.
7. **One adb machine.** Two adb servers connected to the same TV bump each other off. If the agent works on another computer, it reaches the adb machine over SSH. It never runs `adb connect` from anywhere else.
8. **One APK folder.** Then you know what to clean up.

## Keep the app itself safe

- **Pair with a short-lived link.** If the app talks to a server, use a one-time pairing link that expires (lesson 11). Store what the app gets back in private storage, encrypted with a key held in the Android Keystore. Turn app backup off. Never log it.
- **Show, don't act.** A wall display only needs to read. Give it the least access your server allows.
- **Private network only.** Reach the server over a private network like Tailscale, not the open internet. Refuse plain `http://` addresses anywhere else.
- **Look after the screen.** A dashboard stays on for hours. Our example app shifts its content a few pixels every 3 minutes, avoids big white blocks, and dims at night after 10 quiet minutes.

## Turn it off when you're done

- Turn **Network debugging** off in Developer options when the project ends. The app keeps working.
- Use **Revoke debugging authorizations** if a trusted computer is gone.
- Never forward ADB ports on your router. ADB should never be reachable from the internet.

## Notes

These are the rules our agent worked under on 8 Nov 2026, on a TV other people use every day. Rules 1 to 4 and 6 to 7 are in the scripts it ran: install with `-r` only, check the front app before each run, wake the screensaver, demo mode for every measurement and screenshot, screenshots scaled to 1280x720, every adb command through one machine. The front-app check paused one run when another app was in front.

Not run: the Android 13 and later match (`topResumedActivity`), and the end-of-run clean-up in rule 5. Our run stopped without a final Home press. The note about a sleeping TV comes from reading the check, not from a test.

## Links

- [Android Debug Bridge (adb)](https://developer.android.com/tools/adb)
- [Android Keystore system](https://developer.android.com/privacy-and-security/keystore)
- [Back up user data with Auto Backup](https://developer.android.com/identity/data/autobackup)
