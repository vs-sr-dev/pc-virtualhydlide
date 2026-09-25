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
