# The porting route

## Verdict: feasible, by static recompilation

| Road | Meaning | Verdict |
|---|---|---|
| Reimplementation | a new engine reading the assets | No: T&E's engine, 15 programs, undocumented formats (models, animations, dungeon generation) |
| Decompilation | rebuild C source and compile it for PC | No: ~7 750 distinct functions with no symbols |
| Enhanced emulation | an emulator with faster CPUs and instant drawing | Not a port, and GPL code. Useful as a measuring tool only |
| **Static recompilation** | translate the SH-2 code to C++ mechanically; reimplement only the hardware | **Yes** |

Why it is favourable here:

1. **Plain integer code.** The SH-2 has no FPU; the engine is fixed-point
   C compiled by Hitachi's SHC, with regular prologues and literal pools.
   The decoder already matches capstone on every opcode.
2. **Small.** ~14 200 function entries in 15 programs, ~7 750 distinct:
   less than Victorious's 20 653, which the same pipeline handled.
3. **Few exotic features.** No SGL, no SCU DSP, no cache-as-RAM, no VDP2
   rotation plane. The slave SH-2 is used in one place, opportunistically,
   through the standard SPR handshake.
4. **The slowdown is compute and fill-rate.** A frame costs
   `max(n VBlanks, SH-2 work + VDP1 drawing)` (`03-executables.md`). On a
   PC the second term is near zero, so the cap holds all the time.
5. **Music on CD audio** (mostly, to be confirmed): the SCSP matters for
   effects first.

What makes it harder than a Wii port:

1. **The hardware is wide.** Two VDPs that composite per pixel with
   priorities and colour calculation, a sound chip with its own 68000 and
   DSP, a CD block with its own protocol. On the Wii the SDK already cut
   most of this into a few interfaces (GX FIFO, AX, IOS).
2. **No symbols.** Function boundaries, switch tables and indirect-call
   targets come from analysis, not from a symbol table.
3. **Program swapping.** 15 programs share 0x0600B000; the recompiled code
   must be selected by which one is loaded.
4. **CPU access to the VDP1 framebuffer** (13 sites): a GPU renderer has
   to keep a CPU-visible copy where the game looks.

## Where to cut, subsystem by subsystem

The rule, as in wiikit: **cut at the hardware registers, not at library
APIs**. SBL, SGL and in-house code then all work the same, which is what
makes saturnkit reusable for the next game. The one exception is the
BIOS, whose services are plain function pointers and small.

| Subsystem | Cut | Notes |
|---|---|---|
| Master SH-2 | recompiled | per program; delay slots, T bit, MAC with the S bit, the `div0/div1` step, `tas.b`, `sleep` |
| Slave SH-2 | recompiled, run at SINIT | a second context; a SINIT write runs the slave until it waits on its FRT flag again. Deterministic first; a host thread later if it pays |
| BIOS | HLE of the service pointers | ~15 services: interrupt vectors, SCU mask, semaphores, clock, and BUP (backup RAM as a host file). The boot is HLE too: IP.BIN checked, the 1st read file loaded at its address, state as the BIOS leaves it |
| SCU | registers | interrupt controller, the three DMA levels (direct and indirect), timers 0 and 1 (timer 0 is a line compare: needs a raster clock) |
| SMPC | registers | INTBACK (pads from SDL3), SSHON/SSHOFF, SNDON/SNDOFF, CD on/off, clock change, RTC |
| CD block | **registers (HIRQ, CR1–CR4, data port)** | the command set GFS uses: status, TOC, selectors and filters, file system (change/read directory, file info, read file), sector transfer, CD-DA play. Reads the extracted tree or the image itself |
| VDP1 | **command tables in VRAM** | executed at plot on the GPU at N× resolution: sprites (normal, scaled, distorted), polygons, lines, clipping, local coordinates; colour modes and calculation (shadow, half-luminance, half-transparency, Gouraud, mesh). Output is VDP1 *pixel data*, not colours: VDP2 decides |
| VDP2 | **registers + VRAM/CRAM**, composited per frame | NBG layers (cell and bitmap), the sprite layer with its priority and colour-calculation bits, colour offset (the fades), back screen; later windows, line scroll, what other games need |
| SCSP + 68000 | **68000 interpreter + SCSP registers** | Sega's driver (`SDDRVS.TSK`) runs as is; slots, envelopes, FM, the DSP (the areas load a DSP program), CD-DA mixed through the SCSP's external inputs with the volume the game sets |
| Video out | SDL3 window, OpenGL 4.5 | as in wiikit |

