# What this port gave saturnkit

saturnkit (`saturnkit/`, a submodule) was started by this port. Each
entry is a saturnkit commit and what Virtual Hydlide asked of it.

| Session | saturnkit | What |
|---|---|---|
| 1 | e926f67 | `disc`: .cue/.bin sets, IP.BIN, ISO 9660, 1st read file, extraction, CD-DA to WAV. `sh2`: SH7604 decoder (equal to capstone on all opcodes the SH-2 defines), disassembly with literal pools and register names, `--refs`, `--census`, `--find-base`. `hw`: address map, register names, BIOS service pointers, SCU vectors |
| 2 | 4ce9daa | `recomp.discover`: functions and code/data in stripped SHC programs (recursive descent, constant propagation for register calls, three switch forms, pointer and prologue seeds). `recomp.match`: the same function across programs, names carried. `sh2emu`: an SH-2 interpreter (the division helpers, 12 000 of 12 000). `hw`: BIOS 0x0600026C as seen used |
| 2 | cf3250b | `ghidra/ExportFuncs.java`: Ghidra's function list, the independent check behind `discover`'s 571 of 576 |
| 3 | fe9b8b2 | `recomp` (emit and driver): each function to C++, one module per program recognised by its crc32, guarded dispatch through registers, switches, safe points; a CMake project. `runtime/`: the SH-2 context, the work RAMs and the address map, dispatch over modules, no-hardware services, the self-test harness. `recomp.selftest`: vectors from `sh2emu`, the instruction test (every form, alone and in a delay slot, and the control flow), a program's functions that run alone; 51 448 of 51 448 on Virtual Hydlide. `sh2.encode`. `discover`: branches into delay slots, the shift ladder with an offset, data pointers kept out of the seeds (still 571 of Ghidra's 576) |
