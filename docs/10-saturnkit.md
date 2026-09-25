# What this port gave saturnkit

saturnkit (`saturnkit/`, a submodule) was started by this port. Each
entry is a saturnkit commit and what Virtual Hydlide asked of it.

| Session | saturnkit | What |
|---|---|---|
| 1 | e926f67 | `disc`: .cue/.bin sets, IP.BIN, ISO 9660, 1st read file, extraction, CD-DA to WAV. `sh2`: SH7604 decoder (equal to capstone on all opcodes the SH-2 defines), disassembly with literal pools and register names, `--refs`, `--census`, `--find-base`. `hw`: address map, register names, BIOS service pointers, SCU vectors |
| 2 | 4ce9daa | `recomp.discover`: functions and code/data in stripped SHC programs (recursive descent, constant propagation for register calls, three switch forms, pointer and prologue seeds). `recomp.match`: the same function across programs, names carried. `sh2emu`: an SH-2 interpreter (the division helpers, 12 000 of 12 000). `hw`: BIOS 0x0600026C as seen used |
