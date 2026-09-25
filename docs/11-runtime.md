# The runtime core

Phase 4: the recompiled programs on a Saturn made of C++, with no screen
and no sound yet. The runtime is saturnkit's (`saturnkit/runtime`); this
repository gives it the disc and a pad script (`tools/run.py`).

```sh
python tools/recomp.py --build      # also builds build/recomp-build/saturn.exe
python tools/run.py                 # boot to the field, 2 minutes of game time (about 3 s)
python tools/run.py --trace         # the same, with every event on stderr
python tools/run.py --report        # the hardware log of the last run, as the tables below
```

The run is deterministic: time is virtual (below), so the same pad
script reaches the same place at the same VBlank every time.

## The run

Boot to the field, with the pad script of `tools/run.py`: START at VBlank
1200, then START, A and C in turn every two seconds until VBlank 3100,
then nothing. Nothing is on screen yet, so which press does what is not
known; what is known is where it leads.

| Game time | What happens |
|---|---|
| 0.000 | The HLE boot: IP.BIN (MK-81380 V1.000), the 1st read file `A.BIN` (341 528 bytes) at 0x0600B000, recognised as OPEN by its crc32 |
| 0.152 | OPEN starts the slave: SSHOFF, `SYS_SETSINT(0x94, 0x0603C524)`, SSHON; the slave boots there and waits on its FRT |
| 0.362 | OPEN's interrupt handlers: `SYS_SETUINT` for VBlank-IN/OUT, timers 0 and 1, sprite end, SMPC |
| 0.831 | The backup memory: BUP_Init, Stat, Read of `TE_HYD_1DAT`; none is there, so OPEN writes one (18 368 bytes) |
| 1.236 | SNDOFF, the sound driver loaded, SNDON; its first commands |
| 3.468 | The opening movie: a PCM stream (22 050 Hz, stereo) the SH-2's DMAC fills in sound RAM, video paced by its play position |
| 20.0, 30.0 | START |
| 30.757 | OPEN puts the BIOS's handlers back, stops the slave, loads `HYDLIDE/EXEC/HYDSYS.BIN` |
| 31.213 | **Program start 1**: HYDSYS at 0x060EE000, r4 = 11 (STARTUP), r5 = 10 |
| 33.633 | **Program start 2**: HYDSYS's `exec` loads STARTUP (by its strings, the title menu: *Create new world*, *Resume game*…); its slave, its handlers, its sound driver |
| 34.287 | STARTUP reads the save |
| 49.449 | STARTUP writes the save, puts the handlers back, stops the slave |
| 51.827 | **Program start 3**: M_CHI, the first field, r4 = 0 |
| 51.8–71.1 | M_CHI loads the field (38 CD reads) |
| 71.3 onward | **The frame loop**: `main`'s `limiter(&last, 5)` at 0x0600B6F8; 587 frames in 49 s, every one 83–84 ms apart: 12 frames a second, the cap session 2 read |

At the end (VBlank 7 200, game time 120 s): 3 program starts, 1 871 VDP1
frame changes, 3 022 VDP1 draws, the slave woken 7 631 times through
SINIT; no return that went elsewhere, no call to an address that is not
an entry. On the host it takes 3.2 s: about 38 times faster than the
game's own time, without trying to be fast.

Interrupts taken by the master in the run:

| Vector | Source | Taken |
|---|---|---|
| 0x40 | VBlank-IN | 6 838 |
| 0x41 | VBlank-OUT | 6 838 |
| 0x43 | SCU timer 0 | 6 837 |
| 0x44 | SCU timer 1 | 1 094 934 |
| 0x47 | SMPC | 13 651 |
| 0x4B | SCU DMA level 0 end | 2 116 |
| 0x4D | VDP1 sprite draw end | 3 022 |

## How it is built

`saturnkit/runtime`: `sh2.h` and `core.cpp` are the recompiled code's side
(session 3); the Saturn is the rest.

| File | What |
|---|---|
| `machine.cpp` | The run loop, time, interrupts taken by a CPU, the slave as a coroutine, program starts |
| `bios.cpp` | The boot, the BIOS services, the backup memory |
| `mmio.cpp` | The address map outside the work RAMs and the log of every access |
| `scu.cpp` | Interrupt controller, timers, DMA (levels 0–2, direct and indirect) |
| `smpc.cpp` | Commands, INTBACK, a digital pad driven by a script |
| `cdrom.cpp`, `cdblock.cpp` | The disc (.cue/.bin, ISO 9660) and the CD block at its registers |
| `onchip.cpp` | The SH7604's own registers, per CPU: division unit, free-running timer, DMAC |
| `video.cpp` | VDP1, VDP2 and sound RAM as memory, the raster timing, the sound driver's side |
| `main.cpp` | `saturn --cue GAME.cue [--vblanks N] [--input SCRIPT] [--trace] ...` |

