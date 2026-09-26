# Next session: the fields in between, then the rest of phase 6

Where things stand: the game is on screen, plays, and is heard
(`12-video.md`, `13-sound.md`). The frame cap can be lowered
(`tools/run.py --frame-interval 1` or `2`), but everything that moves is
stepped per frame, so the port draws the fields between the game's
frames instead (`--interp`, `14-frame-rate.md`).

## First: the fields in between, finished

The user chose interpolation (`14-frame-rate.md`): `tools/run.py --play
--interp` runs the game at its 12 frames a second and the runtime draws
60 pictures a second, one frame behind. To do:

* The user's eyes on it in play: walking, turning, fighting, enemies,
  the sky, the HUD, menus over the field.
* Zero latency: draw the fields toward the frame the game has already
  built while it waits in its limiter (its 3D list is complete there;
  its textures, the player's picture among them, come with the send).
* The other area programs: find the game layer's addresses in M_DRA,
  M_SYA, M_KYU... (`recomp.match` carries names across programs).
* Commands with no counterpart pop in at their place; fading them in, or
  holding the vanished ones, if it shows.

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
