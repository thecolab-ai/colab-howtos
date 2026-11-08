# Turn on network debugging and connect with ADB

The agent installs and checks the app over the network with ADB. That needs two switches on the TV: developer options, then network debugging. A Shield uses a fixed port. Google TV devices pair with a code first.

You do this part by hand, once. The agent can't press buttons on the TV's settings screens, and it shouldn't.

## Turn on developer options

1. Open **Settings**, then **Device Preferences**, then **About**. (untested)
2. Scroll to **Build** and click it seven times. A message says you're now a developer. (untested)
3. Go back one level. **Developer options** is now in the list. (untested)

Menu names move between devices and versions. On Google TV the path is usually **Settings**, **System**, **About**, then **Android TV OS build**. If you can't find it, search the TV's settings for "build".

## Nvidia Shield and older Android TV: `adb connect`

1. Open **Developer options** and turn on **Network debugging**. (untested)
2. The screen shows the TV's address and port, for example `192.168.1.x:5555`. (untested)
3. Connect from the adb machine.

   ```bash
   adb connect 192.168.1.x:5555
   ```

4. Accept the prompt on the TV, with **Always allow from this computer** ticked. (untested)
5. Check the TV shows as `device`, not `unauthorized`. (untested)

   ```bash
   adb devices -l
   ```

## Google TV: `adb pair`, then `adb connect`

Newer Google TV devices, including the Google TV Streamer, use **Wireless debugging**. You pair once with a one-time code. We had no Google TV device to test on. These steps follow the Android docs.

1. In **Developer options**, turn on **Wireless debugging** and open it. (untested)
2. Choose **Pair device with pairing code**. The TV shows a six-digit code and an address with a port, for example `192.168.1.x:37123`. (untested)
3. Pair with that address. Type the code when asked. (untested)

   ```bash
   adb pair 192.168.1.x:37123
   ```

4. Back on the Wireless debugging screen, note the **IP address and port**. This port is not the pairing port. Connect to it. (untested)

   ```bash
   adb connect 192.168.1.x:41234
   ```

The connect port can change after a reboot, or when you turn wireless debugging off and on. Check the screen again if `adb connect` fails.

## Reserve the TV's address on your router

The agent needs the same address every time. In your router's DHCP or LAN settings, add a reservation (sometimes called a static lease) for the TV. Every router names this differently, so check its manual.

Then put the address in the brief, and tell the agent to pass `-s <address>` on every adb command.

## Troubleshooting

- **`unauthorized`**: the TV hasn't accepted the computer's key. Look for the prompt on the TV. (untested: run `adb kill-server`, then connect again, to get a fresh prompt.)
- **`more than one device/emulator`**: pass `-s 192.168.1.x:5555` on every command.
- **`failed to connect` or a timeout**: the TV is asleep, on another network, or has a new address. Wake it with the remote. Check the address in Developer options.
- **It worked and then stopped**: the TV may have restarted or got a new address. Reserve its address.
- **New computer**: adb keeps its key in `~/.android/adbkey`. A new computer, or a deleted key, means a new prompt on the TV.
- **Two adb servers**: a laptop and a desktop connected at once can bump each other off. Pick one machine.

## Security

Network debugging gives a full shell on the TV to any computer it trusts. Treat it like a house key.

- Only accept the prompt for computers you own. Say no to a prompt you didn't expect.
- Never forward port 5555, or the wireless debugging ports, on your router.
- **Revoke debugging authorizations** in Developer options forgets every trusted computer. Use it if a computer is lost or the project ends.
- Turn network debugging off when you're done. Your app keeps working without it.
- Put visitors on guest Wi-Fi, so their devices can't reach the TV's debug port.

## Notes

On 8 Nov 2026 the Shield (Android 11) already had network debugging on, and the adb machine was already trusted. So only `adb connect` was run, many times. The menu steps, the first prompt, `adb devices -l`, `adb kill-server` and the Google TV pairing flow were not run. They follow the Android and Nvidia docs, so check them on your device.

## Links

- [Android Debug Bridge: connect over Wi-Fi](https://developer.android.com/tools/adb#connect-to-a-device-over-wi-fi)
- [Configure on-device developer options](https://developer.android.com/studio/debug/dev-options)
- [Run apps on a hardware device](https://developer.android.com/studio/run/device)
