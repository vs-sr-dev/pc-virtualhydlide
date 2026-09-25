# The programs

Addresses are for `M_CHI.BIN` (the field) unless noted. Each program links
the same engine at slightly different addresses, so a function found in
one is found in the others by its bytes, not its address.

## Toolchain and libraries

* **Compiler**: Hitachi SHC by all appearances: `mov.l r14,@-r15` /
  `sts.l pr,@-r15` prologues, frame pointer in r14, literal pools after
  each function, a shared runtime helper for division (`0x0603E918`,
  called from ~250 sites).
* **Build**: `Version Jun 26 1995 (17:13:07)` (M_CHI), `(17:17:04)`
  (OPEN): the programs were linked one after another four days before the
  IP.BIN date (1995-06-30).
* **Sega's libraries (SBL)**, recognised by their strings and hardware
  use: GFS and STM (files and streams from the CD), the Cinepak player
  (`Error : CinePack`), the backup-memory library (BUP, through the BIOS
  pointers at 0x06000354/0x06000358), the sound driver interface
  (`SDDRVS.TSK`, sound-area maps), SPR's slave-CPU calls.
* **No SGL.** The 3D engine is T&E's own: it projects vertices on the
  SH-2, sorts polygons in a Z table (`ERROR:AllocZTable`), and writes
  VDP1 command tables itself (`VDP1CmdBuff`, `PolyExec`).
* **No SCU DSP.** No access to its registers (0x25FE0080–0x25FE008C): the
  matrix work is on the SH-2s.
* **No cache used as RAM** (0xC0000000), no rotation background on VDP2
  (RPMD, RPTA untouched): the floor and walls are VDP1 polygons.

## Memory map

The first-read program's crt0 disables interrupts, fills 0x06002000–
0x06005000 with 0xAA (stack canary), sets the stack at 0x06004FFC, clears
the BSS and calls `main` at 0x0600B068. Every program has the same crt0.

| Range | What |
|---|---|
| 0x06000000–0x06002000 | BIOS work area and service pointers |
| 0x06002000–0x06005000 | the stack (filled with 0xAA at boot) |
| **0x0600B000**–~0x0606F000 | **the current program**, text + data + BSS |
| 0x0600B000–0x060B86AC | OPEN.BIN and ENDING.BIN, which have a much larger BSS (≈350 KB, movie buffers) |
| 0x060C0000–0x060CF19C | `LOADER.BIN` (text to 0x060C8260, BSS to 0x060CB19C, stack at 0x060CF19C) |
| **0x060EE000**–0x060FF838 | **`HYDSYS.BIN`, resident** (text to 0x060FA532, BSS to 0x060FF838) |
| 0x00200000–0x00300000 | WRAM-L: data (the programs reference 0x00200000, 0x00240000, 0x00250000, 0x00282000) |

Load addresses from `saturnkit.sh2 --find-base`, checked against each
crt0 (the BSS starts where the file ends): 14 of 15 agree, and MENU.BIN's
crt0 overrules the finder.

| Program | Size | BSS end | Functions (estimate) |
|---|---|---|---|
| OPEN.BIN | 341 528 | 0x060B86AC | ~1 540 |
| STARTUP.BIN | 285 636 | 0x0606EE5B | ~1 030 |
| MENU.BIN | 58 160 | 0x0602086B | ~180 |
| M_CHI.BIN | 283 744 | 0x0606E8DC | ~1 280 |
| M_DRA.BIN | 268 380 | 0x0606A9D8 | ~910 |
| M_SYA.BIN | 269 512 | 0x0606BAB0 | ~1 090 |
| M_KYU.BIN | 284 752 | 0x0606F020 | ~1 240 |
| M_FIN.BIN | 270 064 | 0x0606B020 | ~930 |
| M_BURIAL.BIN | 259 532 | 0x06068984 | ~870 |
| M_ORDEAL.BIN | 265 748 | 0x0606A1E0 | ~900 |
| M_RUINS.BIN | 274 016 | 0x0606C69C | ~1 200 |
| M_SEAL.BIN | 295 632 | 0x060719FC | ~1 140 |
| ENDING.BIN | 339 972 | 0x060B7EA4 | ~1 320 |
| LOADER.BIN | 33 376 | 0x060CB19C | ~330 |
| HYDSYS.BIN | 50 482 | 0x060FF838 | ~280 |

