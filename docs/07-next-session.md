# Next session: the frame rate, and the rest of phase 6

Where things stand: the game is on screen, plays, and is heard
(`12-video.md`, `13-sound.md`). The frame cap can be lowered
(`tools/run.py --frame-interval 1` or `2`), but the player's motion is
stepped per frame, so at 60 fps the player walks 5 times too fast
(`14-frame-rate.md`).

## First: the user's choice for the frame rate

Two ways, not exclusive:

1. **Make the per-frame steps follow dt** (level 3 as planned, with more
   work than one constant). Find every place that steps an object once
   per frame: the player's motion script in the world update
   (0x0602EFDC, entries at +0x48, count at +0x56), the animation poses,
   the enemies, projectiles, the camera. At each, advance the script by
   accumulated dt (an entry every 5 VBlanks) and scale the frame's move
   by dt/5. That needs a way to replace a recompiled function by a
   hand-edited copy (saturnkit has hooks on single instructions, not yet
   replacements). How many places there are decides whether this is one
   session or several; start by listing them (watch the player's and an
   enemy's fields per frame at intervals 5 and 1, as session 6 did).
2. **Keep the logic at 12 fps and draw the frames in between**: the
   draw-list interpolation of `06-attack-plan.md`, or, cleaner if the 3D
   pipeline is read, interpolating the camera and the objects' matrices
   the game hands its renderer.

## Then

* **Sound**: the user's ears on the window's sound (music, effects, the
  movie's voice); a CD-DA play (open questions 6, 7, 14: where the 27
  tracks play; the thank-you on track 2), and whether the driver sets
  slot 16–17's level for it; the 1.6 dB gap to Beetle.
* The same world in both (*Create world with code* HCTSPBMFCH in Beetle
  and in the port), compared view for view.
* VDP1 on the GPU at N× resolution, the software path as the reference.
* What the other areas ask of VDP1 and VDP2; the framebuffer's CPU view
  (open question 4); double-density interlace (question 3).

## When convenient

* Read the slave job (0x0602583C) and its master twin (0x060255DC), and
  the VDP1 command builder.
* 256 lines on a 60 Hz raster: check whether anything in the game depends
  on the PAL line count.
* Open question 17 (timer 1 on every line: with the 68000 running, what
  OPEN's sound queue does).

## Useful

* Play: `python tools/run.py --play` (with sound), `--frame-interval N`.
  Headless to the field: `python tools/run.py` (13 s); pictures: `--
  --shot N,...` (build/run/shot-N.png), video memory: `-- --dump N,...`,
  sound: `-- --wav FILE`.
* The oracle: `python tools/oracle.py --at 30:START,35.3:shot,...`
  (build/oracle/tSECONDS.png), `--record` for its sound
  (build/oracle/record.wav); Beetle runs at 50 frames a second, the times
  are wall-clock.
* `--watch LO:HI` with `--trace` prints each access to a memory area
  (not the work RAMs) with the caller's `pr`. For the work RAMs, session
  6 used a temporary store watchpoint in `sh2.h`'s `st16`/`st32` (not
  kept): worth making an option.
* Regenerate, build and check everything: `python tools/recomp.py --build
  --test` (about 2 minutes).
* When a run stops or ends, the runtime prints where the master's last
  4096 polls were, and the sound side's line (samples, 68000 state).
