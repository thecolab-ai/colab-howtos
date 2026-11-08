# Measure time to first frame

To improve a number in a loop, the agent has to read that number off the real TV, the same way every time. We measured the time from picking a camera to its first video frame on screen. The app writes two timestamps to the Android log, and a script reads them over ADB.

## The two timestamps

1. **Select.** The moment the app acts on the choice. That is OK on a camera tile, or Left or Right while a camera is full screen. The app logs `cam_select uptime=<ms>`.
2. **First frame.** Media3 ExoPlayer calls `onRenderedFirstFrame()` when the first decoded frame reaches the screen. The app logs `cam_first_frame uptime=<ms>` there.

Both use `SystemClock.uptimeMillis()`, the TV's own clock. So your computer's clock and the delay of `adb` never get into the number. Time to first frame is the second value minus the first.

```kotlin
// When a camera is chosen
Log.i("MyAppTiming", "cam_select uptime=${SystemClock.uptimeMillis()} n=$index how=$how")

// In the player listener
override fun onRenderedFirstFrame() {
    Log.i("MyAppTiming", "cam_first_frame uptime=${SystemClock.uptimeMillis()}")
}
```

Kev TV's tag was `KevTvTiming`. Use your own.

## Steps

1. Add the two log lines to your app.
2. Add a way to trigger a select from `adb`, so a script can do it without a remote. Kev TV reads an intent extra, `camera`, and opens that camera once the list has loaded. In Kev TV this only works in demo mode.

   ```bash
   adb -s 192.168.1.x:5555 shell am start -n com.example.tv/.MainActivity --ei camera 0
   ```

3. Make the activity `singleTask` (`android:launchMode="singleTask"` in the manifest). Then the extra reaches the running app through `onNewIntent`, and no second copy starts. `am start` prints a warning each time: "Activity not started, intent has been delivered to currently running top-most instance." That is expected.
4. Clear the log, trigger a select and read the log back.

   ```bash
   A="adb -s 192.168.1.x:5555"
   $A logcat -c
   $A shell am start -n com.example.tv/.MainActivity --ei camera 0
   sleep 5
   $A logcat -d -s MyAppTiming:I
   ```

5. Do the same for a switch. While a camera is full screen, Right on the remote is key event 22.

   ```bash
   $A logcat -c
   $A shell input keyevent 22
   sleep 5
   $A logcat -d -s MyAppTiming:I
   ```

6. Measure cold start as a second number. Then a change that speeds up switching but slows the app's start can't slip through.

   ```bash
   $A shell am force-stop com.example.tv
   $A shell am start -W -n com.example.tv/.MainActivity --ez demo true
   ```

   `TotalTime` in the output is the time to the app's first drawn frame, in ms.

7. Never trust one run. Each build got 7 cold starts, plus 8 or 12 selects, each followed by a switch. The script cycled through four test streams, so each stream came up two or three times per build. Use the median. Lesson 7 has the script.

## Find out where the time goes

The total says how slow it is. It doesn't say why. So we added stage logs, with no change to behaviour, from Media3's `AnalyticsListener`:

```kotlin
val analytics = object : AnalyticsListener {
    override fun onLoadCompleted(t: AnalyticsListener.EventTime, info: LoadEventInfo, data: MediaLoadData) {
        val what = when (data.dataType) {
            C.DATA_TYPE_MANIFEST -> "manifest"
            C.DATA_TYPE_MEDIA -> "media"
            else -> return
        }
        Log.i("MyAppTiming", "cam_load what=$what ms=${info.loadDurationMs} bytes=${info.bytesLoaded}")
    }

    override fun onVideoDecoderInitialized(t: AnalyticsListener.EventTime, name: String, at: Long, initMs: Long) {
        Log.i("MyAppTiming", "cam_decoder ms=$initMs")
    }
}
player.addAnalyticsListener(analytics)
```

Kev TV logs these only between a select and its first frame, and logs timings only, never stream URLs.

What the stage logs showed, on the Shield, in demo mode:

| Case | What happened | Total |
|---|---|---|
| Live test stream, a repeat visit | top playlist 311 ms, then stream playlist 590 ms, then decoder 25 ms; the rest of the wait was not broken down | about 1.6 s |
| Live test stream, first visit in a run | top playlist alone took 2,028 ms | about 3.4 s |
| Video-on-demand stream, first visit | four playlist loads of 518 to 737 ms each, mostly one after another, then 646 ms for the first video segment | about 2.6 s |
| The same stream, picked again | each load about 40 ms, from cache | about 0.3 s |

Decoder start-up was 20 to 34 ms every time. The network was nearly all of the wait. So there was no point tuning the decoder. The things worth trying were fewer, faster or earlier network loads.

## Pin what you're measuring

The loop is only fair if every build sees the same thing.

- **Fixed test streams.** Kev TV's demo mode uses four public HLS test streams: one live stream, Big Buck Bunny and Tears of Steel (both from the Blender Foundation), and Apple's bipbop example. Use streams you have the rights to.
- **A demo mode.** Measuring never touches real cameras or real data.
- **The release build.** Debug builds are slower, and their numbers don't carry over.
- **The same TV state.** The TV awake, and nothing else playing. Lesson 7's script checks which app is in front before each run.

## Gotchas

- `onRenderedFirstFrame` fires again after a seek or a new media item. Read the last `cam_first_frame` after the last `cam_select`, not the first one.
- If a stream fails, there is no first-frame line. Give each run a timeout (ours was 15 s) and record it as `NA`. Don't let a missing number count as fast. Lesson 7 shows how a dead stream made one build look better than it was.
- The first visit to a stream in a run was often 2.5 to 3.5 s. Repeat visits were usually 0.2 to 1.6 s. Report first visits apart from the rest, or one slow visit moves a small median.
- `logcat -c` clears the TV's whole log. That's fine on your own TV.
- The network and the stream's CDN are part of the number. Lesson 7 shows how much they moved it.

## Notes

This is the method behind every number in lesson 7. It was run on 8 Nov 2026 on an Nvidia Shield TV with Android 11, release builds, demo mode, from a Linux machine on the home network. The stage table comes from the instrumented build's log for that run.

## Links

- [Media3 ExoPlayer](https://developer.android.com/media/media3/exoplayer)
- [Player.Listener.onRenderedFirstFrame](https://developer.android.com/reference/androidx/media3/common/Player.Listener#onRenderedFirstFrame())
- [Media3 AnalyticsListener](https://developer.android.com/reference/androidx/media3/exoplayer/analytics/AnalyticsListener)
- [Logcat command-line tool](https://developer.android.com/tools/logcat)
- [App startup time](https://developer.android.com/topic/performance/vitals/launch-time)
- [Big Buck Bunny](https://peach.blender.org/) and [Tears of Steel](https://mango.blender.org/), Blender Foundation, CC BY
