# Optional: if your app talks to a server, Tailscale and pairing over ADB

Skip this lesson if your app only uses public data. Read it if your app needs a server that isn't on the TV's network. A private network such as Tailscale lets the TV reach that server without opening anything to the internet.

A TV makes this setup awkward. You can't type a long login code or a pairing link with a remote. This lesson does it all from the adb machine: install Tailscale, accept the VPN prompt, get the login link, and paste a pairing link into your app.

We ran the Tailscale steps by hand on 8 Nov 2026 on an Nvidia Shield TV with Android 11. Steps not run are marked untested.

## What you need

- ADB connected to the TV (lesson 5).
- A Tailscale account, with your server already on it.
- A phone or laptop to approve the TV's login.
- The Tailscale Android app as an APK file, or the Play Store on the TV.

## Install Tailscale and log in

1. Install Tailscale. We sideloaded the APK, version 1.104.5. You can install it from the Play Store on the TV instead. (Play Store route untested.)

   ```bash
   adb -s 192.168.1.x:5555 install tailscale.apk
   ```

2. Start it. `monkey` with the TV launcher category opens the app's TV screen.

   ```bash
   adb -s 192.168.1.x:5555 shell monkey -p com.tailscale.ipn -c android.intent.category.LEANBACK_LAUNCHER 1
   ```

3. Android shows a VPN dialog, "Connection request". Dump the screen to find its OK button.

   ```bash
   adb -s 192.168.1.x:5555 shell uiautomator dump /sdcard/ui.xml
   adb -s 192.168.1.x:5555 shell cat /sdcard/ui.xml
   adb -s 192.168.1.x:5555 shell rm /sdcard/ui.xml
   ```

4. Find the node with `resource-id="android:id/button1"` and read its `bounds`. Ours was `[1304,691][1432,787]`.
5. Tap the middle of those bounds. For ours that is x = (1304 + 1432) / 2 = 1368 and y = (691 + 787) / 2 = 739.

   ```bash
   adb -s 192.168.1.x:5555 shell input tap 1368 739
   ```

6. Tailscale now shows a QR code and a login code. Scan the QR code with your phone. Or get the login link from the log:

   ```bash
   adb -s 192.168.1.x:5555 logcat -d | grep -o "https://login.tailscale.com/a/[A-Za-z0-9]*"
   ```

7. Open that link on your phone or laptop and approve the TV.
8. Check the TV is in your Tailscale device list. Ours showed up as "SHIELD Android TV".

## Pair your app by pasting a link

Many apps that talk to a server pair once, with a code or a link. A long link is hard to type with a remote, so paste it from the adb machine. Your app's pairing screen will differ from ours, so read its layout first. (untested as written: our app's pairing screen and server are not part of this module.)

1. Open your app's pairing screen. (untested)
2. Dump the layout and find the text field's `bounds`. (untested)

   ```bash
   adb -s 192.168.1.x:5555 shell uiautomator dump /sdcard/ui.xml
   adb -s 192.168.1.x:5555 shell cat /sdcard/ui.xml
   adb -s 192.168.1.x:5555 shell rm /sdcard/ui.xml
   ```

3. Tap the middle of the text field to focus it, the same way as the VPN button. (untested)

   ```bash
   adb -s 192.168.1.x:5555 shell input tap X Y
   ```

4. Make a fresh, one-time pairing link on your server, just before you use it. (untested)
5. Type it into the field. Put single quotes round it, and double quotes round the whole shell command. (untested)

   ```bash
   adb -s 192.168.1.x:5555 shell "input text '<pairing-link>'"
   ```

6. Press Enter. (untested)

   ```bash
   adb -s 192.168.1.x:5555 shell input keyevent KEYCODE_ENTER
   ```

For step 6 to work, give the field a keyboard action that submits, such as `ImeAction.Go` with a `KeyboardActions(onGo = { pair() })`. Then Enter does the job, and the agent never has to find the Pair button.

## Gotchas

- D-pad Down does not move focus out of a Compose `BasicTextField`. Use Enter, or tap something else.
- Tapping a Compose button by the bounds of its text label did nothing in our run. The label's bounds cover only the text, not the button. A keyboard action avoids the problem.
- `input text` treats spaces and some symbols specially. A link with spaces, `&` or `%` needs escaping. (untested)
- A pairing link is a secret while it's valid. It sits in your shell history, and on the TV's screen for a moment. Use a short-lived, one-time link. Make it just before you paste it. Never put a real one in a log, a repo, a steer note or a chat with the agent.
- Only let the app use a plain `http://` server address on your private network, so nothing secret crosses the internet unencrypted.
- The VPN dialog's position depends on the screen size. Read the bounds on your own TV. Don't reuse ours.

## Notes

Steps 1 to 8 of the Tailscale part were run by hand on 8 Nov 2026 on an Nvidia Shield TV with Android 11, Tailscale 1.104.5 (sideloaded APK), with adb on a Linux machine on the same network. The device list was checked in the Tailscale admin console. Not run: the Play Store install, and `input text` with spaces or shell symbols. The pairing steps are written generically, so they are all marked untested. The same commands (`uiautomator dump`, `input tap`, `input text`, `KEYCODE_ENTER`) were used in our run.

## Links

- [Tailscale: install on Android](https://tailscale.com/kb/1079/install-android)
- [adb shell: input and uiautomator](https://developer.android.com/tools/adb#shellcommands)
- [Android VpnService (why the dialog appears)](https://developer.android.com/reference/android/net/VpnService)
- [Keyboard actions in Compose](https://developer.android.com/develop/ui/compose/text/user-input#keyboard-options)
