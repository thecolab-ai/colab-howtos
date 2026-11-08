# Worked example: how Kev TV was built

Kev is Adam's AI agent. It already had iPhone, iPad and Mac apps. Adam wanted a wall display on a TV: what needs his attention, what his agents are doing, his cameras, and whether his servers and sites are up. He gave the job to Claude Code and steered it while it worked.

This lesson is the story of that build. Use it as a pattern for your own app.

## The brief

- A native Android TV app in Kotlin with Compose for TV, for an Nvidia Shield TV.
- It pairs with the Kev server the same way the other apps do.
- No typing and no chat. It only shows things.
- Every install goes over ADB through one home machine.
- Never touch other apps or the TV's settings.
- Build tools go in the agent's own folder, with checksums checked. No admin rights.
- Then pick one latency number and improve it on the real TV (lesson 7).

## How the agent worked

The agent ran unattended for several hours in its own folder. Three plain text files kept it on track:

- **PROGRESS.md**: a log with times, what was done and the numbers measured.
- **FACTS.md**: things already checked, so the agent didn't check them again. For example the TV's Android version, its screen size and which settings were off.
- **STEER.md**: notes from Adam while it worked, newest first. The agent re-read it at every checkpoint.

STEER.md changed the plan several times. Adam cut the app down to a dashboard with no chat or voice. He asked for a servers and health page. He asked for it to look like the other Kev apps. He asked for pages that rotate and feel alive. Late on, he told it to stop the hill-climb and get the app onto live data. The agent picked up each note at its next checkpoint.

## What it built

At the time of the measurements in lessons 6 and 7, the app had:

- **Five rotating pages**, 25 s each, like an airport board: things waiting on you and today's plan, running agents, cameras, servers, and services. Left and Right on the remote jump a page and hold it. A new urgent item jumps straight to its page.
- **Cameras**: a 2x2 grid of stills. OK opens one full screen with live video, using Media3 ExoPlayer and HLS. Left and Right switch camera.
- **A demo mode** with made-up data and public test streams. Every screenshot and every measurement used it.
- **Kev's look**: colours, type scale and logo ported from the Apple apps' design tokens.
- **A small server change**: a new device platform name so the server accepts a TV, and an ops endpoint that is off by default.

The app has been redesigned since then. The method in this module stays the same.

## The surprise: animations off

The first build looked frozen on the real TV. The clock ticked, but nothing else moved.

The TV had **Animation scale** turned off in its developer settings. Compose scales every animation by that setting. With it off, animations jump straight to the end.

The rule was never to change the TV's settings. So the agent fixed it in the app. The app runs Compose under its own recomposer with a `MotionDurationScale` of 1. The TV's setting stays as it was. A trimmed version of that code:

```kotlin
setContent(parent = fullMotionRecomposer()) { /* the app */ }

private fun fullMotionRecomposer(): Recomposer {
    val clock = PausableMonotonicFrameClock(AndroidUiDispatcher.Main[MonotonicFrameClock]!!)
    val context = AndroidUiDispatcher.Main + clock + FullMotion
    val recomposer = Recomposer(context)
    lifecycleScope.launch(context) { recomposer.runRecomposeAndApplyChanges() }
    // Pause the clock in onStop, resume it in onStart, cancel the recomposer in onDestroy.
    return recomposer
}

private object FullMotion : MotionDurationScale {
    override val scaleFactor: Float get() = 1f
}
```

Frames per page over 30 s, release build, held on one page, from `adb shell dumpsys gfxinfo`:

| Page | Before: frames | Before: janky | After: frames | After: janky | After: p50 frame time |
|---|---|---|---|---|---|
| 1 Waiting on you | 33 | 90.9% | 1800 | 0.06% | 5 ms |
| 2 Agents | 35 | 82.9% | 1800 | 0.83% | 5 ms |
| 3 Cameras | 38 | 7.9% | 1799 | 0.17% | 5 ms |
| 4 Servers | 36 | 5.6% | 1802 | 0.00% | 5 ms |
| 5 Services | 35 | 5.7% | 1800 | 0.06% | 5 ms |

1800 frames in 30 s is 60 frames a second. Before the fix it was about 1.

The commands the agent used, once per page:

```bash
A="adb -s 192.168.1.x:5555"
$A shell am start -n com.example.tv/.MainActivity --ei page 1
$A shell dumpsys gfxinfo com.example.tv reset
sleep 30
$A shell dumpsys gfxinfo com.example.tv
```

`--ei page 1` is an extra the app reads to show one page and hold it. Your app needs its own hook like this.

## Memory over an hour

A wall display runs all day. The agent left the demo rotating for an hour and read the app's memory every 5 minutes:

```bash
adb -s 192.168.1.x:5555 shell dumpsys meminfo com.example.tv
```

What it saw:

- Total memory (PSS) started at 106 MB and was 120 MB after 5 minutes.
- At about the 20-minute mark it jumped to 180 MB. The native heap went from 19 MB to 70 MB. The agent's best guess was video buffers from the camera page.
- Over the next 40 minutes it crept from 180 MB to 187 MB. The native heap grew about 5 MB.

The agent then cut allocation churn: drawn shapes such as sparklines and tick marks are now built once instead of over and over. A short 4.5-minute check after that fix showed the native heap flat at 60 to 63 MB once the camera page had played. That check is too short to prove there is no slow leak. A longer soak is still to do.

## Lessons from the build

- **Measure on the real device early.** The animations problem only showed up on the real TV.
- **Give the agent a demo mode.** It made screenshots and measurements safe on a shared TV, and the same from run to run.
- **Let the owner steer in a file.** A note in STEER.md reached the agent at its next checkpoint without stopping it.
- **Small commits.** The app, the server change and the docs went into one pull request in small commits.

## Notes

Built by Adam with Claude Code on 8 Nov 2026, on an Nvidia Shield TV with Android 11. The jank and memory numbers above were measured on that TV with the commands shown, in demo mode, release build. We left screenshots out of this module because even demo screens show camera names.

## Links

- [Compose for TV](https://developer.android.com/training/tv/playback/compose)
- [Media3 ExoPlayer](https://developer.android.com/media/media3/exoplayer)
- [Inspect GPU rendering speed (gfxinfo)](https://developer.android.com/topic/performance/rendering/inspect-gpu-rendering)
- [Inspect your app's memory usage (meminfo)](https://developer.android.com/studio/command-line/dumpsys#meminfo)
- [MotionDurationScale](https://developer.android.com/reference/kotlin/androidx/compose/ui/MotionDurationScale)
