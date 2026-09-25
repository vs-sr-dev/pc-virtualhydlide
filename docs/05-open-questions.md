# Open questions

| # | Question | How to answer |
|---|---|---|
| 1 | ~~What is the in-game frame cap?~~ **5 VBlanks** (session 2): `main`'s loop at 0x0600B6F8 in every area program; 0x06036508 belongs to another screen | — |
| 2 | ~~Once per frame, or by elapsed VBlanks?~~ **By elapsed VBlanks** (session 2): `dt` clamped to 25 in the world update. New question: does every piece of logic keep its precision at `dt` = 1? | play at cap 1 once the port runs |
| 3 | Which screens use VDP1 double-density interlace (FBCR `DIE`/`DIL`, gated by 0x0606D2AC)? | run time; the menus and still screens are the suspects |
| 4 | What do the 13 CPU accesses to the VDP1 framebuffer do: clear it, draw into it (movies, fades), read it back? | read the sites (0x0601B73A, 0x0601BD46, 0x06028E76…) |
| 5 | How HYDSYS swaps programs: **answered** (`exec` at 0x060EE08C, session 2). Still open: who loads `LOADER.BIN`, if anyone; what state survives a swap; what 0x060EE008 points to | the runtime |
| 6 | Is the music all CD-DA? What do the per-area sound-RAM images hold besides effects? | play the game with the oracle; parse `STNHYD.MAP` and a sound bank's directory |
| 7 | ~~What is on track 2 (5 s)?~~ **A thank-you** (heard by the user, session 2): music with a voice saying "Thanks for playing, T&E Soft". Still open: when the game plays it (after the ending? on quitting?) | the CD-audio calls (system call group 0x03) |
| 8 | What does the slave's job (0x0602583C) compute, and its master twin (0x060255DC)? | read them (phase 2) |
| 9 | BIOS pointer 0x0600026C: jumped through right after a program is loaded, so probably "start the program at the 1st read address" | the runtime: what the game expects after the jump |
| 10 | The four player sets `P0`–`P3`: four looks, four classes, or four equipment levels? | read the GOB loader; play |
| 11 | Where are "Hi! Come come everybody." and "Guu… I'm sleepinggguuu…" shown? | xrefs in OPEN.BIN |
| 12 | The 82 432-byte screens in `GRAPH/` and the `.OUT`, `.MAP`, `.DAT` files: what format? | only if needed |
| 13 | What is the screen at 0x06036290 (M_CHI), entered from the frame loop when a countdown runs out, driven by the pad, capped at 2 VBlanks? The map, the status screen? | play |
| 14 | Which of the system call's group 0x03 codes (0x0300–0x0304, STARTUP only) play CD audio? | read group 0x03 at 0x060EEF6C |
| 15 | The ~17 KB of unreached leaf code in OPEN: dead, or called in ways discovery does not see? | the runtime's unknown-target log |
