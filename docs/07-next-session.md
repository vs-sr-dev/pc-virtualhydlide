# Next session: VDP1 and VDP2 on screen (phase 5)

Where things stand: the game runs headless from the boot to the first
field's frame loop (`11-runtime.md`). The VDPs are memory: every command
table and every register the game writes is there, nothing is drawn.
Phase 5 draws it.

## TODO

1. **A window** in saturnkit's runtime: SDL3 and OpenGL 4.5 (wiikit's
   window, input and frame pacing as the starting point). The frame is
   shown at VBlank-IN; with a window the clock is the host's (`realtime`),
   and `--headless` keeps today's deterministic runs for tests.
2. **VDP1**, at each draw (`draw_start` already walks the list): normal,
   scaled and distorted sprites, polygons, polylines and lines; system and
   user clipping, local coordinates; the colour modes (4 bpp bank and
   lookup table, 8 bpp, RGB), end codes, transparent pixels. First exact
   and in software, into the emulated framebuffer the game changes by hand
   (FBCR FCM|FCT); the GPU path at N× resolution once the software one is
   the reference. Colour calculation (half-transparency, shadow, Gouraud,
   mesh) as the screens need it.
3. **VDP2, a first compositor**: the sprite layer from VDP1's framebuffer
   (type 1, palette and RGB mixed, SPCTL 0x3031; priorities from
   PRISA–PRISD), the NBG layers the screens use (STARTUP's NBG2, the
   field's NBG1 scrolled by SCXIN1/SCYIN1) in their cell modes, CRAM, the
   back screen and the colour offset (COAR/COAG/COAB: the fades). 320×224
   for OPEN, **320×256** for STARTUP and M_CHI (TVMD VRESO 2).
4. **The pad** from SDL3 (keyboard and gamepad) into the SMPC's INTBACK
   answer; the script (`--input`) stays for tests.
5. **The oracle**: Beetle Saturn through RetroArch (`F:\RetroArch 2`, as
   `D:\Homebrew6\SAT-LBA\run.ps1` does) for screenshots of the same
   moments: the SEGA and T&E logos, the opening movie, the title menu, the
   first field.
6. **Done when**: the logos, the movie, the title menu and the first
   field are on screen in real time and look like the oracle's
   screenshots; the headless run still reaches the field.

## When convenient

* Read the slave job (0x0602583C) and its master twin (0x060255DC), and
  the VDP1 command builder: phase 5 draws what they build.
* 256 lines on a 60 Hz raster: the runtime puts VBlank-IN at line 224 for
  VRESO 2. Decide what the port shows (256 lines at 60 Hz is the plan)
  and whether anything in the game depends on the PAL line count.
* Where the 27 CD-DA tracks play (open questions 6, 14): HYDSYS's group
  0x03, run the other areas; the runtime notes every CD-DA play.
* Open questions 16 (the sound driver's other outputs) and 17 (timer 1
  on every line).

## Useful

* Regenerate, build and check everything: `python tools/recomp.py --build
  --test` (about 2.5 minutes); it also builds the runtime
  (`build/recomp-build/saturn.exe`).
* The run to the field: `python tools/run.py` (3 s), `--trace` for every
  event, `--report` for the hardware log; after `--` the executable's own
  options: `--peek ADDR[:WORDS],...` (memory at the end), `--watch LO:HI`
  (each address of a memory area, counted), `--input VBLANK:BUTTONS,...`,
  `--vblanks N`, `--realtime`.
* When a run stops or ends, the runtime prints the interrupts taken, the
  return addresses on the stack, and **where the master's last 4096 polls
  were** (the recompiled function that was spinning): the quickest way to
  see what the game is waiting for.
* The generated code: `build/recomp/p_<program>_NNN.cpp`, each line with
  its address and instruction.