About 14 200 function entries in all, about 7 750 distinct (by their
first 24 bytes): the engine repeats in every program. The estimate counts
`bsr` targets and `mov.l` literals that point at a prologue; function
discovery proper is next session's work.

## Program swapping

The game is a set of complete programs that replace each other at
0x0600B000, with a resident system underneath:

* `A.BIN` (= `OPEN.BIN`) boots. It has its own CD and sound code, names
  `HYDLIDE/EXEC/HYDSYS.BIN`, and references 0x060EE000 three times: it
  loads HYDSYS and, by all appearances, starts it.
* `HYDSYS.BIN` has its own crt0 (entry 0x060EE014, after a `bra` over
  two pointers). Its first pointer, at **0x060EE004**, is how the area
  programs reach it: M_CHI loads that pointer 82 times, MENU 3 times. The
  area programs never touch the CD block or the SCSP registers, and HYDSYS
  does (HIRQ, CR1–CR3, the data port, sound RAM): CD, files and sound are
  HYDSYS's services. It also carries the table of program names
  (`MENU.BIN`, `M_CHI.BIN`, … `ENDING.BIN`), so it is presumably what
  loads the next program.
* `LOADER.BIN` has the same name table but nothing references its
  address. A leftover, or loaded by a path not yet seen (open question).

For the recompiler this means one set of functions **per program**, and a
dispatcher that knows which program occupies 0x0600B000 now.

### HYDSYS's interface

`exec(index, arg)` at **0x060EE08C** (reached through the entry at
0x060EE000 once HYDSYS is up) is the program swap:

1. masks interrupts; initialises the system on the first call;
2. writes HYDSYS's header, which the programs read:

   | Address | Value | Meaning |
   |---|---|---|
   | 0x060EE004 | 0x060EE16E | the system call |
   | 0x060EE008 | 0x060F07A8 | a second pointer (a shared block?) |
   | 0x060EE00C | 0 | a hook, called by the system call's exit path if set |
   | 0x060EE010 | 0x12345678 | a signature: HYDSYS is present |

3. loads program `index` (0–13, from the name table at 0x060FA4F0:
   MENU, M_CHI, M_DRA, M_SYA, M_KYU, M_FIN, M_BURIAL, M_ORDEAL, M_RUINS,
   M_SEAL, OPEN, STARTUP, ENDING) to 0x0600B000 through `0x060EF94C`
   (name, address, arg, −1); an out-of-range index loads MENU.
   `0x060EF94C` loads the file and **calls** its crt0 (`jsr @r0` at
   0x060EF972, r4 = arg, r5 = −1), which resets the stack and never
   returns; if the load fails it calls the BIOS pointer at 0x0600026C;
4. only if that call came back does `exec` load and call `MENU.BIN` (the
   name at 0x060FA3C4) the same way, and if that came back too, **jump**
   through 0x0600026C. Session 2 read this jump as
   the program start; session 4 corrected it (`11-runtime.md`): the start
   is the call in step 3, and 0x0600026C is, by all appearances, the
   BIOS's exit to the system menu (it follows load errors, and M_CHI
   calls it on A+B+C+START).

OPEN starts HYDSYS the same way: its own loader (0x06025B34) loads
`HYDLIDE/EXEC/HYDSYS.BIN` to 0x060EE000 and calls it with r4 = 11
(STARTUP) and r5 = 10; HYDSYS's crt0 passes them to `exec`.

The **system call** at 0x060EE16E is variadic, `sys(cmd, ...)`, arguments
on the stack; it dispatches on `cmd & 0xFF00` (`0x060EF164`):

