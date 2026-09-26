# Sessions

## Session 1 (2026-09-25) — feasibility, the disc, the plan

* The disc: IP.BIN (MK-81380, V1.000, Europe), 28 tracks (one data, 27
  CD-DA with 2-second pregaps), 458 files; extracted to `build/extract`,
  the audio to `build/audio` (`01-disc-layout.md`).
* The programs: 15 flat SH-2 binaries, all loaded at 0x0600B000 except
  the resident `HYDSYS.BIN` (0x060EE000) and `LOADER.BIN` (0x060C0000);
  SBL libraries, T&E's own 3D engine, no SGL, no SCU DSP; the slave SH-2
  used through SPR in one renderer function; interrupts and handlers; the
  frame limiter and its VBlank counter; the PAL bit ignored by the area
  programs (`03-executables.md`).
* The formats at a glance: T&E's chunked files, Sega FILM/Cinepak
  movies, SCSP sound-RAM images (`02-data-formats.md`).
* The route: static recompilation, the hardware cut at its registers, the
  frame rate in three levels (`06-attack-plan.md`).
* saturnkit started as its own repository, here as a submodule: `disc`,
  `sh2` (equal to capstone on every SH-2 opcode), `hw`
  (`10-saturnkit.md`).

## Session 2 (2026-09-25) — the code map

* **The frame loop read** (`03-executables.md`): every area program's
  `main` loops with `limiter(&last, 5)`, a cap of one frame every 5
  VBlanks (12 fps at 60 Hz, 10 on a European Saturn), and the logic
  advances by elapsed VBlanks (`dt`, clamped to 25), not per frame. The
  60 fps plan is a constant, not an interpolation (`06-attack-plan.md`).
* **HYDSYS's interface**: `exec(index, arg)` at 0x060EE08C swaps
  programs and writes a header at 0x060EE004 (the system call, a
  pointer, a hook, the signature 0x12345678); the variadic system call
  dispatches four groups (reset, files/CD, sound, CD audio?).
* **Function discovery** for stripped SHC code in saturnkit: 15 programs,
  no conflicts; 571 of the 576 functions Ghidra finds in the field
  program, the other 5 shared tails.
* **The same engine across programs**: `saturnkit.recomp.match` carries
  names from M_CHI (`tools/names-m_chi.tsv`, 25 names) to the other
  programs; the frame limiter lands where its bytes are in 11 of 11.
* **An SH-2 interpreter** in saturnkit; with it the SHC runtime's four
  division helpers identified on 12 000 of 12 000 random operands.

## Session 3 (2026-09-25) — the recompiler

* **All 15 programs to C++** (`09-recompiler.md`): 10 256 functions,
  1.5 million instructions, one module per program, compiled and linked
  with clang in under 90 s. A program in memory is recognised by its crc32, so
  the 13 that share 0x0600B000 each run their own code.
* **The counts**: 36 computed jumps left unresolved, all tail calls
  through tables of function pointers in HYDSYS, LOADER, OPEN and ENDING,
  none in the area programs; 3 342 calls through registers, dispatched at
  run time; no static target outside the modules.
* **The self-test**: 51 448 vectors recorded with the interpreter, 0
  failures: saturnkit's own test of every instruction form (alone and in
  a delay slot) and of the control flow, and 2 647 of the game's
  functions in all 15 programs (the division and bit-field helpers, the
  fixed-point and table routines, the routines on vectors and structures).
* **What it caught**: functions whose code starts below their entry began
  at the wrong place (2% of them); discovery now follows a branch into a
  delay slot, resolves the shift ladder with an offset (the one jump left
  in session 2), and no longer takes a data pointer (crt0's BSS end) for a
  function.
* saturnkit: `recomp` (the emitter and its driver), `recomp.selftest`, and
  the first of the C++ runtime (`runtime/`: the SH-2 context, memory,
  dispatch over modules, the self-test harness) (`10-saturnkit.md`).

## Session 4 (2026-09-26) — the runtime core

* **The game runs, headless** (`11-runtime.md`): from the HLE boot of
  `A.BIN` through OPEN (its movie, its save), HYDSYS, STARTUP (the title
  menu, a new world) to M_CHI, the first field, whose frame loop then
  holds its cap: 587 frames in a row, every one 5 VBlanks apart, 12 fps.
  Deterministic, in virtual time, about 38 times faster than the game's
  own clock; no return that went elsewhere, no call to a non-entry.
* **The Saturn in saturnkit's runtime**: the boot and the BIOS services
  (interrupt handlers, SCU mask, semaphores, the backup memory in a host
  file), program starts (the host stack unwound at every call to a
  program's crt0), SCU interrupts, timers and DMA, the SMPC with a
  scripted pad, the slave as a coroutine woken by SINIT, the CD block at
  its registers over the .cue/.bin, the SH-2's on-chip division unit,
  timer and DMAC, the VDPs as memory with the raster timing, and the
  sound driver's command handshake and PCM play position.
* **Answers**: 0x0600026C is not a program start but, by all appearances,
  the BIOS's exit to the system (open question 9); `exec` starts a program
  by calling its crt0; the title's and the field's music are sequences for
  the sound driver, not CD-DA (question 6, in part); SCU timer 1, every
  raster line, drives OPEN's sound queue; the movie player paces itself
  by the PCM play position; STARTUP and M_CHI set VDP2 to 256 lines, a
  PAL-only mode.
* **Discovery**: a pointer to a stack-frame prologue is an entry wherever
  it lies (STARTUP's VBlank-IN handler was missing); 5 functions found,
  5 wrong or redundant entries gone, the self-test at 51 532 of 51 532.
* `tools/run.py`: the run to the field, its trace, the hardware log as
  tables.

## Session 5 (2026-09-26) — on screen

* **The game in a window** (`12-video.md`): the opening movie, the title,
  the menus and the first field drawn by saturnkit's VDP1 and VDP2 in
  software, shown with SDL3 and OpenGL 4.5 at the Saturn's speed, played
  with the keyboard or a gamepad. Against Beetle Saturn the title, the
  movie's frames and the menus are the same pictures; the field has the
  same look, in a different random world.
* **VDP1**: the command table drawn the chip's way (quadrilaterals as
  lines between two walked edges, anti-aliased lines), every colour mode,
  clipping, mesh, shadow, half-luminance, half-transparency, Gouraud;
  double framebuffers changing frame at VBlank-OUT. **VDP2**: NBG0–NBG3
  in cell and bitmap modes with zoom, the sprite layer, priorities,
  colour calculation, colour offsets, the back screen.
* **Findings**: the frame changes at the end of VBlank (the movie player
  asks for it in its VBlank-IN handler); the sound driver publishes the
  PCM play position in blocks of 4096 samples, and with it the movie runs
  at its own 15 fps instead of 2.4 times too fast; the field's sky is a
  224-line picture stretched to 256 lines by NBG1's zoom; the SEGA screen
  before the movie is the BIOS's; with a backup-RAM cartridge in, OPEN
  asks where to save.
* `tools/oracle.py`: Beetle Saturn driven over UDP (buttons, screenshots)
  with its own settings; `tools/run.py --play`; the runtime's `--shot`,
  `--dump`, and `--watch` tracing the caller.
* **Played** by the user at the end of the session, with a gamepad: the
  menus, a new world, then the field for over two minutes, running
  around and killing monsters. Everything looked right; the sound is
  silent (phase 7).
