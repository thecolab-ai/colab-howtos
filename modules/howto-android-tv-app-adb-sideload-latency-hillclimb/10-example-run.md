# Example run: what the agent built and what went wrong

This lesson follows one run of the method from start to finish. Our example app is an always-on dashboard. The agent built it on its own over several hours, on an Nvidia Shield TV with Android 11. Use the problems it hit as a checklist for your own run.

## The brief, in short

- A native Android TV app in Kotlin with Compose for TV.
- It only shows things. No typing and no chat.
- Every install goes over ADB through one machine on the TV's network.
- Never change the TV's settings or touch other apps (lesson 3).
- Build tools go in the project folder, with checksums checked. No admin rights (lesson 4).
- When the app works, pick one latency number and improve it on the real TV (lessons 8 and 9).

## What the agent built

- **Five pages that rotate**, 25 s each, like an airport board. Most pages are lists and status tiles. Left and Right on the remote jump a page and hold it.
- **A video page.** A 2x2 grid of tiles. OK opens one full screen with Media3 ExoPlayer and HLS. Left and Right switch stream.
- **A demo mode** with made-up data and four public test streams. Every screenshot and every measurement used it, so nothing real was on screen and every build saw the same content.
- **Test hooks**: intent extras to start demo mode, hold a page and open a stream (lesson 7).

## How the steering went

The agent logged to PROGRESS.md and re-read STEER.md at every checkpoint (lesson 2). Steer notes changed the plan several times while it worked:

- Cut the scope to a display only. Drop the text input and voice ideas.
- Add a page.
- Change the look to match a set of design tokens.
- Make the pages rotate and feel alive.
- Late on: stop the hill-climb and hand over.

Each note reached the agent at its next checkpoint. Nobody had to stop it and start again.

## Problem 1: the app looked frozen

The first build looked frozen on the real TV. The clock ticked, but nothing else moved.

The TV had **Animation scale** turned off in its developer settings. Compose scales every animation by that setting. With it off, animations jump straight to the end.

The rules said never to change the TV's settings. So the agent fixed it in the app. The app runs Compose under its own recomposer with a `MotionDurationScale` of 1. The TV's setting stays as it was. A trimmed version of that code:

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

The agent measured each page for 30 s, held on that page, release build, before and after the fix:

```bash
A="adb -s 192.168.1.x:5555"
$A shell am start -n com.example.tv/.MainActivity --ei page 1
$A shell dumpsys gfxinfo com.example.tv reset
sleep 30
$A shell dumpsys gfxinfo com.example.tv
```

| Page | Frames, before / after | Janky, before / after |
|---|---|---|
| 1 | 33 / 1800 | 90.9% / 0.06% |
| 2 | 35 / 1800 | 82.9% / 0.83% |
| 3, video | 38 / 1799 | 7.9% / 0.17% |
| 4 | 36 / 1802 | 5.6% / 0.00% |
| 5 | 35 / 1800 | 5.7% / 0.06% |

1800 frames in 30 s is 60 frames a second. Before the fix it was about 1. After the fix, the median frame time was 5 ms on every page.

What to take from it: **a real TV is not set up like an emulator or a phone.** Check frames on the real device early, and fix what you find in the app, not in the TV's settings.

## Problem 2: memory crept up

A dashboard runs all day. The agent left the demo rotating for an hour and read the app's memory every 5 minutes:

```bash
adb -s 192.168.1.x:5555 shell dumpsys meminfo com.example.tv
```

What it saw:

- Total memory (PSS) started at 106 MB and was 120 MB after 5 minutes.
- At about 20 minutes it jumped to 180 MB. The native heap went from 19 MB to 70 MB. The agent's best guess was video buffers from the video page.
- Over the next 40 minutes it crept from 180 MB to 187 MB.

The agent then cut allocation churn: shapes it drew, such as small charts and tick marks, are now built once instead of on every frame. A 4.5-minute check after that fix showed the native heap flat at 60 to 63 MB once the video page had played. That check is too short to prove there is no slow leak. A longer soak was not run.

What to take from it: **for an always-on app, a soak test is part of done.** Put it in the brief.

## Problem 3: a dead test stream

During the first baseline, one of the four public test streams returned HTTP 404. Its trials had no first frame and were recorded as `NA`. The median left them out, so that build looked faster than it was. The agent swapped the stream for a working one. Lesson 9 has the numbers.

What to take from it: **count your `NA`s.** A failed trial is not a missing number.

## Problem 4: the noise was bigger than the changes

Two builds with the same playback code, measured minutes apart, differed by three to four times on two streams. The stage logs showed the network was nearly all of the wait. The run was stopped before any keep-or-revert round. So the useful result of the hill-climb was a better method, not a faster app. Lesson 9 has the details and the method changes.

## What worked

- **A demo mode from day one.** Safe screenshots and the same content for every measurement.
- **Test hooks.** The agent could reach any screen without a remote.
- **A steer file.** Plan changes without restarts.
- **Small commits.** Each fix could be read, and reverted, on its own.
- **Reading the screen as text.** `uiautomator dump` caught focus and layout problems without a person looking at the TV.

## Notes

Run on 8 Nov 2026 on an Nvidia Shield TV with Android 11, release builds, demo mode, with the commands shown. The steer notes above are short summaries, not the exact words. The app has changed since this run. The method in this module has not. We left screenshots out of this module, so no app data shows.

## Links

- [Compose for TV](https://developer.android.com/training/tv/playback/compose)
- [Media3 ExoPlayer](https://developer.android.com/media/media3/exoplayer)
- [Inspect GPU rendering speed (gfxinfo)](https://developer.android.com/topic/performance/rendering/inspect-gpu-rendering)
- [Inspect your app's memory usage (meminfo)](https://developer.android.com/studio/command-line/dumpsys#meminfo)
- [MotionDurationScale](https://developer.android.com/reference/kotlin/androidx/compose/ui/MotionDurationScale)