| Group | Handler | Codes used by the programs | By its code |
|---|---|---|---|
| 0x00 | 0x060EE1AA | — | reset / initialise |
| 0x01 | 0x060EE1F0 | 0x0100, 0x0102, 0x0108, 0x010A, 0x010B | files and CD (GFS) |
| 0x02 | 0x060EE7DA | 0x0200–0x0210 | sound: loads `SDDRVS.TSK`, `AREATBL`, `SNDTBL`, `STNHYD.MAP`; SCSP, SMPC |
| 0x03 | 0x060EEF6C | 0x0300–0x0304 | 22 functions over the CD block only: CD audio? |

The area programs make ~80 system calls each; MENU makes 3.

## The slave SH-2

The game starts the slave the SBL way (SPR library):

1. `0x0603E76C`: SMPC command 0x03 (`SSHOFF`), then
   `SYS_SETSINT(0x94, 0x0603E6C4)` (the slave's entry), then SMPC command
   0x02 (`SSHON`); the command bytes sit at 0x0604AF28/0x0604AF29.
2. The slave's loop, `0x0603E714`: interrupts masked, it polls the FRT's
   input-capture flag (`FTCSR`, 0xFFFFFE11, bit 0x80), then calls the
   function pointer at **0x060503D4** (read cache-through, 0x260503D4)
   and clears it.
3. The master's side: `0x0603E8E6` (run: wait until the pointer is 0,
   store the function, write 0xFFFF to **SINIT**, 0x21000000, which pulses
   the slave's FRT input); `0x0603E8D0` (is the slave idle?).

It is used **opportunistically**, in one place of the renderer
(0x060286E6): if the slave is idle it gets `0x0602583C`, otherwise the
master runs `0x060255DC` itself. Three other sites wait for it to finish.
In the port, the slave's job can run on the host at the SINIT write,
before the master looks again.

## Interrupts and BIOS services

Installed through the BIOS pointers (`SYS_SETUINT` 0x06000300), each with
its SCU vector. `0x0602A290` saves the previous handlers of 0x40, 0x41,
0x43 and 0x44 (at 0x06057F94–0x06057FA0), installs the game's, sets the
SCU timer 0 compare (T0C) and unmasks them; `0x0602A38C` puts the old
ones back.

| Vector | Source | Handler |
|---|---|---|
| 0x40 | VBlank-IN | 0x0603E5AC: increments the frame counter at **0x06057F40**, then calls a list of per-VBlank callbacks (count at 0x06057F44, table at 0x06057F50) |
| 0x41 | VBlank-OUT | 0x0603E602 |
| 0x43 | SCU timer 0 | 0x0603E688 |
| 0x44 | SCU timer 1 | 0x0603E69C |
| 0x47 | SMPC | 0x06040C5A |
| 0x49–0x4B | SCU DMA end, levels 2–0 | through pointers at 0x0606E868–0x0606E870 |
| **0x4D** | **VDP1 sprite draw end** | 0x0603E65C (the previous handler kept at 0x06057E94) |
| 0x94 (slave) | slave entry | 0x0603E6C4 |

Other services used: `SYS_CHGSCUIM` (mask changes), `SYS_TASSEM` /
`SYS_CLRSEM` (semaphores 0x00, 0x20–0x23, around VDP1 and DMA),
`SYS_GETSYSCK`, `SYS_CHGSYSCK`, the BUP pointers, and 0x0600026C (the
exit to the system, session 4). About 15 services in all: a small HLE
surface, all of it in saturnkit's runtime now (`11-runtime.md`).

## Hardware touched

`python -m saturnkit.sh2 … --refs` over M_CHI (OPEN in brackets where it
differs):

| Block | Registers / areas |
|---|---|
| VDP1 | TVMR, FBCR, PTMR, EWDR, EWLR, EWRR, EDSR; VRAM 0x25C00000–0x25C7FFFF; **the framebuffer**, 0x25C80000/0x25CB8000/0x25CC0000 (13 sites) |
| VDP2 | TVMD, TVSTAT, CYCA0L, BGON, SCXIN1/SCYIN1 (NBG1 scroll), the colour offset COAR/COAG/COAB (fades); VRAM, CRAM. (OPEN also: ZMCTL, SPCTL, PRISD) |
| SCU | DMA level 0 (D0R, D0W, D0C, D0EN), T0C |
| SMPC | COMREG, IREG, OREG0–OREG31, SR, SF |
| CD block | (OPEN, HYDSYS) HIRQ, CR1–CR4, the data port 0x25898000 |
| SCSP | (OPEN, HYDSYS) sound RAM, the common registers at 0x25B00400 |
| Slave | SINIT (0x21000000) |
| SH-2 on-chip | FRT (FTCSR, FICR; OPEN also FRC, TCR), IPRB, CCR (cache), DRCR0 (DMAC), DIVU (DVSR, DVDNTL, DVCR) |

## The frame and its limiter

### The main loop

Every area program has the same `main` at 0x0600B068 (it is first in the
link order), and in it the same loop, 0x0600B59A–0x0600B7B8:

1. read the VBlank counter (`0x0602A57C` returns 0x06057F40); `delta` =
   now − the last frame's count (0x06050464); if `delta` < 50, advance
   two clocks by it: a timer capped at 150 (`0x0601BBBC`) and the play
   time in hours/minutes/seconds on a base of **60** (`0x06037E0C`);
2. the updates (`0x0600C6C0`, `0x0602C366`, `0x0602D3FE`, `0x0602EFDC`,
   `0x0602EDEC`, `0x06024D10`, `0x06024A18`…), the drawing, `0x06029920`;
3. **`limiter(&last, 5)`** at 0x0600B6F8: wait until 5 VBlanks have
   passed since the previous frame;
4. back to 1.

**The game is capped at one frame every 5 VBlanks: 12 frames a second on
a 60 Hz console, 10 on a European one.** Whenever the work and the VDP1
drawing take longer than 5 VBlanks, it drops further.

### The logic runs on elapsed time

The world update (`0x0602EFDC` in M_CHI) keeps its own clock:
`dt = now − last` (0x0605A294), **clamped to 25**, and adds `dt` to its
timers and counters (compared against 10, 25, 150, 500, 1 000) and hands it
to the movement routines (`0x0602BDEA`). Other subsystems (0x0603897C,
0x060398E2, 0x06029DDA, the pad reader 0x060241B2…) read the counter the
same way and compare elapsed VBlanks with durations. The clamp is in every
program that has the engine (M_CHI 0x0602F076, OPEN 0x0602C50A, …).

So the logic does not step once per frame: it steps by elapsed VBlanks.
Two consequences:

* **The cap is a constant.** Lowering the 5 should raise the frame rate
  without changing the game's speed: 1 gives a frame per VBlank. Whether
  every piece of logic keeps its precision with `dt` = 1 (integer
  rounding in movement, animations stepped by thresholds) is to check in
  play.
* **Everything is timed in 60 Hz VBlanks.** The play clock divides by 60;
  a European console delivers 50, so the whole game (timers, movement,
  the clock) runs at 5/6 speed there. The area programs never read
  TVSTAT's PAL bit (their one TVSTAT read tests ODD); only OPEN and ENDING
  test it, twice each, near the end of their text where the libraries
  sit, most likely in the movie player.

### The limiter

`0x0602A566(last, n)` spins until the counter at 0x06057F40 has moved `n`
past `*last`, then stores the counter in `*last`. `0x0602A54E(n)` waits
for `n` VBlanks. The counter is incremented by the VBlank-IN handler
(0x0603E5AC). Calls in M_CHI:

| Site | n | Where |
|---|---|---|
| 0x0600B594 | 0 | `main`, before the loop: starts the clock |
| **0x0600B6F8** | **5** | `main`'s loop: the frame cap |
| 0x06036508 | 0 (r12) | 0x06036290, a screen called from the loop (pad-driven, not the field) |
| 0x060366AC | 2 | the same screen: 30 fps (25 on PAL) |

The same four sites exist in all nine area programs, at the same
addresses for `main` (0x0600B594, 0x0600B6F8).

### Interlace

At `0x0604549A` (the VDP1 frame-change code) the program reads TVSTAT's
ODD bit and sets FBCR to `DIE|DIL` or `DIE`: VDP1 double-density
interlace, drawing one field's lines per frame. It runs only when the
halfword at 0x0606D2AC is non-zero; which screens use high-resolution
interlace is open.
