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
4. **The slowdown is compute and fill-rate, and the cap is a constant.**
   A frame costs `max(5 VBlanks, SH-2 work + VDP1 drawing)`, and the logic
   steps by elapsed time (`03-executables.md`). On a PC the second term is
   near zero, so the cap holds all the time, and the cap itself can be
   lowered.
5. ~~**Music on CD audio**~~: not in the title and the first field
   (session 4): there the music is sequences for the sound driver, so the
   SCSP and its 68000 matter for music too, not only effects. Where the
   27 CD-DA tracks play is still to find.

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
| Slave SH-2 | recompiled, a coroutine | a second context on a host thread that runs only when the master hands it the CPU: at SSHON, at a SINIT write, and at the master's polls while it has work; it gives the CPU back when it waits on its FRT flag again. Deterministic (session 4) |
| BIOS | HLE of the service pointers | ~15 services: interrupt vectors, SCU mask, semaphores, clock, and BUP (backup RAM as a host file). The boot is HLE too: IP.BIN checked, the 1st read file loaded at its address, state as the BIOS leaves it |
| SCU | registers | interrupt controller, the three DMA levels (direct and indirect), timers 0 and 1 (timer 0 is a line compare: needs a raster clock) |
| SMPC | registers | INTBACK (pads from SDL3), SSHON/SSHOFF, SNDON/SNDOFF, CD on/off, clock change, RTC |
| CD block | **registers (HIRQ, CR1–CR4, data port)** | the command set GFS uses: status, TOC, selectors and filters, file system (change/read directory, file info, read file), sector transfer, CD-DA play. Reads the extracted tree or the image itself |
| VDP1 | **command tables in VRAM** | executed at plot on the GPU at N× resolution: sprites (normal, scaled, distorted), polygons, lines, clipping, local coordinates; colour modes and calculation (shadow, half-luminance, half-transparency, Gouraud, mesh). Output is VDP1 *pixel data*, not colours: VDP2 decides |
| VDP2 | **registers + VRAM/CRAM**, composited per frame | NBG layers (cell and bitmap), the sprite layer with its priority and colour-calculation bits, colour offset (the fades), back screen; later windows, line scroll, what other games need |
| SCSP + 68000 | **68000 interpreter + SCSP registers** | Sega's driver (`SDDRVS.TSK`) runs as is; slots, envelopes, FM, the DSP (the areas load a DSP program), CD-DA mixed through the SCSP's external inputs with the volume the game sets |
| Video out | SDL3 window, OpenGL 4.5 | as in wiikit |

## The frame rate — the heart of this port

Session 2 read the main loop (`03-executables.md`): the game caps itself
at **one frame every 5 VBlanks** (12 fps at 60 Hz, 10 on a European
Saturn) and drops below that whenever the frame takes longer; and its
logic advances by **elapsed VBlanks** (`dt`, clamped to 25), not once per
frame. That turns the plan into three steps, each an option the player
can choose:

**Level 1 — no slowdown.** With the SH-2 code native and VDP1 drawing on
the GPU, the frame is always ready before its 5 VBlanks: a steady 12 fps.
It comes from the route itself: the original game, never below its own
cap.

**Level 2 — the speed the designers meant.** Everything is timed in 60 Hz
VBlanks (the play clock divides by 60) and the area programs ignore the
PAL bit, so a European Saturn ran the whole game at 5/6 speed. The port
runs VBlank at 60 Hz (TVSTAT reports NTSC): the Japanese speed with the
European text.

**Level 3 — 30 or 60 fps.** The cap is the constant 5 in `main`
(0x0600B6F4, `mov #5,r5`, the same address in all nine area programs).
Because the logic steps by `dt`, lowering it to 2 or 1 should give 30 or
60 fps at the same game speed, for the cost of one patched constant in
the port's game layer. To verify in play: movement and animation that
round `dt` badly when it is small. If something does, it is fixed where
it is, in recompiled code we own. No interpolation should be needed.

Beyond the frame rate, the same ownership of the code allows: rendering
at the PC's resolution (VDP1 coordinates are integers, so true sub-pixel
precision means taking vertices from the projection, before rounding),
mesh drawn as real transparency, a longer view distance if the engine's
culling constants allow it, widescreen (projection width, culling, HUD,
VDP2 backgrounds: the hardest).

## Oracle

Beetle Saturn (Mednafen) through RetroArch is installed
(`F:\RetroArch 2`, used by the SAT-LBA project): `tools/oracle.py`
presses its buttons and takes its screenshots over UDP (`12-video.md`);
the user's eyes for play. A debugger (Mednafen
standalone, or Ghidra reading plus our own runtime's traces) helps with
run-time values. Ghidra 12.1.2 has an SH-2
language for deeper reading.

## Phases

| Phase | Goal | saturnkit gains |
|---|---|---|
| 1 ✓ | feasibility, disc, code survey, plan | `disc`, `sh2`, `hw` |
| 2 | **code map**: function discovery on stripped SHC code, switch tables; the frame loop, its cap and how the logic steps (done); HYDSYS's services and the program swap (done); the slave job, the VDP1 command builder | `recomp.discover` (done), `exe`, a Python SH-2 interpreter as oracle, `fingerprint` (SBL by signature) |
| 3 ✓ | **recompiler**: all 15 programs to C++, compiling and linking; self-test of isolated functions (division helper, fixed-point math, sort) against the interpreter (`09-recompiler.md`) | `recomp` (layer 4), the runtime's `core`, `stub`, `selftest` |
| 4 ✓ | **runtime core**: memory map, BIOS HLE boot, SCU interrupts and DMA, SMPC, the slave, CD block at its registers, the sound driver's handshake; from the boot through OPEN, HYDSYS and STARTUP to M_CHI's frame loop at 12 fps (`11-runtime.md`) | runtime: `machine`, `bios`, `mmio`, `scu`, `smpc`, `cdrom`, `cdblock`, `onchip`, `video` |
| 5 ✓ | **VDP2 + VDP1 on screen**: the opening movie, the title, the menus and the first field, in software, in a window, with the pad; against Beetle Saturn (`12-video.md`). The SEGA licence screen is the BIOS's, not the game's | runtime: `vdp1` (software), `vdp2`, `host`; `tools/oracle.py` here |
| 6 | **in the field**: play it (drawn since phase 5: distorted sprites, Gouraud, shadow); the same world against the oracle; VDP1 on the GPU at N× resolution; what the other areas ask of VDP1 and VDP2; the framebuffer's CPU view | `vdp1` on the GPU, `vdp2` as needed |
| 7 | **sound**: CD-DA through the SCSP mixer, the 68000 and the SCSP for effects | `m68k`, `scsp`, `audio` |
| 8 | **the frame rate**: 60 Hz VBlank, the cap held, then the cap lowered to 2 and 1 and the game checked at 30 and 60 fps | profiler, frame pacing |
| 9 | **PC finish**: resolution, window/fullscreen, pad and keyboard mapping, saves to a host file, configuration; release shape | |

Session 5 moved phase 7 (sound) before the rest of phase 6: the field
already plays right, and silence is the most visible gap. Phases 2–4
were wide and mostly invisible; the first picture came in phase 5. The runtime parts that are not game-specific (window, audio
output, the profiler) can start from wiikit's, same author and licence.

## Principles kept from the Wii ports

* BYOA: nothing from the disc in git; `iso/` and `build/` are ignored.
* Game knowledge in this repository's `tools/`; everything else in
  saturnkit, checked on every port that uses it.
* Every claim checked against the disc or the running game before it
  goes into the docs.