### Time

The recompiled code has no cycle counts. It has safe points (loop
back-edges, calls, `ldc …,sr`), and every 256 of them the master polls:
time moves on, the devices run, interrupts are taken. Time is virtual by
default, 400 ns a safe point (about 11 instructions at 28.6 MHz), and a
register access costs a safe point, so a loop that waits on a device lets
time pass (in this run it makes no difference: everything the game waits
for comes with time). `--realtime` takes the host's clock instead.

The raster is NTSC, 263 lines at 59.94 Hz: line 0 raises VBlank-OUT, line
224 (240 with TVMD's VRESO) VBlank-IN, every line HBlank-IN and the SCU
timers. Virtual time is not a model of the SH-2's speed: in it the field
never takes more than its 5 VBlanks, where the Saturn does (session 1).

### Program starts

In the game a program is started by a call to its crt0, which resets the
stack and never returns: OPEN calls HYDSYS at 0x060EE000 (through its own
loader, 0x06025B34), and HYDSYS's loader (0x060EF94C, called by `exec`)
calls the program it loaded at 0x0600B000 with `jsr @r0`. `sh2_call` sees
a call to a module's base address, identifies the image there by its
crc32, activates its module, and throws back to the runtime's loop, which
calls the entry on an empty host stack. Three per run so far, and they
cost nothing measurable.

### The BIOS

The boot leaves what the BIOS would: IP.BIN at 0x06002000, the 1st read
file (the first file record of the root directory) at the 1st read
address, VBR 0x06000000, the stack at 0x06002000, interrupts masked.
IP.BIN's own code is not run.

Every pointer slot of the two vector tables (master 0x06000000, slave
0x06000400) holds a "BIOS ROM" address of its own, so calling any of them
lands in the runtime, which knows which slot it was. The services the
game uses:

| Service | What the runtime does |
|---|---|
| `SYS_SETUINT` / `GETUINT` (0x06000300/304) | Its own table of handlers; the vector points at the dispatcher. The BIOS's default handler has an address too, so a program that saves the handler and puts it back (all of them do) gets the same one |
| `SYS_SETSINT` / `GETSINT` (0x06000310/314) | The vector itself; 0 puts the dispatcher back. Vector 0x94 is where the slave boots |
| `SYS_SETSCUIM`, `SYS_CHGSCUIM`, 0x06000348 | IMS, and the variable kept in step |
| `SYS_TASSEM` / `CLRSEM` (0x06000330/334) | 256 semaphores; `TASSEM` returns nonzero when it took one (the game spins while it returns 0) |
| `SYS_CHGSYSCK`, 0x06000324 | The variable (the clock is not changed) |
| BUP (0x06000354/358) | Init, SelPart, Format, Stat, Write, Read, Delete, Dir, Verify, GetDate, SetDate on the internal memory, kept in `build/run/backup.bin` |
| 0x0600026C | Stops the run: "exit to the system" |

The interrupt dispatcher: SR and a return address pushed on the stack, the
mask raised to the level, then the handler `SYS_SETUINT` registered,
called like a function (`rts`), then everything restored, as the BIOS's
own dispatcher and its `rte` would. A vector the program set itself with
`SYS_SETSINT` is taken the way the CPU takes it, and must end with `rte`.
Every handler in the run was a `SYS_SETUINT` one.

0x0600026C, open since session 1: the programs never use it to start
anything. They call it when a program fails to load (OPEN 0x06025B4C,
HYDSYS 0x060EF964 and 0x060EF330); `exec` jumps through it only if the
program it started comes back, which no crt0 does; and M_CHI's
0x0602A010 calls it once the pad shows A, B, C and START together (the
Saturn's reset combination), after two system calls. That is the BIOS's
exit to the system menu, by all appearances; the run never reached it.

### The slave

A second context on a host thread used as a coroutine: exactly one CPU
runs at a time and control changes hands at fixed points, so the run
stays deterministic. SSHON boots it from vector 0x94 (the address the
program set with `SYS_SETSINT(0x94, …)` just before, in OPEN, STARTUP and
M_CHI alike); it runs until it waits, which for SBL's slave loop means it
reads its FRT's input-capture flag (FTCSR bit 7) and finds it clear. A
write to SINIT sets that flag and hands it the CPU at once; while it has
work, the master gives it a slice at each poll. SSHOFF unwinds it.

In the run it booted three times and took 7 631 jobs; M_CHI's renderer
hands it `0x0602583C` when it is idle (session 1).

### The CD block

At its registers (HIRQ, CR1–CR4, the data port at 0x25818000), over the
sectors of the .cue/.bin: the drive delivers them at double speed while it
plays, through the CD device connection and the filters (FAD range,
subheader) into the partitions of a 200-sector buffer. Commands complete
at once; the periodic status comes every 16.7 ms. CD-DA plays would be
recorded and timed, not heard: the run asked for none.

Commands the run used (215 010 in all): Get Status 124 312, Get Sector
Number 56 300, the sector loop (Calculate and Get Actual Size, Get Sector
Data, End Data Transfer, Delete Sector Data) 6 701 each, Reset Selector
172, Get Buffer Size 165, Set CD Device Connection 90, Play Disc 90 (all
by FAD, all on the data track), the filters' subheader conditions, mode
and connection 84 each (never a FAD range), Seek 83, Get Session Info 16,
Initialize 5, Abort File 4, Set Sector Length 4, Get TOC 4. GFS reads the
directories itself: of the CD block's file-system commands only Abort
File comes up.

### Sound: the driver's side

The 68000 is not run. What the SH-2 waits for from it is SBL's sound
driver taking commands: the host writes 16-byte blocks into sound RAM at
0x700 (the address the driver publishes at 0x404) and waits until a
block's first byte is cleared. The runtime clears it at the next poll and
logs the command. One kind is followed further: PCM streaming (0x85
start, 0x86 stop), because the movie player paces itself by the play
position the driver publishes at 0x7A0 + 2 × stream; the runtime runs it
from the start command's pitch (0x7800: 22 050 Hz) and ring size.

902 commands in the run: 0x09 ×768, 0x02 ×56, 0x82 ×25, 0x0E ×20, 0x0C,
0x0D and 0x01 ×6, 0x05 ×4, 0x08, 0x83 and 0x87 ×3, 0x85 and 0x86 once.
0x01 and 0x02 look like sequence start and stop: the title's and the
field's music are sequences for the sound driver, not CD-DA (open
question 6).

### What the game needed that took finding

* **VBlank alone is not enough.** OPEN's sound task (the queue that feeds
  the driver, 0x060387EC) is hooked on SCU timer 1, which the game runs
  on every raster line (T1MD 1, T1S 0xFF). Without it the queue never
  drains and OPEN waits for it forever before loading HYDSYS. Timer 1 is
  the most frequent interrupt of the run.
