# Keep a shared TV safe while an agent works on it

The TV in the lounge belongs to everyone in the house. An agent with ADB can install apps, change settings and take screenshots. So set the rules before it starts, and put them in the prompt.

## Rules we gave the agent

1. **Only touch your own app.** Install and update it with `adb install -r`. Never uninstall, disable or update another app, the launcher, or anything the household uses.
2. **Never change settings.** That includes developer settings like animation scale. Our TV had animations off, and the first build looked frozen. The fix went into the app, not the TV's settings (lesson 4).
3. **Check who's watching.** Before each measuring run, check which app is in front. If it's not your app, the home screen or the screensaver, someone is using the TV. Wait 10 minutes and check again. If the command prints nothing, treat that as "someone might be watching" too. (Checked on Android 11 only.)

   ```bash
   adb -s 192.168.1.x:5555 shell dumpsys activity activities | grep -m1 -E "topResumedActivity|mResumedActivity"
   ```

4. **Leave it how you found it.** Go back to the home screen at the end. (untested)

   ```bash
   adb -s 192.168.1.x:5555 shell input keyevent KEYCODE_HOME
   ```

   Also undo anything your app saved for testing. Kev TV keeps the page dwell time, so a run that set it to 600 s has to set it back.

5. **Only capture demo data.** Run the app in demo mode for anything you capture or share. A real dashboard shows calendars, messages and cameras. A screenshot of it is household data.
6. **Shrink screenshots before an agent reads them.** A 4K capture is large and slow. We scaled ours to 1280x720.
7. **One adb machine.** Run every adb command from one home machine. If the agent works on another computer, it reaches that machine over SSH. It never runs `adb connect` from anywhere else.
8. **Builds go in one folder.** Copy each APK to one folder on the home machine and install from there. Delete the folder when the project ends.

## Keep the app itself safe

- **Pair with a short-lived link.** Use a one-time pairing link that expires (lesson 5). Store whatever the app gets back in private, encrypted storage (the Android Keystore), turn app backup off, and never log it.
- **Show, don't act.** A wall display only needs to read. Give it the least access your server allows.
- **Private network only.** Reach the server over a private network like Tailscale, not the open internet. Refuse plain `http://` addresses anywhere else.
- **Look after the screen.** A dashboard stays on for hours. Kev TV shifts its content a few pixels every 3 minutes, avoids big white blocks, and dims from 23:00 to 06:00 after 10 quiet minutes.

## Turn it off when you're done

- Turn **Network debugging** off in Developer options when the project is finished. The app keeps working.
- Use **Revoke debugging authorizations** if a trusted computer is gone.
- Never forward ADB ports on your router. ADB should never be reachable from the internet.

## Notes

These are the rules Adam's agent worked under on 8 Nov 2026, on a TV the household uses every day. Rules 1 to 3 and 5 to 7 are in the scripts it ran: install with `-r` only, check the front app before each run, demo mode for every measurement and screenshot, screenshots scaled to 1280x720, every adb command through one home machine. We have no record of the final `KEYCODE_HOME` press in this build. The APK folder on the home machine was still in use when this lesson was written.

## Links

- [Android Debug Bridge (adb)](https://developer.android.com/tools/adb)
- [Android Keystore system](https://developer.android.com/privacy-and-security/keystore)
- [Back up user data with Auto Backup](https://developer.android.com/identity/data/autobackup)
