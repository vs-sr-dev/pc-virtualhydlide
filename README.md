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
    tools/           Virtual Hydlide-specific tools (none yet)
    saturnkit/       game-agnostic Saturn toolkit (submodule)
    iso/, build/     your disc and everything derived from it (ignored by git)

## Tools

The Python tools need only Python 3.8+ and no dependencies. Run from the
repository root.

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
```

## Status

Session 1: feasibility, disc and code survey, the plan. The route is
static recompilation of the SH-2 code with the Saturn's hardware replaced
(`docs/06-attack-plan.md`). saturnkit has its layers 1–3 started: disc,
SH-2 decoder (checked against capstone on all 65 536 words), address map.

## Documentation

* [00-sessions.md](docs/00-sessions.md) — what each session did
* [01-disc-layout.md](docs/01-disc-layout.md) — IP.BIN, tracks, the file tree
* [02-data-formats.md](docs/02-data-formats.md) — first look at the game's files
* [03-executables.md](docs/03-executables.md) — memory map, program swapping, the slave SH-2, interrupts, BIOS services, the frame limiter
* [04-curiosities.md](docs/04-curiosities.md) — things found on the way
* [05-open-questions.md](docs/05-open-questions.md) — what is not known yet
* [06-attack-plan.md](docs/06-attack-plan.md) — feasibility, route, phases, the frame-rate strategy
* [07-next-session.md](docs/07-next-session.md) — the next session's list
* [10-saturnkit.md](docs/10-saturnkit.md) — what this port gave saturnkit

## Licence

MIT — see [LICENSE](LICENSE). Virtual Hydlide is © 1995 T&E Soft / Sega;
this project contains none of it.
