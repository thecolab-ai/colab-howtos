# Measure a number on the real TV

To improve a number in a loop, the agent has to read that number off the real TV, the same way every time, with no one holding the remote. This lesson shows how, with the number we used: the time from picking a video to its first frame on screen.

Our example dashboard has a page of four video tiles playing public test streams. OK on a tile opens it full screen. Left and Right switch to the next stream. Your number might be cold start, time to load a list, or scroll smoothness. The method is the same.

## Pick the number

- **One main number** that a person would feel. Ours: time from picking a stream to its first frame.
- **One guard number** that must not get worse. Ours: cold start time. Then a change that speeds up switching but slows the app's start can't slip through.
- **Measured on the TV's own clock.** Then your computer's clock and the delay of `adb` never get into the number.

## The two timestamps

1. **Select.** The moment the app acts on the choice: OK on a tile, or Left or Right while a stream is full screen. The app logs `stream_select uptime=<ms>`.
2. **First frame.** Media3 ExoPlayer calls `onRenderedFirstFrame()` when the first decoded frame reaches the screen. The app logs `stream_first_frame uptime=<ms>` there.

Both use `SystemClock.uptimeMillis()`. Time to first frame is the second value minus the first.

```kotlin
// When a stream is chosen
Log.i("MyAppTiming", "stream_select uptime=${SystemClock.uptimeMillis()} n=$index how=$how")

// In the player listener
override fun onRenderedFirstFrame() {
    Log.i("MyAppTiming", "stream_first_frame uptime=${SystemClock.uptimeMillis()}")
}
```

## Steps

1. Add the two log lines to your app.
2. Add a test hook so a script can pick a stream without the remote (lesson 7). Our app reads an intent extra, `stream`, and opens that stream once the list has loaded. It only does this in demo mode.

   ```bash
   A="adb -s 192.168.1.x:5555"
   $A shell am start -n com.example.tv/.MainActivity --ei stream 0
   ```

3. Clear the log, trigger a select and read the log back.

   ```bash
   $A logcat -c
   $A shell am start -n com.example.tv/.MainActivity --ei stream 0
   sleep 5
   $A logcat -d -s MyAppTiming:I
   ```

4. Do the same for a switch. While a stream is full screen, Right on the remote is key event 22.

   ```bash
   $A logcat -c
   $A shell input keyevent 22
   sleep 5
   $A logcat -d -s MyAppTiming:I
   ```

5. Measure the guard number, cold start. `TotalTime` in the output is the time to the app's first drawn frame, in ms.

   ```bash
   $A shell am force-stop com.example.tv
   $A shell am start -W -n com.example.tv/.MainActivity --ez demo true
   ```

6. Never trust one run. We used 7 cold starts per build, plus 8 or 12 selects, each followed by a switch. The script cycles through four test streams, so each stream had 4 or 6 visits per build (selects plus switches). That was too few: one slow visit moved a median a lot. Use at least 16 selects, so each stream gets 8 visits, and more if you can. Use the median per stream. Lesson 9 has the script.

## Find out where the time goes

The total says how slow it is. It doesn't say why. So the agent added stage logs from Media3's `AnalyticsListener`, with no change to behaviour. `AnalyticsListener` is marked `@UnstableApi` in Media3, so opt in where you use it. The imports are `androidx.annotation.OptIn` and `androidx.media3.common.util.UnstableApi`.

```kotlin
@OptIn(UnstableApi::class)
fun addStageLogs(player: ExoPlayer) {
    val analytics = object : AnalyticsListener {
        override fun onLoadCompleted(t: AnalyticsListener.EventTime, info: LoadEventInfo, data: MediaLoadData) {
            val what = when (data.dataType) {
                C.DATA_TYPE_MANIFEST -> "manifest"
                C.DATA_TYPE_MEDIA -> "media"
                else -> return
            }
            Log.i("MyAppTiming", "stream_load what=$what ms=${info.loadDurationMs} bytes=${info.bytesLoaded}")
        }

        override fun onVideoDecoderInitialized(t: AnalyticsListener.EventTime, name: String, at: Long, initMs: Long) {
            Log.i("MyAppTiming", "stream_decoder ms=$initMs")
        }
    }
    player.addAnalyticsListener(analytics)
}
```

Our app logs these only between a select and its first frame. It logs timings only, never stream addresses.

What the stage logs showed, on our Shield, in demo mode:

| Case | What happened | Total |
|---|---|---|
| Live test stream, a repeat visit | top playlist 311 ms, then stream playlist 590 ms, then decoder 25 ms; the rest of the wait was not broken down | about 1.6 s |
| Live test stream, first visit in a run | top playlist alone took 2,028 ms | about 3.4 s |
| Video-on-demand stream, first visit | four playlist loads of 518 to 737 ms each, mostly one after another, then 646 ms for the first video segment | about 2.6 s |
| The same stream, picked again | each load about 40 ms, from cache | about 0.3 s |

Decoder start-up was 20 to 34 ms every time. The network was nearly all of the wait. So there was no point tuning the decoder. The things worth trying were fewer, faster or earlier network loads.

## Pin what you're measuring

The loop is only fair if every build sees the same thing. Put these in the brief too:

- **Fixed test content.** Our demo mode uses four public HLS test streams: one live stream, Big Buck Bunny and Tears of Steel (both from the Blender Foundation), and Apple's bipbop example. Use content you have the rights to.
- **Demo mode.** Measuring never touches real data.
- **The release build.** Debug numbers don't carry over.
- **The same TV state.** The TV awake, and nothing else playing. Lesson 9's script checks which app is in front before each run.
- **The agent may not change what is measured.** Otherwise it can "improve" the number by measuring something easier.

## Gotchas

- `onRenderedFirstFrame` fires again after a seek or a new media item. Read the last `stream_first_frame` after the last `stream_select`, not the first one.
- If a stream fails, there is no first-frame line. Give each run a timeout (ours was about 15 to 30 s) and record it as `NA`. Don't let a missing number count as fast. Lesson 9 shows how a dead stream made one build look better than it was.
- The first visit to a stream in a run was often 2.5 to 3.5 s. Repeat visits were usually 0.2 to 1.6 s. Report first visits apart from the rest, or one slow visit moves a small median.
- The network and the stream's server are part of the number. Lesson 9 shows how much they moved it.

## Notes

This is the method behind every number in lesson 9. It was run on 8 Nov 2026 on an Nvidia Shield TV with Android 11, release builds, demo mode, from a Linux adb machine on the same network. The stage table comes from the instrumented build's log for that run. Only names were changed for this lesson: the log tag, the event names and the intent extra. The `@OptIn` wrapper round the stage logs was added after review and has not been compiled in this form.

## Links

- [Media3 ExoPlayer](https://developer.android.com/media/media3/exoplayer)
- [Player.Listener.onRenderedFirstFrame](https://developer.android.com/reference/androidx/media3/common/Player.Listener#onRenderedFirstFrame())
- [Media3 AnalyticsListener](https://developer.android.com/reference/androidx/media3/exoplayer/analytics/AnalyticsListener)
- [Logcat command-line tool](https://developer.android.com/tools/logcat)
- [App startup time](https://developer.android.com/topic/performance/vitals/launch-time)
- [Big Buck Bunny](https://peach.blender.org/) and [Tears of Steel](https://mango.blender.org/), Blender Foundation, CC BY
