# Next session: playing in the field (phase 6)

Where things stand: the game is on screen and plays (`12-video.md`).
VDP1 and VDP2 are drawn in software, the window takes the keyboard and a
gamepad, and the opening movie, the title, the menus and the first field
look like Beetle Saturn's. Sound is still silent (phase 7).

## TODO

1. **Play it** with the user, in the field and beyond: walk, fight, open
   the map and the status screen (open question 13), reach another area
   (M_DRA, M_SYA…). Whatever looks wrong is a finding; a VDP2 feature the
   compositor does not do is noted once in the log ("VDP2: … is not
   done").
2. **The same world in both**: *Create world with code* HCTSPBMFCH in
   Beetle (`tools/oracle.py` presses the buttons) and in the port, and
   compare the same view: the horizon's haze, the Gouraud shading, the
   shadow sprite, the HUD.
3. **VDP1 on the GPU** at N× resolution, the software path kept as the
   reference (a run can draw both and compare). Mesh as real
   transparency, as an option.
4. **What the other areas ask for**: VDP2 features that turn up (windows,
   line scroll, rotation?), VDP1's framebuffer from the CPU (open
   question 4), double-density interlace (question 3).
5. **Done when**: a stretch of play in the field and one other area looks
   like the oracle, with nothing noted as not done that shows.

## When convenient

* Read the slave job (0x0602583C) and its master twin (0x060255DC), and
  the VDP1 command builder.
* 256 lines on a 60 Hz raster: the port shows 256 lines and puts
  VBlank-IN at line 224 for VRESO 2; check whether anything in the game
  depends on the PAL line count.
* The movie's cadence: a new frame every 4 VBlanks at 60 Hz, sometimes 3
  or 5; compare with Beetle's at 50 Hz.
* Where the 27 CD-DA tracks play (open questions 6, 14); open questions
  16 (the rest of the sound driver's area) and 17 (timer 1 on every line).

## Useful

* Play: `python tools/run.py --play`. Headless to the field:
  `python tools/run.py` (8 s); pictures: `-- --shot N,...`
  (build/run/shot-N.png), video memory: `-- --dump N,...`.
* The oracle: `python tools/oracle.py --at 30:START,35.3:shot,...`
  (build/oracle/tSECONDS.png); Beetle runs at 50 frames a second, the
  times are wall-clock.
* `--watch LO:HI` with `--trace` prints each access to the range with
  the caller's `pr`: the quickest way to find who reads a variable.
* Regenerate, build and check everything: `python tools/recomp.py --build
  --test` (about 2.5 minutes).
* When a run stops or ends, the runtime prints where the master's last
  4096 polls were: what the game is waiting for.