## The frame rate — the heart of this port

Three levels, each a separate decision:

**Level 1 — no slowdown.** With the SH-2 code native and VDP1 drawing on
the GPU, the frame is always ready before its minimum VBlank count: the
game runs at its own cap all the time. This comes from the route itself;
nothing game-specific is needed. What is left to learn is the cap: `n` in
the in-game call to the limiter (`0x0602A566` in M_CHI), read at run time.

**Level 2 — the speed the designers meant.** The European build does not
look at the PAL bit, so on a PAL Saturn everything counted in VBlanks ran
at 5/6 speed. The port runs VBlank at 60 Hz (TVSTAT reports NTSC): the
Japanese speed with the European text. The movie player, which does read
the PAL bit, then follows NTSC timing too.

**Level 3 — above the cap (optional, researched once the game runs).**
Whether 60 frames a second is reachable depends on how the logic advances:

* if it steps by **elapsed VBlanks** (a delta), lowering `n` to 1 gives
  60 fps with correct speed, for the cost of a patch;
* if it steps **once per frame**, the logic must stay at the cap and the
  extra frames are interpolated: either game-specific (the camera and the
  objects' positions interpolated before T&E's projection, which we can
  hook because we own the code) or, game-agnostic and harder, by matching
  VDP1 commands between consecutive frames (the Z-sort reorders them, so
  matching is heuristic).

Beyond the frame rate, the same ownership of the code allows: rendering
at the PC's resolution (VDP1 coordinates are integers, so true sub-pixel
precision means taking vertices from the projection, before rounding),
mesh drawn as real transparency, a longer view distance if the engine's
culling constants allow it, widescreen (projection width, culling, HUD,
VDP2 backgrounds: the hardest).

## Oracle

Beetle Saturn (Mednafen) through RetroArch is installed
(`F:\RetroArch 2`, used by the SAT-LBA project): screenshots by frame
count for comparison, the user's eyes for play. A debugger (Mednafen
standalone, or Ghidra reading plus our own runtime's traces) is needed to
read run-time values such as the limiter's `n`. Ghidra 12.1.2 has an SH-2
language for deeper reading.

## Phases

| Phase | Goal | saturnkit gains |
|---|---|---|
| 1 ✓ | feasibility, disc, code survey, plan | `disc`, `sh2`, `hw` |
| 2 | **code map**: function discovery on stripped SHC code, switch tables, the executable map; trace the frame loop and the limiter's `n`, the slave job, the VDP1 command builder; how the logic steps | function discovery, `exe` (programs, crt0, swapping), a Python SH-2 interpreter as oracle, `fingerprint` (SBL by signature) |
| 3 | **recompiler**: all 15 programs to C++, compiling and linking; self-test of isolated functions (division helper, fixed-point math, sort) against the interpreter | `recomp` (layer 4) |
| 4 | **runtime core**: memory map, BIOS HLE boot, SCU interrupts and DMA, SMPC, slave at SINIT, CD block HLE; `A.BIN` runs to its first frame, HYDSYS loads, programs swap | runtime: `core`, `bios`, `scu`, `smpc`, `cdblock`, `boot` |
| 5 | **VDP2 + VDP1 on screen**: the SEGA logo, the opening movie (Cinepak through the emulated CD), the title and the menus | `vdp2`, `vdp1` (GPU), `video` |
| 6 | **in the field**: distorted sprites, Gouraud, half-transparency, mesh, the digitised sprites; the framebuffer's CPU view; play with the pad | `vdp1` complete, `pad` |
| 7 | **sound**: CD-DA through the SCSP mixer, the 68000 and the SCSP for effects | `m68k`, `scsp`, `audio` |
| 8 | **the frame rate**: 60 Hz VBlank, the cap held, then level 3 | profiler, frame pacing |
| 9 | **PC finish**: resolution, window/fullscreen, pad and keyboard mapping, saves to a host file, configuration; release shape | |

Phases 2–4 are wide and mostly invisible; the first picture comes in
phase 5. The runtime parts that are not game-specific (window, audio
output, the profiler) can start from wiikit's, same author and licence.

## Principles kept from the Wii ports

* BYOA: nothing from the disc in git; `iso/` and `build/` are ignored.
* Game knowledge in this repository's `tools/`; everything else in
  saturnkit, checked on every port that uses it.
* Every claim checked against the disc or the running game before it
  goes into the docs.
