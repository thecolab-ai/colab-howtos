# Write the brief, and steer the agent with a file

The agent works alone for hours. It only knows what you write down. Four plain text files in the project folder do the job:

- **BRIEF.md**: the job. You write it once, before the start.
- **FACTS.md**: things the agent has already checked, such as the TV's Android version. It writes them down so it doesn't check them again.
- **PROGRESS.md**: a dated log of what it did, what it measured and what is next. The agent writes it. You read it.
- **STEER.md**: your notes while it works. The newest dated note goes at the top and wins. The agent re-reads the file at every checkpoint.

## What goes in the brief

A good brief has four parts:

1. **Goal.** What the app does, in a few lines. Say "Kotlin, Jetpack Compose for TV, remote only".
2. **Device facts.** The TV model, Android version, screen size, and the one adb address to use.
3. **Constraints.** What the agent may and may not do: tools, folders, the TV, secrets, commits.
4. **Done means.** A checklist the agent can verify itself. Without it, the agent can't tell when to stop.

Here is a template. Fill in the parts in angle brackets.

```markdown
# Brief: <app name>

## Goal
A native Android TV app in Kotlin with Jetpack Compose for TV (androidx.tv:tv-material).
It shows <what it shows>. Remote only: D-pad, OK and Back. No typing, no touch.

## Device facts
- TV: <model>, Android <version> (API <level>)
- Screen: <from `adb shell wm size`>
- adb: from <home machine> only, always as `adb -s 192.168.1.x:5555`

## Toolchain
- JDK 17, Android SDK and Gradle live in this folder. Run `. ./env.sh` first.
- No sudo and no system installs. Check every download against its published SHA-256.

## Constraints
- Package id com.example.tv. Release builds signed with the debug key. Sideload only.
- <paste the rules from lesson 3>
- Small commits: one change each, with a message that says why.
- No secrets in code, logs, commits, screenshots or PROGRESS.md.

## Done means
- `./gradlew assembleRelease` and the unit tests pass.
- The app is on the TV's home screen with a banner and opens with OK.
- Every screen can be reached with the D-pad, and focus is always visible.
- A demo mode with made-up data, started with `--ez demo true`.
- One screenshot per screen in demo mode, scaled to 1280x720.
- PROGRESS.md lists what was measured and what is left.

## Checkpoints
After each commit: add a dated entry to PROGRESS.md, re-read STEER.md
(the newest note at the top wins), then carry on.
```

## Steps

1. Make the project folder and the four files.

   ```bash
   mkdir tv-app && cd tv-app && touch BRIEF.md FACTS.md PROGRESS.md STEER.md
   ```

2. Collect the device facts for the brief. Each command only reads. (untested as written: the agent found these facts in our run, but the exact commands were not logged)

   ```bash
   A="adb -s 192.168.1.x:5555"
   $A shell getprop ro.build.version.release
   $A shell getprop ro.build.version.sdk
   $A shell wm size
   $A shell settings get global animator_duration_scale
   ```

3. Write `BRIEF.md` from the template. (untested)
4. Start your agent in the folder. Give it one prompt: "Read BRIEF.md and do it. Log to PROGRESS.md. Re-read STEER.md at every checkpoint." (untested)
5. Read `PROGRESS.md` from time to time. Don't interrupt the agent unless something is wrong.
6. To change course, add a dated note at the top of `STEER.md`. Say what it overrides. The agent picks it up at its next checkpoint.

   ```markdown
   ## 2026-11-08 13:40: scope change (overrides the brief's Goal)
   - Make it a display only: no typing, no chat, no voice.
   - Pages: what needs attention, running jobs, status of services.
   - Measure on the real TV from now on. Skip the emulator.
   ```

7. To stop cleanly, write a stop note. Tell it what to save and where.

   ```markdown
   ## 2026-11-08 17:10: stop and hand over
   - Stop at the next clean point. Save the logs.
   - Update PROGRESS.md: numbers so far, what is left.
   - Push your commits to a new branch. Don't open a pull request.
   - Then stop. Don't touch the TV again.
   ```

8. Review the work commit by commit.

   ```bash
   git log --oneline
   ```

## What we saw in our run

- The steer file changed the plan several times: skip the emulator and measure on the TV, cut the app down to a display, add a status page, match the look of other apps, make the pages rotate, then stop the hill-climb and ship. The agent picked up each note at its next checkpoint without a restart.
- `FACTS.md` kept the agent from checking the same thing twice. It held the TV's Android version, CPU type, screen size and density, and the fact that animations were off.
- Small commits paid off. The theme, page rotation, the animation fix, a test stream swap, a memory fix and the timing logs each went in on their own. Any one of them could be reverted alone.

## Gotchas

- A note only lands at the next checkpoint. If something is urgent, stop the agent.
- Date every note and put the newest at the top. Two undated notes that disagree leave the agent guessing.
- Never put a secret in `STEER.md`. If the agent needs a credential, name it and say where it lives. Don't paste it.
- If the brief has no "done means" list, the agent decides when it's done. Write the list.

## Notes

In our run, on 8 Nov 2026, the agent kept `FACTS.md`, `PROGRESS.md` and `STEER.md` exactly as described, and re-read `STEER.md` at checkpoints. The brief was the agent's first prompt, not a file, so steps 3 and 4 are marked untested. The template above is a cleaned-up version of it, with the done list we would add next time. The two steer notes are shortened, generic versions of real notes from that run. Step 2's commands were not logged in the run, so they are marked untested.

## Links

- [Claude Code: best practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Codex CLI](https://github.com/openai/codex)
- [adb shell commands](https://developer.android.com/tools/adb#shellcommands)