* **The movie waits for the sound.** The player reads the PCM play
  position at 0x25A007A0; with it frozen, the movie stops after 42 VDP1
  draws.
* **A handler discovery had not found.** STARTUP's VBlank-IN handler
  (0x0603C0BC) is only passed to `SYS_SETUINT`, after a pool nothing
  reads; `discover` now takes a pointer to a stack-frame prologue as an
  entry wherever it lies (`09-recompiler.md`).
* **Seek to 0xFFFFFF** is "pause here", not a FAD.

## The hardware touched

`python tools/run.py --report` after the run above. Registers, by access
(R/W and width) and count:

| Block | Registers | Count |
|---|---|---|
| CD block | HIRQ R16 | 23 162 420 |
| | HIRQ W16 | 238 108 |
| | CR1–CR4 R16 / W16 | 483 130 / 215 010 each |
| | data port 0x25818000 R32 (13.7 MB) | 3 422 015 |
| | data port 0x25898000 R16 (TOC, file info) | 816 |
| SCU | D0R, D0W, D0C, D0AD, D0EN, D0MD W32 (level 0 only) | 2 116 each |
| | T0C, T1S, T1MD W32 | 5 each |
| SMPC | COMREG W8 / SF R8, W8 | 6 862 / 6 895, 6 862 |
| | IREG0 W8 (INTBACK, continue) / IREG1–2 W8 | 20 476 / 6 826 each |
| | OREG0–7 R8 (status, pads) | 6 825–40 950 |
| | OREG8–15 R8 (area code, system status, SMEM) | 1 each |
| | SR R8 | 20 470 |
| | DDR1, DDR2, IOSEL, EXLE W8 | 6 each |
| SINIT | 0x01000000 W16 | 7 631 |
| VDP1 | FBCR W16 / PTMR W16 | 1 853 / 3 028 |
| | TVMR W16, EWDR/EWLR/EWRR W16 | 3, 9 each |
| VDP2 | the whole register block, TVMD–COBB W16 (an image written whole) | 15 each |
| | SCXIN1, SCYIN1 (NBG1 scroll) | 601 |
| | PRISA–PRISD (sprite priorities) | 580 |
| | COAR/COAG/COAB (fades) | 119 |
| | SPCTL–SFCCMD | 77 |
| | CCRSA–CCRSD | 70 |
| | TVMD / BGON / CLOFEN, CLOFSL / PRINA–PRIR / CCRNA–CCRLB / COBR–COBB | 32 / 16 / 14 / 8 / 5 / 3 |
| | TVSTAT R16 | 1 |
| SCSP | 0x05B00400 W16 (common control) | 2 |
| SH-2 on-chip | DVSR, DVDNT, DVCR W32 | 1 237 083, 860 430, 860 430 |
| | DVDNTH R32 / W32, DVDNTL R32 / W32 | 570 263 / 376 653, 666 820 / 376 653 |
| | FRCH, FRCL R8 | 56 917 each |
| | FTCSR R8 / W8 (the slave's wait) | 7 634 / 7 631 |
| | CCR R8 / W8 (cache purges) | 8 256 each |
| | SAR0, DAR0, TCR0 W32; CHCR0 R/W; DMAOR R/W (PCM to sound RAM) | 354 each; 1 416 / 1 062; 708 / 354 |
| | TIER W8, IPRA W16, IPRB W16, TCR R/W8 | 3, 3, 3, 1 |

Memory areas:

| Area | Access | Lowest | Highest | Count |
|---|---|---|---|---|
| VDP1 VRAM | W | 0x05C00000 | 0x05C7FFFF | 21 336 110 |
| VDP1 VRAM | R | 0x05C56EEE | 0x05C60E22 | 5 |
| VDP2 VRAM | W | 0x05E00000 | 0x05E7FFFF | 4 607 752 |
| VDP2 VRAM | R | 0x05E40000 | 0x05E44D23 | 28 446 |
| VDP2 CRAM | W | 0x05F00000 | 0x05F005FE | 1 280 |
| SCSP RAM | W | 0x05A00000 | 0x05A76964 | 1 132 101 |
| SCSP RAM | R | 0x05A000A0 | 0x05A40000 | 40 837 |
| cache address array | W | 0x60000000 | 0x600003F0 | 1 536 |

**Calls to addresses that are not entries: none** (open question 15), in
the code this run reached.

Not touched in the run: the VDP1 framebuffer (open question 4), VDP1's
EDSR (the game waits for the sprite-end interrupt instead), SCU DMA
levels 1 and 2, the CD block's MPEG commands, the SCSP's slots, the A-bus.

## What the screens set up

For phase 5: the video registers as the game left them at four moments of
the same run (`tools/run.py --vblanks N -- --peek 25F80000:8,...`).

| VBlank (game time) | Program | TVMD | BGON | CHCTLA | SPCTL | VDP1 FBCR / PTMR |
|---|---|---|---|---|---|---|
| 150 (2.5 s) | OPEN | 0x8000: 320×224 | 0: no scroll plane, VDP1 alone | 0x3232 | 0x3031 | 3 / 1 |
| 600 (10 s, the movie) | OPEN | 0x8000 | 0: the movie is VDP1's | 0x3233 | 0x3031 | 3 / 1 |
| 2 600 (43 s) | STARTUP | **0x8020: 320×256** | 0x0704: NBG2 (and the TPON bits of NBG0–2) | 0x121C | 0x3031 | 3 / 1 |
| 7 200 (120 s, the field) | M_CHI | **0x8020: 320×256** | 0x0002: NBG1 (scrolled every frame) | 0x1132 | 0x3031 | 3 / 1 |

* **256 lines is a PAL-only mode.** STARTUP and M_CHI set TVMD's VRESO to
  2 although the area programs never read TVSTAT's PAL bit (session 1):
  the European build draws 320×256 whatever the console. The port's
  compositor has to show 256 lines; the runtime keeps NTSC timing
  (VBlank-IN at line 224 for VRESO 2, which the Saturn only has on PAL).
* Sprites: type 1, palette and RGB mixed (SPCTL 0x3031), priority 7 for
  every sprite register (PRISA–PRISD 0x0707). VDP1 changes frame by hand
  (FBCR FCM|FCT) and draws when PTMR is written.

## Limits

* **No 68000.** Sound-driver commands are taken and logged, PCM play
  positions run from time; sequences and effects make no sound. The
  driver's other outputs (0x25A000A0–0xAE are read too) stay as written.
* **CD-DA** plays would be timed, not heard.
* **VDP1** "draws" in 1 ms and draws nothing; the command list is walked
  for the counts. VDP2 is not composited.
* **Interrupts** come at polls only (up to 256 safe points late), and an
  interrupt raised twice before it is taken is one: timer 1, every line on
  the Saturn, comes about once a poll.
* **SMPC**: the status bytes (system status, cartridge) are an emulator's
  choice, not checked; area code 0x0C (Europe) with NTSC timing.
* **Not emulated**: the SCU DSP, on-chip interrupts (a DMAC end interrupt
  stops the run), the cache (purges ignored), MINIT beyond its flag.
* **The slave's boot address** (vector 0x94) is inferred from the three
  programs, not from the BIOS.
