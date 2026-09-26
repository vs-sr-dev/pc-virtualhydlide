# Open questions

| # | Question | How to answer |
|---|---|---|
| 1 | ~~What is the in-game frame cap?~~ **5 VBlanks** (session 2): `main`'s loop at 0x0600B6F8 in every area program; 0x06036508 belongs to another screen | — |
| 2 | ~~Once per frame, or by elapsed VBlanks?~~ **By elapsed VBlanks** (session 2): `dt` clamped to 25 in the world update. New question: does every piece of logic keep its precision at `dt` = 1? | play at cap 1 once the port runs |
| 3 | Which screens use VDP1 double-density interlace (FBCR `DIE`/`DIL`, gated by 0x0606D2AC)? None from the boot to the first field (session 5: FBCR is only ever 3 there) | run time; the other areas' menus and still screens |
| 4 | What do the 13 CPU accesses to the VDP1 framebuffer do: clear it, draw into it (movies, fades), read it back? None ran from the boot to the first field (sessions 4 and 5) | read the sites (0x0601B73A, 0x0601BD46, 0x06028E76…); the runtime's log in other screens |
| 5 | How HYDSYS swaps programs: **answered** (`exec` at 0x060EE08C, session 2; the start is a call to the new crt0, session 4). Still open: who loads `LOADER.BIN` (nobody from the boot to the field); what 0x060EE008 points to (a function, 0x060F07A8) | the runtime, further on |
| 6 | Is the music all CD-DA? **Not in the title and the first field** (session 4): no CD-DA play from the boot to the field; the sound driver gets sequence starts (command 0x01) there. Where the 27 CD-DA tracks play, and what the per-area sound-RAM images hold, is open | the runtime in other areas; parse `STNHYD.MAP` and a sound bank's directory |
| 7 | ~~What is on track 2 (5 s)?~~ **A thank-you** (heard by the user, session 2): music with a voice saying "Thanks for playing, T&E Soft". Still open: when the game plays it (after the ending? on quitting?) | the CD-audio calls (system call group 0x03) |
| 8 | What does the slave's job (0x0602583C) compute, and its master twin (0x060255DC)? | read them (phase 2) |
| 9 | ~~BIOS pointer 0x0600026C~~: **not a program start** (session 4). Programs are started by a call to their crt0; 0x0600026C follows load errors, `exec`'s fallback and A+B+C+START in M_CHI: the BIOS's exit to the system menu, by all appearances | — |
| 10 | The four player sets `P0`–`P3`: four looks, four classes, or four equipment levels? | read the GOB loader; play |
| 11 | Where are "Hi! Come come everybody." and "Guu… I'm sleepinggguuu…" shown? | xrefs in OPEN.BIN |
| 12 | The 82 432-byte screens in `GRAPH/` and the `.OUT`, `.MAP`, `.DAT` files: what format? | only if needed |
| 13 | What is the screen at 0x06036290 (M_CHI), entered from the frame loop when a countdown runs out, driven by the pad, capped at 2 VBlanks? The map, the status screen? | play |
| 14 | Which of the system call's group 0x03 codes (0x0300–0x0304, STARTUP only) play CD audio? | read group 0x03 at 0x060EEF6C |
| 15 | The ~17 KB of unreached leaf code in OPEN: dead, or called in ways discovery does not see? No call to a non-entry from the boot to the first field (session 4), OPEN's movie and title included | the runtime's log, in the rest of the game |
| 16 | The sound driver's other outputs. **In part** (session 5): 0x25A00404 holds the address of the driver's area (0x700: the command blocks); the byte at area + 0xA0 + 2 × stream is the PCM play position in blocks of 4096 samples, which the PCM task (0x06055C36) counts; the reads of 0x25A000A0–0xAE are that task before the driver has set 0x404. Open: the rest of the area, and whether the game waits on any of it later | the runtime's `--watch` (it now traces the caller); the 68000 (phase 7) |
| 17 | SCU timer 1 fires on every raster line (T1MD 1, T1S 0xFF) and drives OPEN's sound queue: is that the rate the game means, and does any program use it for more than the sound task? | read the timer-1 hooks in each program |
