# Open questions

| # | Question | How to answer |
|---|---|---|
| 1 | What is the in-game frame cap: `n` at the limiter call 0x06036508 (M_CHI)? | read it at run time (debugger, or our runtime's trace) |
| 2 | Does the game logic step once per frame, or by elapsed VBlanks? Decides whether 60 fps is a patch or an interpolation | read the main loop (phase 2): what the limiter's return value feeds |
| 3 | Which screens use VDP1 double-density interlace (FBCR `DIE`/`DIL`, gated by 0x0606D2AC)? | run time; the menus and still screens are the suspects |
| 4 | What do the 13 CPU accesses to the VDP1 framebuffer do: clear it, draw into it (movies, fades), read it back? | read the sites (0x0601B73A, 0x0601BD46, 0x06028E76…) |
| 5 | Which program loads which: who loads `LOADER.BIN`, if anyone; how HYDSYS swaps programs and what state survives the swap | read HYDSYS's service table (0x060EE004 → 0x060EE16E) |
| 6 | Is the music all CD-DA? What do the per-area sound-RAM images hold besides effects? | play the game with the oracle; parse `STNHYD.MAP` and a sound bank's directory |
| 7 | What is on track 2 (5 s)? | listen: `build/audio/track02.wav` |
| 8 | What does the slave's job (0x0602583C) compute, and its master twin (0x060255DC)? | read them (phase 2) |
| 9 | BIOS pointer 0x0600026C: which service? | its call sites' arguments; the BIOS itself |
| 10 | The four player sets `P0`–`P3`: four looks, four classes, or four equipment levels? | read the GOB loader; play |
| 11 | Where are "Hi! Come come everybody." and "Guu… I'm sleepinggguuu…" shown? | xrefs in OPEN.BIN |
| 12 | The 82 432-byte screens in `GRAPH/` and the `.OUT`, `.MAP`, `.DAT` files: what format? | only if needed |
