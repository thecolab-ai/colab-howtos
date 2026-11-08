# Put the TV on Tailscale and pair your app over ADB

Your app may need to reach a server that isn't on your home network, such as an agent running on a cloud box. A private network like Tailscale fixes that without opening anything to the internet.

A TV makes setup awkward. You can't type a long login code or pairing link with a remote. This lesson does all of it from a computer with ADB: install Tailscale, accept the VPN prompt, get the login link, and paste a pairing link into your app.

All the steps here were run by hand on 8 Nov 2026 on an Nvidia Shield TV with Android 11, unless marked untested.

## What you need

- ADB connected to the TV (lessons 1 and 2).
- A Tailscale account, and your server already on your tailnet.
- A phone or laptop to approve the login.
- The Tailscale Android app as an APK file, or the Play Store on the TV.

## Install Tailscale and log in

1. Install Tailscale. We sideloaded the APK, version 1.104.5. You can install it from the Play Store on the TV instead. (Play Store route untested.)

   ```bash
   adb -s 192.168.1.x:5555 install tailscale.apk
   ```

2. Start it. `monkey` with the TV launcher category opens the app's TV activity.

   ```bash
   adb -s 192.168.1.x:5555 shell monkey -p com.tailscale.ipn -c android.intent.category.LEANBACK_LAUNCHER 1
   ```

3. Android shows a VPN consent dialog ("Connection request"). Dump the screen layout to find its OK button.

   ```bash
   adb -s 192.168.1.x:5555 shell uiautomator dump /sdcard/ui.xml
   adb -s 192.168.1.x:5555 shell cat /sdcard/ui.xml
   ```

4. Find the node with `resource-id="android:id/button1"` and read its `bounds`. Ours was `[1304,691][1432,787]`.
5. Tap the middle of those bounds. For ours that is x = (1304 + 1432) / 2 = 1368 and y = (691 + 787) / 2 = 739.

   ```bash
   adb -s 192.168.1.x:5555 shell input tap 1368 739
   ```

6. Tailscale now shows a QR code and a login code. You can scan the QR code. Or get the login link from the log:

   ```bash
   adb -s 192.168.1.x:5555 logcat -d | grep -o "https://login.tailscale.com/a/[A-Za-z0-9]*"
   ```

7. Open that link on your phone or laptop and approve the device.
8. Check the TV is in your tailnet's device list. Ours showed up as "SHIELD Android TV".

## Pair your app by pasting a link

Most apps that talk to a server pair once with a code or link. Kev's server makes a one-time `kev://pair?p=...` link of about 180 characters. Nobody wants to type that with a remote.

Kev TV takes the link in a text field. Here is how to fill it from ADB. Your app's screen will differ, so read its layout first (step 2).

1. Open the app's pairing screen. Kev TV starts in demo mode, so we pressed Back twice to leave it.

   ```bash
   adb -s 192.168.1.x:5555 shell input keyevent 4
   adb -s 192.168.1.x:5555 shell input keyevent 4
   ```

2. Dump the layout and find the text field's bounds. This works for Compose apps too, because Compose exposes its semantics to `uiautomator`.

   ```bash
   adb -s 192.168.1.x:5555 shell uiautomator dump /sdcard/ui.xml
   adb -s 192.168.1.x:5555 shell cat /sdcard/ui.xml
   ```

3. Tap the middle of the text field to focus it, the same way as the VPN button.

   ```bash
   adb -s 192.168.1.x:5555 shell input tap X Y
   ```

4. Make a fresh pairing link on your server, just before you use it.
5. Type the link into the field. Put single quotes round it, and double quotes round the whole shell command.

   ```bash
   adb -s 192.168.1.x:5555 shell "input text '<link>'"
   ```

6. Press Enter. In Kev TV the field's keyboard action is Go, which runs Pair.

   ```bash
   adb -s 192.168.1.x:5555 shell input keyevent KEYCODE_ENTER
   ```

## Gotchas

- D-pad Down does not move focus out of a Compose `BasicTextField`. Use Enter, or tap something else.
- Tapping a Compose button by the bounds of its text label did nothing for us. The label's bounds cover only the text, not the button. Give your app a keyboard action (such as `ImeAction.Go`) so Enter does the job.
- `input text` treats spaces and some symbols specially. Kev's link is base64url, so it needed no escaping. A link with spaces or `&` needs more care. (untested)
- The pairing link is a secret while it's valid. It sits in your shell history and on the TV's screen for a moment. Use a short-lived, one-time link, make it just before you paste it, and never put a real one in a log, a repo or a chat.
- Kev TV only allows a plain `http://` server address if it's on the tailnet (`100.64.0.0/10` or `*.ts.net`) or loopback. Do the same, so your token never crosses the internet over plain HTTP.

## Notes

Run by hand on 8 Nov 2026 on an Nvidia Shield TV, Android 11, Tailscale 1.104.5 (sideloaded APK), adb from a Linux machine on the home network. The device list was checked with the Tailscale API. Not run: installing Tailscale from the Play Store, and `input text` with spaces or shell symbols.

## Links

- [Tailscale: install on Android](https://tailscale.com/kb/1079/install-android)
- [adb shell: input and uiautomator](https://developer.android.com/tools/adb#shellcommands)
- [Android VpnService (why the consent dialog appears)](https://developer.android.com/reference/android/net/VpnService)
