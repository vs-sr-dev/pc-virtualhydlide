# pc-virtualhydlide

Toward a native PC port of **Virtual Hydlide** (Sega Saturn, T&E Soft /
Sega, 1995), the 3D remake of the 1984 action RPG, with its randomly
generated field, digitised actors as sprites, and a frame rate that
collapses whenever the field fills up. It was never re-released. The goal
is the game running natively on PC, and running **smoothly**: the frame
rate is the first thing a port has to fix.

This repository documents the disc, its formats and its code, and grows
the tooling for the port. Alongside it grows **saturnkit**, a
game-agnostic toolkit for Saturn reverse engineering: everything the port
needs that is not specific to Virtual Hydlide. It is taken here as a
submodule: clone with `--recursive`, or run `git submodule update --init`.

## BYOA — Bring Your Own Assets

This repository contains **documentation and tools only**. No game data, no
executables, no assets. You need your own original disc. The work is done
on the European release, MK-81380 (V1.000, 1995-06-30), as a Redump-style
.cue/.bin set.

## Layout

    docs/            disc, format and code analysis, and the plan
    tools/           Virtual Hydlide-specific data and tools: names-m_chi.tsv, recomp.py, run.py
    saturnkit/       game-agnostic Saturn toolkit (submodule)
    iso/, build/     your disc and everything derived from it (ignored by git)

## Tools

The Python tools need only Python 3.8+ and no dependencies. Building the
recompiled C++ needs CMake, Ninja and clang (MSYS2's mingw64, found at
`C:\msys64\mingw64\bin`). Run from the repository root.

```sh
CUE="iso/Virtual Hydlide (Europe).cue"

# the disc: IP.BIN, the ISO 9660 volume, the 28 tracks; extract it
python -m saturnkit.disc "$CUE" --info
python -m saturnkit.disc "$CUE" --list
python -m saturnkit.disc "$CUE" --extract build/extract
python -m saturnkit.disc "$CUE" --audio build/audio

# the code: where each executable loads, a function, who builds an address
EXE=build/extract/HYDLIDE/EXEC/M_CHI.BIN
python -m saturnkit.sh2 $EXE --find-base
python -m saturnkit.sh2 $EXE --base 0600B000 --at 0603E714 --count 40   # the slave SH-2's loop
python -m saturnkit.sh2 $EXE --base 0600B000 --refs 25D00000:25D00018   # VDP1 registers
python -m saturnkit.hw 25D00002 06000310

# functions and code/data; names from M_CHI carried to another program
python -m saturnkit.recomp.discover $EXE --base 0600B000 --report
python -m saturnkit.recomp.match $EXE@0600B000 build/extract/HYDLIDE/EXEC/M_KYU.BIN@0600B000 --names tools/names-m_chi.tsv --out build/names/M_KYU.tsv

# run a guest function: the SHC unsigned division, 100 / 7
python -m saturnkit.sh2emu $EXE --base 0600B000 --call 060224DC --regs r1=100,r0=7

# all 15 programs to C++, built with clang (MSYS2) and checked against the interpreter
python tools/recomp.py --build --test

# the game on saturnkit's runtime, headless: boot to the first field, then the hardware log
python tools/run.py
python tools/run.py --report
```

## Status

Session 2: the code map. The game caps itself at one frame every 5
VBlanks (12 fps, 10 on a European Saturn) and its logic runs on elapsed
time, so the port's 60 fps is one constant (`docs/03-executables.md`,
`docs/06-attack-plan.md`). saturnkit can now find the functions of the
stripped programs, match the engine across all 15, and run guest code in
an interpreter.

Session 3: the recompiler. All 15 programs are C++ (10 256 functions, 1.5
million instructions) that compiles, links, and agrees with the
interpreter on 51 448 recorded calls (`docs/09-recompiler.md`).

Session 4: the runtime core. The recompiled game runs on saturnkit's
Saturn, still with no screen: it boots, plays its opening movie, loads
HYDSYS, goes through the title menu and reaches the first field, whose
frame loop holds its cap of 12 frames a second (`docs/11-runtime.md`).
Next: VDP1 and VDP2 on screen (`docs/07-next-session.md`).

## Documentation

* [00-sessions.md](docs/00-sessions.md) — what each session did
* [01-disc-layout.md](docs/01-disc-layout.md) — IP.BIN, tracks, the file tree
* [02-data-formats.md](docs/02-data-formats.md) — first look at the game's files
* [03-executables.md](docs/03-executables.md) — memory map, program swapping, the slave SH-2, interrupts, BIOS services, the frame limiter
* [04-curiosities.md](docs/04-curiosities.md) — things found on the way
* [05-open-questions.md](docs/05-open-questions.md) — what is not known yet
* [06-attack-plan.md](docs/06-attack-plan.md) — feasibility, route, phases, the frame-rate strategy
* [07-next-session.md](docs/07-next-session.md) — the next session's list
* [09-recompiler.md](docs/09-recompiler.md) — the programs as C++: the generated code, the counts, the self-test
* [11-runtime.md](docs/11-runtime.md) — the runtime core: the run to the field, how the Saturn is built, the hardware touched
* [10-saturnkit.md](docs/10-saturnkit.md) — what this port gave saturnkit

## Licence

MIT — see [LICENSE](LICENSE). Virtual Hydlide is © 1995 T&E Soft / Sega;
this project contains none of it.
