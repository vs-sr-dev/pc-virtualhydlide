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
`SYS_GETSYSCK`, `SYS_CHGSYSCK`, the BUP pointers, and 0x0600026C (not
identified). About 15 services in all: a small HLE surface.

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

The frame is paced by two things:

1. **VDP1 finishes drawing.** The sprite-draw-end interrupt (0x4D) tells
   the program the frame is drawn; the program writes FBCR and PTMR itself
   (the exact change mode is to read at run time).
2. **A minimum number of VBlanks.** `0x0602A566(last, n)` spins until the
   VBlank counter at 0x06057F40 has moved `n` past `*last`, then stores
   the counter. M_CHI calls it with `n = 2` at 0x060366AC, `n = 5` in
   `main` (0x0600B6F8), and with `n` from a variable at 0x06036508, the
   call that looks like the in-game loop's (to read at run time).
   `0x0602A54E(n)` waits for `n` VBlanks.

So a frame costs `max(n VBlanks, SH-2 work + VDP1 drawing)`. On the
Saturn the second term wins as soon as the field fills with polygons and
sprites, and the game slows. On the PC both the SH-2 work and the drawing
cost next to nothing: the game should hold its cap, whatever it is, all
the time. How the game logic advances per frame (fixed step or by elapsed
VBlanks) decides whether that cap is the speed the designers meant: see
`06-attack-plan.md`.

**The area programs never read TVSTAT's PAL bit** (their one TVSTAT read
tests ODD). Only OPEN and ENDING test it, twice each, near the end of
their text where the libraries sit: most likely the movie player. A PAL
console delivers 50 VBlanks a second, so a cap of `n = 2` means 25 frames
a second on a European Saturn and 30 on a Japanese one, and anything
counted in VBlanks runs 5/6 as fast. The port chooses its own VBlank
rate.

### Interlace

At `0x0604549A` (the VDP1 frame-change code) the program reads TVSTAT's
ODD bit and sets FBCR to `DIE|DIL` or `DIE`: VDP1 double-density
interlace, drawing one field's lines per frame. It runs only when the
halfword at 0x0606D2AC is non-zero; which screens use high-resolution
interlace is open.
